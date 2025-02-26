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

        prompt = f"""Jste senior trader specializující se na price action analýzu. Analyzujte data s důrazem na všechny časové rámce, bez poskytování konkrétních vstupních bodů.

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
  - DŮLEŽITÉ: Uveďte konkrétní cenové cíle ve formátu čísla (např. 92000), ne jako rozsah
  - Popište, jak by cena mohla narážet na klíčové rezistence během své cesty nahoru
- Bearish scénář (popište podmínky, spouštěče a potenciální cílové úrovně) 
  - DŮLEŽITÉ: Uveďte konkrétní cenové cíle ve formátu čísla (např. 84000), ne jako rozsah
  - Popište, jak by cena mohla narážet na klíčové supporty během své cesty dolů
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
        
        # Hledat sekci "MOŽNÉ SCÉNÁŘE DALŠÍHO VÝVOJE" nebo podobnou
        scenario_section = re.search(r'(MOŽNÉ SCÉNÁŘE|SCÉNÁŘE|SCENÁŘE|VÝVOJE)(.*?)(##|\Z)', 
                                    analysis, re.DOTALL | re.IGNORECASE)
        
        if scenario_section:
            scenario_text = scenario_section.group(2)
            
            # Hledání bullish scénáře a ceny - přesnější pattern zaměřený na číselné cíle
            bullish_target = None
            bullish_section = re.search(r'[Bb]ullish.*?(\d{4,6})', scenario_text)
            if bullish_section:
                try:
                    bullish_target = float(bullish_section.group(1).replace(',', '.'))
                    if bullish_target > current_price * 1.005:  # Musí být aspoň 0.5% nad aktuální cenou
                        scenarios.append(('bullish', bullish_target))
                except (ValueError, IndexError):
                    pass
            
            # Pokud nebyl nalezen konkrétní cíl, hledej i v jiných formátech
            if not bullish_target:
                bullish_patterns = [
                    r"[Bb]ullish.*?(\d{4,6})",
                    r"[Vv]zhůru.*?(\d{4,6})",
                    r"[Rr]ůst.*?(\d{4,6})",
                    r"[Cc]íl.*?(\d{4,6})"
                ]
                
                for pattern in bullish_patterns:
                    matches = re.findall(pattern, scenario_text)
                    for match in matches:
                        try:
                            price = float(match.replace(',', '.'))
                            if price > current_price * 1.005:  # Musí být aspoň 0.5% nad aktuální cenou
                                scenarios.append(('bullish', price))
                                break
                        except (ValueError, IndexError):
                            continue
                    if len(scenarios) > 0 and scenarios[-1][0] == 'bullish':
                        break
            
            # Hledání bearish scénáře a ceny - přesnější pattern zaměřený na číselné cíle
            bearish_target = None
            bearish_section = re.search(r'[Bb]earish.*?(\d{4,6})', scenario_text)
            if bearish_section:
                try:
                    bearish_target = float(bearish_section.group(1).replace(',', '.'))
                    if bearish_target < current_price * 0.995:  # Musí být aspoň 0.5% pod aktuální cenou
                        scenarios.append(('bearish', bearish_target))
                except (ValueError, IndexError):
                    pass
            
            # Pokud nebyl nalezen konkrétní cíl, hledej i v jiných formátech
            if not bearish_target:
                bearish_patterns = [
                    r"[Bb]earish.*?(\d{4,6})",
                    r"[Pp]okles.*?(\d{4,6})",
                    r"[Pp]ád.*?(\d{4,6})",
                    r"[Dd]olů.*?(\d{4,6})"
                ]
                
                for pattern in bearish_patterns:
                    matches = re.findall(pattern, scenario_text)
                    for match in matches:
                        try:
                            price = float(match.replace(',', '.'))
                            if price < current_price * 0.995:  # Musí být aspoň 0.5% pod aktuální cenou
                                scenarios.append(('bearish', price))
                                break
                        except (ValueError, IndexError):
                            continue
                    if len(scenarios) > 0 and scenarios[-1][0] == 'bearish':
                        break
        
        # Pokud jsme nenašli žádné scénáře, zkusíme prohledat celý text
        if not scenarios:
            # Obecný pattern pro nalezení cenových hodnot
            price_pattern = r'\b(\d{4,6})\b'
            prices = re.findall(price_pattern, analysis)
            
            prices = [float(p) for p in prices if p.isdigit()]
            prices = sorted(list(set(prices)))  # Deduplikace a seřazení
            
            # Identifikace bullish a bearish cílů na základě aktuální ceny
            bullish_target = None
            bearish_target = None
            
            for price in prices:
                if price > current_price * 1.05:  # 5% nad aktuální cenou
                    if not bullish_target or price > bullish_target:
                        bullish_target = price
                elif price < current_price * 0.95:  # 5% pod aktuální cenou
                    if not bearish_target or price < bearish_target:
                        bearish_target = price
            
            if bullish_target:
                scenarios.append(('bullish', bullish_target))
            if bearish_target:
                scenarios.append(('bearish', bearish_target))
        
        # Logování nalezených scénářů pro ladění
        logger.info(f"Nalezené scénáře: {scenarios}")
        
        return scenarios

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
                value_pattern = r'[Ss]upport.*?([0-9,.-]+)'
            else:
                value_pattern = r'[Rr]esisten[cč][en].*?([0-9,.-]+)'
        
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
