#!/usr/bin/env python3

import matplotlib
# Nastavení neinteraktivního backend před importem pyplot
matplotlib.use('Agg')

import logging
import re
from datetime import datetime
import os

# Importy specializovaných grafů
from src.visualization.charts.intraday_chart import IntradayChart
from src.visualization.charts.swing_chart import SwingChart
from src.visualization.charts.simple_chart import SimpleChart

logger = logging.getLogger(__name__)

class ChartGenerator:
    """
    Hlavní třída pro generování grafů. Koordinuje výběr správného typu grafu
    podle typu analýzy a deleguje vykreslování na specializované třídy.
    """
    
    def extract_zones_from_text(self, analysis_text):
        """
        Extrahuje zóny supportů a resistencí z textu analýzy.
        Očekává strukturované sekce ve formátu '### HLAVNÍ SUPPORTNÍ ZÓNY:' a '### HLAVNÍ RESISTENČNÍ ZÓNY:'.
        
        Args:
            analysis_text (str): Text analýzy
            
        Returns:
            tuple: (support_zones, resistance_zones) jako seznamy (min, max) tuple
        """
        support_zones = []
        resistance_zones = []
        
        # Extrakce supportních zón
        support_section = re.search(r"### HLAVNÍ SUPPORTNÍ ZÓNY:(.*?)(?:###|\Z)", analysis_text, re.DOTALL)
        if support_section:
            section_text = support_section.group(1).strip()
            logger.info(f"Nalezena sekce supportních zón: {section_text}")
            
            # Hledání všech odrážek s cenovými rozsahy
            bullet_points = re.findall(r"- (\d+(?:[.,]\d+)?)-(\d+(?:[.,]\d+)?)", section_text)
            
            for min_price, max_price in bullet_points:
                try:
                    min_value = float(min_price.replace(',', '.'))
                    max_value = float(max_price.replace(',', '.'))
                    
                    # Validace hodnot
                    if min_value < max_value:
                        support_zones.append((min_value, max_value))
                        logger.info(f"Extrahována supportní zóna: {min_value}-{max_value}")
                    else:
                        logger.warning(f"Ignorována neplatná support zóna s min > max: {min_value}-{max_value}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Chyba při zpracování supportní zóny: {str(e)}")
                    continue
        else:
            logger.warning("Strukturovaná sekce supportních zón nebyla nalezena")
        
        # Extrakce resistenčních zón
        resistance_section = re.search(r"### HLAVNÍ RESISTENČNÍ ZÓNY:(.*?)(?:###|\Z)", analysis_text, re.DOTALL)
        if resistance_section:
            section_text = resistance_section.group(1).strip()
            logger.info(f"Nalezena sekce resistenčních zón: {section_text}")
            
            # Hledání všech odrážek s cenovými rozsahy
            bullet_points = re.findall(r"- (\d+(?:[.,]\d+)?)-(\d+(?:[.,]\d+)?)", section_text)
            
            for min_price, max_price in bullet_points:
                try:
                    min_value = float(min_price.replace(',', '.'))
                    max_value = float(max_price.replace(',', '.'))
                    
                    # Validace hodnot
                    if min_value < max_value:
                        resistance_zones.append((min_value, max_value))
                        logger.info(f"Extrahována resistenční zóna: {min_value}-{max_value}")
                    else:
                        logger.warning(f"Ignorována neplatná resistance zóna s min > max: {min_value}-{max_value}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Chyba při zpracování resistenční zóny: {str(e)}")
                    continue
        else:
            logger.warning("Strukturovaná sekce resistenčních zón nebyla nalezena")
        
        # Fallback - pokud v popisku nebyla nalezena žádná sekce v očekávaném formátu
        if not support_zones or not resistance_zones:
            logger.warning("Použití alternativní metody pro detekci zón")
            
            # Hledání v sekci KRÁTKODOBÝ TREND A KONTEXT (pro intraday analýzy)
            trend_section = re.search(r"KRÁTKODOBÝ TREND A KONTEXT[^#]*", analysis_text, re.IGNORECASE | re.DOTALL)
            if trend_section and (not support_zones or not resistance_zones):
                section_text = trend_section.group(0)
                
                # Hledání zmínek o podpoře a rezistenci
                if not support_zones:
                    support_matches = re.findall(r"[Pp]odpora:?\s*(\d+(?:[.,]\d+)?)-(\d+(?:[.,]\d+)?)", section_text)
                    for min_price, max_price in support_matches:
                        try:
                            min_value = float(min_price.replace(',', '.'))
                            max_value = float(max_price.replace(',', '.'))
                            if min_value < max_value:
                                support_zones.append((min_value, max_value))
                                logger.info(f"Extrahována supportní zóna z trendu: {min_value}-{max_value}")
                        except (ValueError, IndexError):
                            continue
                
                if not resistance_zones:
                    resistance_matches = re.findall(r"[Rr]ezistence:?\s*(\d+(?:[.,]\d+)?)-(\d+(?:[.,]\d+)?)", section_text)
                    for min_price, max_price in resistance_matches:
                        try:
                            min_value = float(min_price.replace(',', '.'))
                            max_value = float(max_price.replace(',', '.'))
                            if min_value < max_value:
                                resistance_zones.append((min_value, max_value))
                                logger.info(f"Extrahována rezistenční zóna z trendu: {min_value}-{max_value}")
                        except (ValueError, IndexError):
                            continue
        
        # Limitování počtu zón na maximálně 2 pro lepší přehlednost v grafu
        if len(support_zones) > 2:
            logger.info(f"Omezení počtu supportních zón z {len(support_zones)} na 2")
            support_zones = support_zones[:2]
        
        if len(resistance_zones) > 2:
            logger.info(f"Omezení počtu resistenčních zón z {len(resistance_zones)} na 2")
            resistance_zones = resistance_zones[:2]
        
        logger.info(f"Finální supportní zóny: {support_zones}")
        logger.info(f"Finální resistenční zóny: {resistance_zones}")
        
        return support_zones, resistance_zones
    
    def extract_scenarios_from_text(self, analysis_text, current_price):
        """
        Extrahuje scénáře pro vizualizaci z textu analýzy.
        Očekává strukturované sekce jako '### BULLISH SCÉNÁŘ:' atd.
        
        Args:
            analysis_text (str): Text analýzy
            current_price (float): Aktuální cena
            
        Returns:
            list: Seznam scénářů jako [('bullish', target_price), ('bearish', target_price), ...]
        """
        scenarios = []
        
        # Hledání bullish scénáře
        bullish_section = re.search(r"### BULLISH SCÉNÁŘ:(.*?)(?:###|\Z)", analysis_text, re.DOTALL)
        if bullish_section:
            # Hledání cílové úrovně
            target_match = re.search(r"Cílová úroveň:?\s*\[?(\d+(?:[.,]\d+)?)\]?", bullish_section.group(1))
            if target_match:
                try:
                    bullish_target = float(target_match.group(1).replace(',', '.'))
                    if bullish_target > current_price:
                        scenarios.append(('bullish', bullish_target))
                        logger.info(f"Extrahován bullish scénář s cílem: {bullish_target}")
                    else:
                        logger.warning(f"Bullish cíl {bullish_target} není nad aktuální cenou {current_price}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Chyba při zpracování bullish scénáře: {str(e)}")
        else:
            logger.info("Bullish scénář nebyl nalezen v strukturované sekci")
        
        # Hledání bearish scénáře
        bearish_section = re.search(r"### BEARISH SCÉNÁŘ:(.*?)(?:###|\Z)", analysis_text, re.DOTALL)
        if bearish_section:
            # Hledání cílové úrovně
            target_match = re.search(r"Cílová úroveň:?\s*\[?(\d+(?:[.,]\d+)?)\]?", bearish_section.group(1))
            if target_match:
                try:
                    bearish_target = float(target_match.group(1).replace(',', '.'))
                    if bearish_target < current_price:
                        scenarios.append(('bearish', bearish_target))
                        logger.info(f"Extrahován bearish scénář s cílem: {bearish_target}")
                    else:
                        logger.warning(f"Bearish cíl {bearish_target} není pod aktuální cenou {current_price}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Chyba při zpracování bearish scénáře: {str(e)}")
        else:
            logger.info("Bearish scénář nebyl nalezen v strukturované sekci")
        
        # Hledání neutrálního scénáře
        neutral_section = re.search(r"### NEUTRÁLNÍ SCÉNÁŘ:(.*?)(?:###|\Z)", analysis_text, re.DOTALL)
        if neutral_section:
            # Hledání očekávaného rozsahu
            range_match = re.search(r"Očekávaný rozsah:?\s*\[?(\d+(?:[.,]\d+)?)\]?-\[?(\d+(?:[.,]\d+)?)\]?", neutral_section.group(1))
            if range_match:
                try:
                    lower_bound = float(range_match.group(1).replace(',', '.'))
                    upper_bound = float(range_match.group(2).replace(',', '.'))
                    if lower_bound < upper_bound:
                        scenarios.append(('neutral', (lower_bound, upper_bound)))
                        logger.info(f"Extrahován neutrální scénář s rozsahem: {lower_bound}-{upper_bound}")
                    else:
                        logger.warning(f"Neutrální rozsah {lower_bound}-{upper_bound} má min > max")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Chyba při zpracování neutrálního scénáře: {str(e)}")
        else:
            logger.info("Neutrální scénář nebyl nalezen v strukturované sekci")
        
        # Fallback - pokud nebyly nalezeny žádné scénáře ve strukturovaném formátu
        if not scenarios:
            logger.warning("Použití alternativní metody pro detekci scénářů")
            
            # Hledání v sekci možných scénářů
            scenario_section = re.search(r"MOŽNÉ SCÉNÁŘE DALŠÍHO VÝVOJE(.*?)(?:##|\Z)", analysis_text, re.DOTALL | re.IGNORECASE)
            if scenario_section:
                scenario_text = scenario_section.group(1)
                
                # Hledání bullish cíle
                if not any(s[0] == 'bullish' for s in scenarios):
                    bullish_matches = re.findall(r"[Bb]ullish.*?(\d{4,6}(?:[.,]\d+)?)", scenario_text)
                    if bullish_matches:
                        try:
                            bullish_target = float(bullish_matches[0].replace(',', '.'))
                            if bullish_target > current_price * 1.005:  # Alespoň 0.5% nad aktuální cenou
                                scenarios.append(('bullish', bullish_target))
                                logger.info(f"Extrahován bullish scénář alternativním způsobem: {bullish_target}")
                        except (ValueError, IndexError):
                            pass
                
                # Hledání bearish cíle
                if not any(s[0] == 'bearish' for s in scenarios):
                    bearish_matches = re.findall(r"[Bb]earish.*?(\d{4,6}(?:[.,]\d+)?)", scenario_text)
                    if bearish_matches:
                        try:
                            bearish_target = float(bearish_matches[0].replace(',', '.'))
                            if bearish_target < current_price * 0.995:  # Alespoň 0.5% pod aktuální cenou
                                scenarios.append(('bearish', bearish_target))
                                logger.info(f"Extrahován bearish scénář alternativním způsobem: {bearish_target}")
                        except (ValueError, IndexError):
                            pass
        
        logger.info(f"Finální scénáře: {scenarios}")
        return scenarios

    def generate_chart(self, df, support_zones, resistance_zones, symbol, 
                      filename=None, days_to_show=5, hours_to_show=None, 
                      timeframe=None, scenarios=None, analysis_text=None,
                      analysis_type="intraday"):
        """
        Generuje svíčkový graf s podporami, resistencemi a scénáři podle typu analýzy.
        
        Args:
            df (pandas.DataFrame): DataFrame s OHLCV daty
            support_zones (list): Seznam podporních zón jako (min, max) tuples
            resistance_zones (list): Seznam resistenčních zón jako (min, max) tuples
            symbol (str): Trading symbol
            filename (str, optional): Cesta k souboru pro uložení grafu
            days_to_show (int, optional): Počet dní k zobrazení (default: 5)
            hours_to_show (int, optional): Počet hodin k zobrazení (přepíše days_to_show)
            timeframe (str, optional): Časový rámec dat
            scenarios (list, optional): Seznam scénářů jako (typ, cena) tuples
            analysis_text (str, optional): Text analýzy pro extrakci dat
            analysis_type (str, optional): Typ analýzy - "swing", "intraday" nebo "simple"
            
        Returns:
            str: Cesta k vygenerovanému grafickému souboru
        """
        # Logování základních informací
        logger.info(f"Generuji graf pro {symbol} ({timeframe}), typ analýzy: {analysis_type}")
        
        # Nastavení výchozí cesty pro uložení grafu
        if not filename:
            charts_dir = "charts"
            os.makedirs(charts_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(charts_dir, f"{symbol}_{timeframe}_{timestamp}.png")
        
        # Extrakce zón z textu, pokud nebyly předány nebo jsou prázdné
        if analysis_text and (not support_zones or not resistance_zones):
            extracted_support, extracted_resistance = self.extract_zones_from_text(analysis_text)
            
            if not support_zones:
                support_zones = extracted_support
                logger.info(f"Použití extrahovaných supportních zón: {support_zones}")
            
            if not resistance_zones:
                resistance_zones = extracted_resistance
                logger.info(f"Použití extrahovaných resistenčních zón: {resistance_zones}")
        
        # Extrakce scénářů z textu, pokud nebyly předány a jedná se o swing analýzu
        if analysis_type == "swing" and not scenarios and analysis_text:
            try:
                current_price = df['close'].iloc[-1] if len(df) > 0 else None
                if current_price:
                    scenarios = self.extract_scenarios_from_text(analysis_text, current_price)
                    logger.info(f"Použití extrahovaných scénářů: {scenarios}")
            except Exception as e:
                logger.error(f"Chyba při extrakci scénářů: {str(e)}")
        
        # Výběr správného typu grafu podle typu analýzy
        try:
            if analysis_type == "swing":
                chart = SwingChart(
                    df, 
                    symbol, 
                    timeframe=timeframe, 
                    days_to_show=days_to_show
                )
                chart.add_support_zones(support_zones)
                chart.add_resistance_zones(resistance_zones)
                if scenarios:
                    chart.add_scenarios(scenarios)
            
            elif analysis_type == "intraday":
                chart = IntradayChart(
                    df, 
                    symbol, 
                    timeframe=timeframe, 
                    hours_to_show=hours_to_show if hours_to_show else days_to_show * 24
                )
                chart.add_support_zones(support_zones)
                chart.add_resistance_zones(resistance_zones)
            
            else:  # simple
                chart = SimpleChart(
                    df, 
                    symbol, 
                    timeframe=timeframe,
                    days_to_show=days_to_show
                )
                chart.add_support_zones(support_zones)
                chart.add_resistance_zones(resistance_zones)
            
            # Vykreslení a uložení grafu
            chart_path = chart.render(filename)
            logger.info(f"Graf úspěšně vygenerován: {chart_path}")
            return chart_path
            
        except Exception as e:
            logger.error(f"Chyba při generování grafu: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
