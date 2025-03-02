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

    def generate_intraday_analysis(self, symbol, dataframes):
        """
        Generuje analýzu zaměřenou na intraday obchodování.
    
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
        all_timeframes = ["4h", "30m", "5m"]
    
        for tf in all_timeframes:
            if tf in dataframes:
                df = dataframes[tf]
                num_candles = 5 if tf in ['4h'] else (10 if tf == '30m' else 15)
        
                tf_data = f"## Časový rámec: {tf}\n"
                tf_data += f"Rozsah dat: {df.index[0]} až {df.index[-1]}\n"
                tf_data += f"Počet svíček: {len(df)}\n"
                tf_data += f"Posledních {num_candles} svíček:\n"
                tf_data += f"{df[['open','high','low','close','volume']].tail(num_candles).to_markdown()}\n\n"
        
                patterns = patterns_by_tf[tf]
                if patterns:
                    tf_data += f"Poslední patterny:\n"
                    for pattern in patterns[-8:]:  # Zobrazíme více patternů pro intraday analýzu
                        tf_data += f"- {pattern[0]} na úrovni {pattern[2]:.2f}-{pattern[3]:.2f} ({pattern[1]})\n"
            
                timeframe_data.append(tf_data)

        # Získáme aktuální cenu z posledního dataframe
        latest_price = None
        if '30m' in dataframes:
            latest_price = dataframes['30m']['close'].iloc[-1]
        elif '5m' in dataframes:
            latest_price = dataframes['5m']['close'].iloc[-1]
        elif '4h' in dataframes:
            latest_price = dataframes['4h']['close'].iloc[-1]

        prompt = f"""Jste senior intraday trader specializující se na price action analýzu se zaměřením na intradenní obchodování. Analyzujte data s důrazem na krátkodobé příležitosti.

Symbol: {symbol}
Aktuální cena: {latest_price:.2f}
# DATA PODLE ČASOVÝCH RÁMCŮ
{''.join(timeframe_data)}

## 1. 📊 KRÁTKODOBÝ TREND A KONTEXT (4h)
- Popište aktuální strukturu trhu (vyšší high/low, nižší high/low)
- Objemový profil (kde se koncentruje nejvíce objemu)
- Pozice v rámci vyššího trendu

### HLAVNÍ SUPPORTNÍ ZÓNY:
- (Uveďte 1-2 klíčové supportní zóny POUZE POD aktuální cenou {latest_price:.2f}, každou na nový řádek ve formátu "min-max")
- Příklad správného formátu: "78250-81000" (vždy musí být min < max a max < {latest_price:.2f})

### HLAVNÍ RESISTENČNÍ ZÓNY:
- (Uveďte 1-2 klíčové resistenční zóny POUZE NAD aktuální cenou {latest_price:.2f}, každou na nový řádek ve formátu "min-max")
- Příklad správného formátu: "90000-92000" (vždy musí být min > {latest_price:.2f} a min < max)

## 2. 🔍 INTRADAY PŘÍLEŽITOSTI (30m)
- Aktuální situace v 30-minutovém timeframe
- Klíčové patterny a významné cenové akce
- Potenciální objemové divergence
- Býčí/medvědí bias

## 3. 🔎 SCALPING SETUPS (5m)
- Specifické price action patterny (např. pin bar, engulfing, inside bar)
- Order Blocks a FVG zóny
- Cenové mezery (gaps)

## 4. 💡 KONKRÉTNÍ OBCHODNÍ PŘÍLEŽITOSTI
- Přesné vstupní úrovně s popisem typu vstupu (breakout/pullback)
- Stop loss úrovně
- Take profit úrovně (alespoň 2 pro postupné vybírání zisku)
- Časová platnost setupu

DŮLEŽITÉ:
- SUPPORTNÍ ZÓNY MUSÍ BÝT VŽDY POD AKTUÁLNÍ CENOU, RESISTENČNÍ ZÓNY VŽDY NAD! Žádná supportní zóna nemůže být nad resistenční zónou!
- KONKRÉTNÍ informace, žádný vágní text
- Přehledné a stručné odrážky
- DODRŽUJTE přesný formát pro supportní a resistenční zóny jako "min-max" (např. "85721-85532")
- NEVKLÁDEJTE sekce, pro které nemáte data
- NEZAHRNUJTE závěrečné shrnutí ani varování na konci analýzy"""

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
        Tato verze je určena pro swing analýzu se zaměřením na středně až dlouhodobé obchodování.
    
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
        all_timeframes = ["1w", "1d", "4h"]
    
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
- Fázová analýza trhu (akumulace/distribuce, trendové/nárazové pohyby)
- Klíčové weekly/daily uzávěry
- Fair Value Gaps (FVG) s přesnými úrovněmi cen (pokud existují)
- Order Blocks (OB) s přesnými úrovněmi cen (pokud existují)

### HLAVNÍ SUPPORTNÍ ZÓNY:
- (Uveďte 1-2 supportní zóny POUZE POD aktuální cenou {latest_price:.2f}, každou na nový řádek ve formátu "min-max")
- Příklad správného formátu: "78250-81000" (vždy musí být min < max a max < {latest_price:.2f})

### HLAVNÍ RESISTENČNÍ ZÓNY:
- (Uveďte 1-2 resistenční zóny POUZE NAD aktuální cenou {latest_price:.2f}, každou na nový řádek ve formátu "min-max")
- Příklad správného formátu: "90000-92000" (vždy musí být min > {latest_price:.2f} a min < max)

## 2. 🔍 STŘEDNĚDOBÝ KONTEXT (4H)
- Pozice v rámci vyššího trendu
- Významné cenové nerovnováhy (FVG) (pokud existují)
- Order Blocks na 4H timeframu (pokud existují)
- Objemové klastry

## 3. 💡 MOŽNÉ SCÉNÁŘE DALŠÍHO VÝVOJE

### BULLISH SCÉNÁŘ:
- Podmínky a spouštěče
- Cílová úroveň: [PŘESNÁ HODNOTA > {latest_price:.2f}]

### BEARISH SCÉNÁŘ:
- Podmínky a spouštěče
- Cílová úroveň: [PŘESNÁ HODNOTA < {latest_price:.2f}]

### NEUTRÁLNÍ SCÉNÁŘ:
- Podmínky a pravděpodobnost konsolidace
- Očekávaný rozsah: [MIN]-[MAX] (musí zahrnovat aktuální cenu {latest_price:.2f})

## 4. ⚠️ VÝZNAMNÉ ÚROVNĚ K SLEDOVÁNÍ
- Důležité swingové high/low
- ŽÁDNÉ KONKRÉTNÍ VSTUPY - pouze úrovně k sledování
- Nezahrnujte sekce, pro které nemáte dostatek dat - pokud nemáte pivot pointy, prostě je nevyjmenovávejte

DŮLEŽITÉ:
- SUPPORTNÍ ZÓNY MUSÍ BÝT VŽDY POD AKTUÁLNÍ CENOU, RESISTENČNÍ ZÓNY VŽDY NAD! Žádná supportní zóna nemůže být nad resistenční zónou!
- DODRŽUJTE přesný formát pro supportní a resistenční zóny jako "min-max" (např. "85721-85532")
- Všechny supportní a resistenční zóny musí být ve správném pořadí vůči aktuální ceně
- NEZAHRNUJTE žádné závěrečné shrnutí ani varování na konci analýzy
- NEPIŠTE fráze jako "Tato analýza poskytuje přehled" nebo podobné shrnující věty
- NEVKLÁDEJTE sekce, pro které nemáte data - pokud něco nelze určit, sekci vynechte
- Přehledné a stručné odrážky
- Pouze konkrétní informace, žádný vágní text
- Nepoužívejte žádná varování ani 'AI' fráze (například vyhněte se 'vždy si ověřte aktuální tržní podmínky')"""

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
            raise Exception(f"Chyba při generování swing analýzy: {str(e)}")

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
        
        # Hledání bullish scénáře
        bullish_section = re.search(r"### BULLISH SCÉNÁŘ:(.*?)###", analysis, re.DOTALL)
        if bullish_section:
            # Hledání cílové úrovně
            target_match = re.search(r"Cílová úroveň:\s*\[?(\d+(?:[.,]\d+)?)\]?", bullish_section.group(1))
            if target_match:
                try:
                    bullish_target = float(target_match.group(1).replace(',', '.'))
                    if bullish_target > current_price:
                        scenarios.append(('bullish', bullish_target))
                        logger.info(f"Extrahován bullish scénář s cílem: {bullish_target}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Chyba při zpracování bullish scénáře: {str(e)}")
        
        # Hledání bearish scénáře
        bearish_section = re.search(r"### BEARISH SCÉNÁŘ:(.*?)###", analysis, re.DOTALL)
        if bearish_section:
            # Hledání cílové úrovně
            target_match = re.search(r"Cílová úroveň:\s*\[?(\d+(?:[.,]\d+)?)\]?", bearish_section.group(1))
            if target_match:
                try:
                    bearish_target = float(target_match.group(1).replace(',', '.'))
                    if bearish_target < current_price:
                        scenarios.append(('bearish', bearish_target))
                        logger.info(f"Extrahován bearish scénář s cílem: {bearish_target}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Chyba při zpracování bearish scénáře: {str(e)}")
        
        # Hledání neutrálního scénáře
        neutral_section = re.search(r"### NEUTRÁLNÍ SCÉNÁŘ:(.*?)(?:##|\Z)", analysis, re.DOTALL)
        if neutral_section:
            # Hledání očekávaného rozsahu
            range_match = re.search(r"Očekávaný rozsah:\s*\[?(\d+(?:[.,]\d+)?)\]?-\[?(\d+(?:[.,]\d+)?)\]?", neutral_section.group(1))
            if range_match:
                try:
                    lower_bound = float(range_match.group(1).replace(',', '.'))
                    upper_bound = float(range_match.group(2).replace(',', '.'))
                    if lower_bound < upper_bound:
                        scenarios.append(('neutral', (lower_bound, upper_bound)))
                        logger.info(f"Extrahován neutrální scénář s rozsahem: {lower_bound}-{upper_bound}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Chyba při zpracování neutrálního scénáře: {str(e)}")
        
        # Pokud nejsou nalezeny žádné scénáře, použijeme fallback metodu
        if not scenarios:
            logger.warning("Nebyly nalezeny žádné strukturované scénáře, zkouším fallback metodu")
            
            # Hledání zmínek o možných cílech
            bullish_matches = re.findall(r"[Bb]ullish.*?cíl.*?(\d{4,6}(?:[.,]\d+)?)", analysis)
            bearish_matches = re.findall(r"[Bb]earish.*?cíl.*?(\d{4,6}(?:[.,]\d+)?)", analysis)
            
            if bullish_matches:
                try:
                    bullish_target = float(bullish_matches[0].replace(',', '.'))
                    if bullish_target > current_price * 1.005:  # Alespoň 0.5% nad aktuální cenou
                        scenarios.append(('bullish', bullish_target))
                except (ValueError, IndexError):
                    pass
                    
            if bearish_matches:
                try:
                    bearish_target = float(bearish_matches[0].replace(',', '.'))
                    if bearish_target < current_price * 0.995:  # Alespoň 0.5% pod aktuální cenou
                        scenarios.append(('bearish', bearish_target))
                except (ValueError, IndexError):
                    pass
        
        logger.info(f"Extrahované scénáře: {scenarios}")
        return scenarios

    def extract_zones_from_analysis(self, analysis, zone_type, current_price=None):
        """
        Extrahuje zóny supportů nebo resistancí z textu analýzy.
    
        Args:
            analysis (str): Text analýzy
            zone_type (str): Typ zóny ('support' nebo 'resistance')
            current_price (float, optional): Aktuální cena pro validaci zón
        
        Returns:
            list: Seznam zón ve formátu [(min1, max1), (min2, max2), ...]
        """
        zones = []
    
        # Určení správného nadpisu sekce podle typu zóny
        if zone_type.lower() == "support":
            section_header = "### HLAVNÍ SUPPORTNÍ ZÓNY:"
        else:
            section_header = "### HLAVNÍ RESISTENČNÍ ZÓNY:"
    
        # Hledání sekce se zónami
        section_pattern = f"{re.escape(section_header)}(.*?)(?:###|\Z)"
        section_match = re.search(section_pattern, analysis, re.DOTALL)
    
        if section_match:
            section_text = section_match.group(1).strip()
            logger.info(f"Nalezena sekce {zone_type} zón: {section_text}")
        
            # Hledání všech odrážek s cenovými rozsahy
            bullet_points = re.findall(r"- (\d+(?:[.,]\d+)?)-(\d+(?:[.,]\d+)?)", section_text)
        
            for min_price, max_price in bullet_points:
                try:
                    min_value = float(min_price.replace(',', '.'))
                    max_value = float(max_price.replace(',', '.'))
                
                    # Základní validace hodnot
                    if min_value >= max_value:
                        logger.warning(f"Ignorována neplatná zóna s min >= max: {min_value}-{max_value}")
                        continue
                
                    # Pokud je poskytnuta aktuální cena, validujeme zóny proti ní
                    if current_price is not None:
                        if zone_type.lower() == "support" and max_value >= current_price:
                            logger.warning(f"Ignorována supportní zóna nad nebo na aktuální ceně: {min_value}-{max_value} (aktuální: {current_price})")
                            continue
                        elif zone_type.lower() == "resistance" and min_value <= current_price:
                            logger.warning(f"Ignorována resistenční zóna pod nebo na aktuální ceně: {min_value}-{max_value} (aktuální: {current_price})")
                            continue
                
                    zones.append((min_value, max_value))
                    logger.info(f"Extrahována {zone_type} zóna: {min_value}-{max_value}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Chyba při zpracování {zone_type} zóny: {str(e)}")
                    continue
        else:
            logger.warning(f"Sekce {section_header} nebyla nalezena v textu")
            
        # Fallback - zkusíme hledat v textu podle obecnějších vzorů
        if not zones:
            logger.warning(f"Použití fallback metody pro detekci {zone_type} zón")
        
            if zone_type.lower() == "support":
                patterns = [
                    r"[Ss]upportní zón[ay]?:?\s*(\d+(?:[.,]\d+)?)-(\d+(?:[.,]\d+)?)",
                    r"[Pp]odpora:?\s*(\d+(?:[.,]\d+)?)-(\d+(?:[.,]\d+)?)"
                ]
            else:
                patterns = [
                    r"[Rr]esistenční zón[ay]?:?\s*(\d+(?:[.,]\d+)?)-(\d+(?:[.,]\d+)?)",
                    r"[Rr]ezistence:?\s*(\d+(?:[.,]\d+)?)-(\d+(?:[.,]\d+)?)"
                ]
        
            for pattern in patterns:
                matches = re.findall(pattern, analysis)
                for min_price, max_price in matches:
                    try:
                        min_value = float(min_price.replace(',', '.'))
                        max_value = float(max_price.replace(',', '.'))
                    
                        # Základní validace hodnot
                        if min_value >= max_value:
                            logger.warning(f"Ignorována neplatná zóna s min >= max: {min_value}-{max_value}")
                            continue
                    
                        # Pokud je poskytnuta aktuální cena, validujeme zóny proti ní
                        if current_price is not None:
                            if zone_type.lower() == "support" and max_value >= current_price:
                                logger.warning(f"Ignorována supportní zóna nad nebo na aktuální ceně: {min_value}-{max_value} (aktuální: {current_price})")
                                continue
                            elif zone_type.lower() == "resistance" and min_value <= current_price:
                                logger.warning(f"Ignorována resistenční zóna pod nebo na aktuální ceně: {min_value}-{max_value} (aktuální: {current_price})")
                                continue
                    
                        zones.append((min_value, max_value))
                        logger.info(f"Extrahována {zone_type} zóna fallbackem: {min_value}-{max_value}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Chyba při zpracování {zone_type} zóny: {str(e)}")
                        continue
    
        # Deduplikace zón
        unique_zones = []
        for zone in zones:
            if zone not in unique_zones:
                unique_zones.append(zone)
    
        # Seřazení zón podle relevance k aktuální ceně
        if current_price is not None:
            if zone_type.lower() == "support":
                # Seřadit supportní zóny sestupně (nejvyšší první - blíže aktuální ceně)
                unique_zones.sort(key=lambda x: x[0], reverse=True)
            else:
                # Seřadit resistenční zóny vzestupně (nejnižší první - blíže aktuální ceně)
                unique_zones.sort(key=lambda x: x[0])
    
        return unique_zones

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
