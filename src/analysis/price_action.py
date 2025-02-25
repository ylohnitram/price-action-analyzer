#!/usr/bin/env python3

from datetime import datetime
from openai import OpenAI
import pandas as pd

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
            str: Vygenerovaná intraday analýza
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

# ZADÁNÍ ANALÝZY
1. 🕵️♂️ 4H KONTEXT (max 3 body)
- Trendový směr
- Nejdůležitější support/resistance

2. 📈 30M SETUPY
- 3 klíčové hladiny pro dnešek
- Potenciální směr pohybu
- Ideální vstupní zóny

3. ⚡ 5M PŘÍLEŽITOSTI (pouze pokud kvalitní)
- Konkrétní vstupní úrovně
- Cíle a rizika
- Časová relevance (dopoledne/odpoledne)

Formát:
- Max 8 odrážek
- Používejte bublinové emoji pro úrovně: 🔵-strong, 🟢-moderate, 🟡-weak
- Žádný úvod/závěr
- Časové okno: {datetime.now().strftime("%H:%M")}-{datetime.now().replace(hour=22, minute=0).strftime("%H:%M")}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2500
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Chyba při generování intraday analýzy: {str(e)}")

    def generate_multi_timeframe_analysis(self, symbol, dataframes):
        """
        Generuje multi-timeframe analýzu na základě dat z různých časových rámců.
        
        Args:
            symbol (str): Obchodní symbol
            dataframes (dict): Slovník s DataFrame pro různé časové rámce
            
        Returns:
            str: Vygenerovaná analýza
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

# ZADÁNÍ ANALÝZY
Vytvořte stručnou multi-timeframe analýzu v češtině se zaměřením na:
## 1. DLOUHODOBÝ TREND (1W/1D)
- Hlavní support/resistance zóny (min. 3 významné úrovně)
- Fázová analýza trhu (akumulace/distribuce, trendové/nárazové pohyby)
- Klíčové weekly/daily uzávěry

## 2. STŘEDNĚDOBÝ KONTEXT (4H)
- Pozice v rámci vyššího trendu
- Významné cenové mezery (imbalance zones)
- Objemové klastry

## 3. KRÁTKODOBÉ SIGNÁLY (30m/5m) [POUZE POKUD RELEVANTNÍ]
- Výrazné price action patterny
- Likvidní úrovně pro vstupy
- Rychlé obchodní příležitosti (max 2 pokud existují)

Formát:
- Max 10 odrážek
- Používejte emoji pro vizuální oddělení sekcí (🎯📉📈⚠️)
- Žádné úvodní fráze, pouze fakta
- Časové razítko: {datetime.now().strftime("%d.%m.%Y %H:%M")}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=3000
            )
            return response.choices[0].message.content
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
            str: Vygenerovaná analýza
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
1. Významné cenové mezery
2. Silné zóny na grafu
3. Falešné průrazy klíčových úrovní
4. Vztah mezi cenou a objemem
5. Konkrétní obchodní příležitosti s přesnými vstupními úrovněmi

Formát:
- Stručné odrážky
- Konkrétní cenové úrovně z dat
- Žádné technické indikátory
- Časové razítko: {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            return response.choices[0].message.content
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

