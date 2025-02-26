#!/usr/bin/env python3

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from openai import OpenAI
import re
import logging

logger = logging.getLogger(__name__)

class PriceActionAnalyzer:
    """Třída pro analýzu price action dat pomocí AI."""

    def __init__(self, api_key):
        """
        Inicializuje analyzátor price action.
        
        Args:
            api_key (str): OpenAI API klíč
        """
        self.client = OpenAI(api_key=api_key)

    def detect_patterns(self, df):
        """
        Detekuje price action patterny v DataFrame.
        
        Args:
            df (pandas.DataFrame): DataFrame s OHLCV daty
            
        Returns:
            list: Seznam detekovaných patternů
        """
        patterns = []
        
        # Detekce cenových nerovnováh (Fair Value Gaps)
        for i in range(1, len(df)-1):
            # Bullish nerovnováha
            if df['low'].iloc[i] > df['high'].iloc[i-1]:
                patterns.append(('Bullish FVG', df.index[i], df['high'].iloc[i-1], df['low'].iloc[i]))
            
            # Bearish nerovnováha
            if df['high'].iloc[i] < df['low'].iloc[i-1]:
                patterns.append(('Bearish FVG', df.index[i], df['high'].iloc[i], df['low'].iloc[i-1]))

        # Detekce silných zón (Order Blocks)
        for i in range(1, len(df)-1):
            body_size = abs(df['close'].iloc[i] - df['open'].iloc[i])
            total_range = df['high'].iloc[i] - df['low'].iloc[i]
            
            if total_range > 0 and body_size / total_range > 0.7:
                # Bullish Order Block (svíčka před výrazným pohybem vzhůru)
                if i < len(df)-2 and df['close'].iloc[i+1] > df['open'].iloc[i+1] and df['close'].iloc[i+1] > df['close'].iloc[i]:
                    patterns.append(('Bullish OB', df.index[i], df['low'].iloc[i], df['high'].iloc[i]))
                
                # Bearish Order Block (svíčka před výrazným pohybem dolů)
                if i < len(df)-2 and df['close'].iloc[i+1] < df['open'].iloc[i+1] and df['close'].iloc[i+1] < df['close'].iloc[i]:
                    patterns.append(('Bearish OB', df.index[i], df['low'].iloc[i], df['high'].iloc[i]))

        # Detekce falešných průrazů (Liquidity Sweeps)
        lookback = 5
        for i in range(lookback, len(df)-1):
            high_level = df['high'].iloc[i-lookback:i].max()
            low_level = df['low'].iloc[i-lookback:i].min()
            
            # Průraz vysoko s následným návratem (false breakout)
            if df['high'].iloc[i] > high_level and df['close'].iloc[i+1] < high_level:
                patterns.append(('False High Breakout', df.index[i], high_level, df['high'].iloc[i]))
            
            # Průraz nízko s následným návratem (false breakout)
            if df['low'].iloc[i] < low_level and df['close'].iloc[i+1] > low_level:
                patterns.append(('False Low Breakout', df.index[i], df['low'].iloc[i], low_level))

        # Detekce swingových high/low (významné vrcholy a dna)
        for i in range(2, len(df)-2):
            # Swing high (lokální vrchol)
            if df['high'].iloc[i] > df['high'].iloc[i-1] and df['high'].iloc[i] > df['high'].iloc[i-2] and \
               df['high'].iloc[i] > df['high'].iloc[i+1] and df['high'].iloc[i] > df['high'].iloc[i+2]:
                patterns.append(('Swing High', df.index[i], df['high'].iloc[i] * 0.99, df['high'].iloc[i] * 1.01))
            
            # Swing low (lokální dno)
            if df['low'].iloc[i] < df['low'].iloc[i-1] and df['low'].iloc[i] < df['low'].iloc[i-2] and \
               df['low'].iloc[i] < df['low'].iloc[i+1] and df['low'].iloc[i] < df['low'].iloc[i+2]:
                patterns.append(('Swing Low', df.index[i], df['low'].iloc[i] * 0.99, df['low'].iloc[i] * 1.01))

        return patterns

    def generate_multi_timeframe_analysis(self, symbol, dataframes):
        """
        Generuje multi-timeframe analýzu na základě dat z různých časových rámců.
        Tato verze je upravena pro nezahrnování konkrétních vstupů a zaměření na zóny.
        
        Args:
            symbol (str): Obchodní symbol
            dataframes (dict): Slovník s DataFrame pro různé časové rámce
            
        Returns:
            tuple: (analýza, support_zóny, resistance_zóny, scenáře)
        """
        patterns_by_tf = {}
        for tf, df in dataframes.items():
            patterns_by_tf[tf] = self.detect_patterns(df)

        timeframe_data = []
        all_timeframes = ["1w", "1d", "4h", "30m", "5m"]
        
        for tf in all_timeframes:
            if tf in dataframes:
                df = dataframes[tf]
                num_candles = 5 if tf in ['1w', '1d'] else (7 if tf == '4h' else 10)
                
                tf_data = f"## Časový rámec: {tf}\n"
                tf_data += f"Rozsah dat: {df.index[0]} až {df.index[-1]}\n"
                tf_data += f"Počet svíček: {len(df)}\n"
                tf_data += f"Posledních {num_candles} svíček:\n"
                tf_data += f"{df[['open','high','low','close','volume']].tail(num_candles).to_markdown()}\n\n"
                
                patterns = patterns_by_tf[tf]
                if patterns:
                    tf_data += f"Poslední patterny:\n"
                    for pattern in patterns[-8:]:  # Zobrazíme více patternů pro lepší analýzu
                        tf_data += f"- {pattern[0]} na úrovni {pattern[2]:.2f}-{pattern[3]:.2f} ({pattern[1]})\n"
                
                timeframe_data.append(tf_data)

        # Získáme aktuální cenu z posledního dataframe
        latest_price = None
        if '1d' in dataframes:
            latest_price = dataframes['1d']['close'].iloc[-1]
        elif '4h' in dataframes:
            latest_price = dataframes['4h']['close'].iloc[-1]

        prompt = f"""Jste senior trader specializující se na price action analýzu. Analyzujte data s důrazem na všechny časové rámce, ale bez poskytování konkrétních vstupních bodů.

Symbol: {symbol}
Aktuální cena: {latest_price:.2f}
# DATA PODLE ČASOVÝCH RÁMCŮ
{''.join(timeframe_data)}

## 1. 📊 DLOUHODOBÝ TREND (1W/1D)
- Hlavní supportní zóny (min. 4 významné zóny definované jako rozsah cen, např. 86000-86200)
- Hlavní resistenční zóny (min. 4 významné zóny definované jako rozsah cen, např. 89400-89600)
- Fair Value Gaps (FVG) s přesnými úrovněmi cen
- Order Blocks (OB) s přesnými úrovněmi cen
- Fázová analýza trhu (akumulace/distribuce, trendové/nárazové pohyby)
- Klíčové weekly/daily uzávěry

## 2. 🔍 STŘEDNĚDOBÝ KONTEXT (4H)
- Pozice v rámci vyššího trendu
- Významné cenové nerovnováhy (FVG)
- Order Blocks na 4H timeframu
- Objemové klastry
- Hlavní supportní a resistenční zóny

## 3. 💡 MOŽNÉ SCÉNÁŘE DALŠÍHO VÝVOJE
- Bullish scénář (popište podmínky, spouštěče a potenciální cílové úrovně)
- Bearish scénář (popište podmínky, spouštěče a potenciální cílové úrovně) 
- Neutrální scénář (konsolidace nebo range bound chování)

## 4. ⚠️ VÝZNAMNÉ ÚROVNĚ K SLEDOVÁNÍ
- Denní pivot pointy
- Důležité swingové high/low
- ŽÁDNÉ KONKRÉTNÍ VSTUPY - pouze úrovně k sledování

Formát:
- Přehledné a stručné odrážky
- Pouze konkrétní informace, žádný vágní text
- Nepoužívejte žádná varování ani 'AI' fráze (například vyhněte se 'vždy si ověřte aktuální tržní podmínky')
- Časové razítko: {datetime.now().strftime("%d.%m.%Y %H:%M")}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=3000
            )
            analysis = response.choices[0].message.content
            
            # Extrahování zón supportů a resistancí
            support_zones = self.extract_zones_from_analysis(analysis, "support")
            resistance_zones = self.extract_zones_from_analysis(analysis, "resistance")
            
            # Extrahování scénářů pro vizualizaci
            scenarios = self.extract_scenarios_from_analysis(analysis, latest_price)
            
            return analysis, support_zones, resistance_zones, scenarios
            
        except Exception as e:
            raise Exception(f"Chyba při generování multi-timeframe analýzy: {str(e)}")

    def extract_scenarios_from_analysis(self, analysis, current_price):
        """
        Extrahuje scénáře pro vizualizaci z textu analýzy.
        
        Args:
            analysis (str): Text analýzy
            current_price (float): Aktuální cena
            
        Returns:
            list: Seznam scénářů ve formátu [('bullish', target_price), ('bearish', target_price), ...]
        """
        scenarios = []
        
        # Hledání bullish scénáře a ceny
        bullish_patterns = [
            r"[Bb]ullish.*?([0-9,.-]+)",
            r"[Vv]zhůru.*?([0-9,.-]+)",
            r"[Rr]ůst.*?([0-9,.-]+)",
            r"[Cc]íl.*?([0-9,.-]+)"
        ]
        
        # Hledání bearish scénáře a ceny
        bearish_patterns = [
            r"[Bb]earish.*?([0-9,.-]+)",
            r"[Pp]okles.*?([0-9,.-]+)",
            r"[Pp]ád.*?([0-9,.-]+)",
            r"[Dd]olů.*?([0-9,.-]+)"
        ]
        
        # Hledání cen v bullish scénáři
        bullish_targets = []
        for pattern in bullish_patterns:
            matches = re.findall(pattern, analysis)
            for match in matches:
                try:
                    price = float(match.replace(',', '.'))
                    if price > current_price * 1.005:  # Musí být aspoň 0.5% nad aktuální cenou
                        bullish_targets.append(price)
                except (ValueError, IndexError):
                    continue
        
        # Hledání cen v bearish scénáři
        bearish_targets = []
        for pattern in bearish_patterns:
            matches = re.findall(pattern, analysis)
            for match in matches:
                try:
                    price = float(match.replace(',', '.'))
                    if price < current_price * 0.995:  # Musí být aspoň 0.5% pod aktuální cenou
                        bearish_targets.append(price)
                except (ValueError, IndexError):
                    continue
        
        # Přidání bullish scénáře (pokud existuje)
        if bullish_targets:
            # Seřadíme a vybereme nejvyšší cíl a jeden uprostřed
            bullish_targets.sort()
            mid_index = len(bullish_targets) // 2
            scenarios.append(('bullish', bullish_targets[-1]))  # Nejvyšší cíl
            if len(bullish_targets) > 2 and bullish_targets[mid_index] != bullish_targets[-1]:
                scenarios.append(('bullish_mid', bullish_targets[mid_index]))  # Cíl uprostřed
        
        # Přidání bearish scénáře (pokud existuje)
        if bearish_targets:
            # Seřadíme a vybereme nejnižší cíl a jeden uprostřed
            bearish_targets.sort()
            mid_index = len(bearish_targets) // 2
            scenarios.append(('bearish', bearish_targets[0]))  # Nejnižší cíl
            if len(bearish_targets) > 2 and bearish_targets[mid_index] != bearish_targets[0]:
                scenarios.append(('bearish_mid', bearish_targets[mid_index]))  # Cíl uprostřed
        
        return scenarios

    def extract_zones_from_analysis(self, analysis, zone_type):
        """
        Extrahuje zóny supportů nebo resistancí z textu analýzy.
        
        Args:
            analysis (str): Text analýzy
            zone_type (str): Typ zóny ('support' nebo 'resistance')
            
        Returns:
            list: Seznam zón ve formátu [(min1, max1), (min2, max2), ...]
        """
        zones = []
        
        # Různé možné variace názvů v textu
        if zone_type.lower() == "support":
            patterns = [
                r"[Ss]upportní zón[ay]:\s*([0-9,.-]+)-([0-9,.-]+)",
                r"[Ss]upport[ní]{0,2} zón[ay]?.*?([0-9,.-]+)-([0-9,.-]+)",
                r"[Ss]upport.*?([0-9,.-]+)-([0-9,.-]+)",
                r"[Bb]ullish OB.*?([0-9,.-]+)-([0-9,.-]+)",
                r"[Bb]ullish FVG.*?([0-9,.-]+)-([0-9,.-]+)"
            ]
        else:  # resistance
            patterns = [
                r"[Rr]esistenční zón[ay]:\s*([0-9,.-]+)-([0-9,.-]+)",
                r"[Rr]esisten[cč][en]í zón[ay]?.*?([0-9,.-]+)-([0-9,.-]+)",
                r"[Rr]esisten[cč][en].*?([0-9,.-]+)-([0-9,.-]+)",
                r"[Bb]earish OB.*?([0-9,.-]+)-([0-9,.-]+)",
                r"[Bb]earish FVG.*?([0-9,.-]+)-([0-9,.-]+)"
            ]
        
        for pattern in patterns:
            matches = re.findall(pattern, analysis)
            for match in matches:
                try:
                    min_value = float(match[0].replace(',', '.'))
                    max_value = float(match[1].replace(',', '.'))
                    zones.append((min_value, max_value))
                except (ValueError, IndexError):
                    continue
        
        # Pokud nenajdeme zóny pomocí rozsahů, zkusíme hledat konkrétní hodnoty
        if not zones:
            if zone_type.lower() == "support":
                value_pattern = r"[Ss]upport.*?([0-9,.-]+)"
            else:
                value_pattern = r"[Rr]esisten[cč][en].*?([0-9,.-]+)"
            
            matches = re.findall(value_pattern, analysis)
            for match in matches:
                try:
                    value = float(match.replace(',', '.'))
                    # Vytvoříme z konkrétní hodnoty malou zónu (±0.5%)
                    margin = value * 0.005
                    zones.append((value - margin, value + margin))
                except ValueError:
                    continue
        
        # Omezení počtu zón pro lepší přehlednost a výkon (max 8 - upraveno pro zahrnutí více úrovní)
        if len(zones) > 8:
            zones = zones[:8]
            
        return zones

    # Ponecháváme ostatní metody beze změny...
    def generate_intraday_analysis(self, symbol, dataframes):
        """
        Generuje intraday analýzu zaměřenou na kratší časové rámce.
        
        Args:
            symbol (str): Obchodní symbol
            dataframes (dict): Slovník s DataFrame pro různé časové rámce
            
        Returns:
            tuple: (analýza, support_zóny, resistance_zóny)
        """
        # Detekce patternů pro každý časový rámec
        patterns_by_tf = {}
        for tf, df in dataframes.items():
            patterns_by_tf[tf] = self.detect_patterns(df)

        # Příprava dat pro prompt
        timeframe_data = []
        intraday_timeframes = ["4h", "30m", "5m"]
        
        for tf in intraday_timeframes:
            if tf in dataframes:
                df = dataframes[tf]
                num_candles = 7 if tf == '4h' else (10 if tf == '30m' else 15)
                
                tf_data = f"## Časový rámec: {tf}\n"
                tf_data += f"Rozsah dat: {df.index[0]} až {df.index[-1]}\n"
                tf_data += f"Počet svíček: {len(df)}\n"
                tf_data += f"Posledních {num_candles} svíček:\n"
                tf_data += f"{df[['open','high','low','close','volume']].tail(num_candles).to_markdown()}\n\n"
                
                patterns = patterns_by_tf[tf]
                if patterns:
                    tf_data += f"Poslední patterny:\n"
                    patt_count = 5 if tf == '4h' else (7 if tf == '30m' else 10)
                    for pattern in patterns[-patt_count:]:
                        tf_data += f"- {pattern[0]} na úrovni {pattern[2]:.2f}-{pattern[3]:.2f} ({pattern[1]})\n"
                
                timeframe_data.append(tf_data)

        prompt = f"""Jste profesionální day trader. Vytvořte stručnou intraday analýzu pro dnešní seanci.

Symbol: {symbol}
# KLÍČOVÉ ÚROVNĚ
{''.join(timeframe_data)}

## 🕵️♂️ 4H KONTEXT
- Trendový směr
- Nejdůležitější supportní zóny (definujte jako rozsah cen, např. 86000-86200)
- Nejdůležitější resistenční zóny (definujte jako rozsah cen, např. 89400-89600)

## 📈 30M SETUPY
- Klíčové zóny pro dnešek:
  - Supportní zóny: definujte 2-3 klíčové zóny s rozsahem
  - Resistenční zóny: definujte 2-3 klíčové zóny s rozsahem
- Potenciální směr pohybu
- Ideální vstupní zóny

## ⚡ KONKRÉTNÍ OBCHODNÍ PŘÍLEŽITOSTI
- Uveďte pouze obchodní příležitosti s RRR 2:1 nebo lepším
- Uveďte 1-2 jasné obchodní příležitosti v tomto formátu:

Pokud [podmínka], pak:
Pozice: [LONG/SHORT]
Vstup: [přesná cenová úroveň]
SL: [přesná cenová úroveň]
TP1: [přesná cenová úroveň] (50%)
TP2: [přesná cenová úroveň] (50%)
RRR: [přesný poměr risk/reward, např. 2.5:1]
Časová platnost: [konkrétní časový údaj]

- Pokud je jedna z variant (LONG/SHORT) mnohem méně pravděpodobná vzhledem k tržnímu kontextu, uveďte pouze tu pravděpodobnější variantu
- NEZAHRNUJTE žádné závěrečné shrnutí ani varování

Formát:
- Stručné, přehledné odrážky
- Pouze konkrétní informace, žádný vágní text
- Nepoužívejte žádná varování ani 'AI' fráze (například vyhněte se 'vždy si ověřte aktuální tržní podmínky')
- Časové okno: {datetime.now().strftime("%H:%M")}-{datetime.now().replace(hour=22, minute=0).strftime("%H:%M")}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2500
            )
            analysis = response.choices[0].message.content
            
            # Extrahování zón supportů a resistancí
            support_zones = self.extract_zones_from_analysis(analysis, "support")
            resistance_zones = self.extract_zones_from_analysis(analysis, "resistance")
            
            return analysis, support_zones, resistance_zones
            
        except Exception as e:
            raise Exception(f"Chyba při generování intraday analýzy: {str(e)}")

    def generate_analysis(self, symbol, df, patterns=None):
        """
        Generuje analýzu na základě historických dat a detekovaných patternů.
        
        Args:
            symbol (str): Obchodní symbol
            df (pandas.DataFrame): DataFrame s OHLCV daty
            patterns (list, optional): Seznam detekovaných patternů
            
        Returns:
            tuple: (analýza, support_zóny, resistance_zóny)
        """
        if patterns is None:
            patterns = self.detect_patterns(df)
        
        last_5_patterns = patterns[-5:] if patterns else []

        prompt = f"""Jste profesionální trader specializující se na čistou price action. Analyzujte následující data:
Symbol: {symbol}
Časový rámec: {df.index[-1] - df.index[-2] if len(df) > 1 else 'neznámý'}
Posledních 10 svíček:
{df[['open','high','low','close','volume']].tail(10).to_markdown()}

Detekované patterny:
{last_5_patterns}

Vytvořte analýzu v češtině se zaměřením na:
1. Trendový kontext a struktura trhu (3-4 body)
2. Klíčové cenové zóny:
   - Supportní zóny (definujte jako rozsahy cen, např. 86000-86200)
   - Resistenční zóny (definujte jako rozsahy cen, např. 89400-89600)
3. Vztah mezi cenou a objemem

4. KONKRÉTNÍ OBCHODNÍ PŘÍLEŽITOSTI:
- Uveďte pouze obchodní příležitosti s RRR 2:1 nebo lepším
- Uveďte 1-2 jasné obchodní příležitosti v tomto formátu:

Pokud [podmínka], pak:
Pozice: [LONG/SHORT]
Vstup: [přesná cenová úroveň]
SL: [přesná cenová úroveň]
TP1: [přesná cenová úroveň] (50%)
TP2: [přesná cenová úroveň] (50%)
RRR: [přesný poměr risk/reward, např. 2.5:1]
Platnost: [konkrétní časový údaj]

- Pokud je jedna z variant (LONG/SHORT) mnohem méně pravděpodobná vzhledem k tržnímu kontextu, uveďte pouze tu pravděpodobnější variantu
- NEZAHRNUJTE žádné závěrečné shrnutí ani varování

Formát:
- Stručné odrážky
- Pouze konkrétní informace, žádný vágní text
- Nepoužívejte žádná varování ani 'AI' fráze (například vyhněte se 'vždy si ověřte aktuální tržní podmínky')
- Časové razítko: {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            analysis = response.choices[0].message.content
            
            # Extrahování zón supportů a resistancí
            support_zones = self.extract_zones_from_analysis(analysis, "support")
            resistance_zones = self.extract_zones_from_analysis(analysis, "resistance")
            
            return analysis, support_zones, resistance_zones
            
        except Exception as e:
            raise Exception(f"Chyba při generování analýzy: {str(e)}")

    def process_data(self, klines_data):
        """
        Zpracuje surová data z Binance API do pandas DataFrame.
       
        Args:
            klines_data (list): Seznam svíček z Binance API
            
        Returns:
            pandas.DataFrame: Zpracovaná data
        """
        df = pd.DataFrame(klines_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
       
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)
           
        return df

    def process_multi_timeframe_data(self, multi_tf_data):
        """
        Zpracuje multi-timeframe data z Binance API.
      
        Args:
            multi_tf_data (dict): Slovník se seznamy svíček pro různé timeframy
            
        Returns:
            dict: Slovník s DataFrame pro každý timeframe
        """
        result = {}
        for timeframe, klines_data in multi_tf_data.items():
            if klines_data:
                df = self.process_data(klines_data)
                result[timeframe] = df
        return result
