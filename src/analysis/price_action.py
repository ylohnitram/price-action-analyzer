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
            if df['low'].iloc[i] > df['high'].iloc[i-1] and df['low'].iloc[i+1] > df['high'].iloc[i]:
                patterns.append(('Bullish Gap', df.index[i], df['low'].iloc[i], df['high'].iloc[i]))
            
            # Bearish nerovnováha
            if df['high'].iloc[i] < df['low'].iloc[i-1] and df['high'].iloc[i+1] < df['low'].iloc[i]:
                patterns.append(('Bearish Gap', df.index[i], df['high'].iloc[i], df['low'].iloc[i]))

        # Detekce silných zón (Order Blocks)
        for i in range(len(df)):
            body_size = abs(df['close'].iloc[i] - df['open'].iloc[i])
            total_range = df['high'].iloc[i] - df['low'].iloc[i]
            
            if total_range > 0 and body_size / total_range > 0.7:
                direction = 'Bullish Zone' if df['close'].iloc[i] > df['open'].iloc[i] else 'Bearish Zone'
                patterns.append((direction, df.index[i], df['low'].iloc[i], df['high'].iloc[i]))

        # Detekce falešných průrazů (Liquidity Sweeps)
        lookback = 5
        for i in range(lookback, len(df)):
            # Průraz vysoko
            if df['high'].iloc[i] > df['high'].iloc[i-lookback:i].max() and df['close'].iloc[i] < df['high'].iloc[i-lookback:i].max():
                patterns.append(('False High Breakout', df.index[i], df['high'].iloc[i-lookback:i].max(), df['high'].iloc[i]))
            
            # Průraz nízko
            if df['low'].iloc[i] < df['low'].iloc[i-lookback:i].min() and df['close'].iloc[i] > df['low'].iloc[i-lookback:i].min():
                patterns.append(('False Low Breakout', df.index[i], df['low'].iloc[i-lookback:i].min(), df['low'].iloc[i]))

        return patterns

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

    def generate_multi_timeframe_analysis(self, symbol, dataframes):
        """
        Generuje multi-timeframe analýzu na základě dat z různých časových rámců.
        
        Args:
            symbol (str): Obchodní symbol
            dataframes (dict): Slovník s DataFrame pro různé časové rámce
            
        Returns:
            tuple: (analýza, support_zóny, resistance_zóny)
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
                    for pattern in patterns[-5:]:
                        tf_data += f"- {pattern[0]} na úrovni {pattern[2]:.2f}-{pattern[3]:.2f} ({pattern[1]})\n"
                
                timeframe_data.append(tf_data)

        prompt = f"""Jste senior trader specializující se na dlouhodobé investiční strategie. Analyzujte data s důrazem na vyšší časové rámce.

Symbol: {symbol}
# DATA PODLE ČASOVÝCH RÁMCŮ
{''.join(timeframe_data)}

## 1. 📊 DLOUHODOBÝ TREND (1W/1D)
- Hlavní supportní zóny (min. 3 významné zóny definované jako rozsah cen, např. 86000-86200)
- Hlavní resistenční zóny (min. 3 významné zóny definované jako rozsah cen, např. 89400-89600)
- Fázová analýza trhu (akumulace/distribuce, trendové/nárazové pohyby)
- Klíčové weekly/daily uzávěry

## 2. 🔍 STŘEDNĚDOBÝ KONTEXT (4H)
- Pozice v rámci vyššího trendu
- Významné cenové mezery (imbalance zones)
- Objemové klastry

## 3. 💯 KONKRÉTNÍ OBCHODNÍ PŘÍLEŽITOSTI
- Uveďte pouze obchodní příležitosti s RRR 2:1 nebo lepším
- Uveďte 1-2 jasné obchodní příležitosti v tomto formátu:

Pokud [podmínka], pak:
Pozice: [LONG/SHORT]
Vstup: [přesná cenová úroveň]
SL: [přesná cenová úroveň]
TP1: [přesná cenová úroveň] (50%)
TP2: [přesná cenová úroveň] (50%)
RRR: [přesný poměr risk/reward, např. 2.5:1]
Časový horizont: [krátkodobý/střednědobý/dlouhodobý]
Platnost: [konkrétní časový údaj]

- Pokud je jedna z variant (LONG/SHORT) mnohem méně pravděpodobná vzhledem k tržnímu kontextu, uveďte pouze tu pravděpodobnější variantu
- NEZAHRNUJTE žádné závěrečné shrnutí ani varování

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
            
            return analysis, support_zones, resistance_zones
            
        except Exception as e:
            raise Exception(f"Chyba při generování multi-timeframe analýzy: {str(e)}")

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
                r"[Ss]upport.*?([0-9,.-]+)-([0-9,.-]+)"
            ]
        else:  # resistance
            patterns = [
                r"[Rr]esistenční zón[ay]:\s*([0-9,.-]+)-([0-9,.-]+)",
                r"[Rr]esisten[cč][en]í zón[ay]?.*?([0-9,.-]+)-([0-9,.-]+)",
                r"[Rr]esisten[cč][en].*?([0-9,.-]+)-([0-9,.-]+)"
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
        
        # Omezení počtu zón pro lepší přehlednost a výkon (max 5)
        if len(zones) > 5:
            zones = zones[:5]
            
        return zones

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
