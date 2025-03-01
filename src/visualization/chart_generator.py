#!/usr/bin/env python3

import matplotlib
# Nastavení neinteraktivního backend před importem pyplot
matplotlib.use('Agg')

import logging
import re
from datetime import datetime

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
        """Extrahuje zóny supportů a resistencí z textu analýzy."""
        support_zones = []
        resistance_zones = []
        
        # Hledání supportních zón v sekci supportních zón
        support_section_pattern = r"Hlavní supportní zón[^:]*:([^#]+)"
        support_section = re.search(support_section_pattern, analysis_text, re.IGNORECASE | re.DOTALL)
        
        if support_section:
            # Získáme text sekce supportů
            section_text = support_section.group(1)
            logger.info(f"Nalezena sekce supportních zón: {section_text}")
            
            # Hledání všech odrážek v sekci
            bullet_points = re.findall(r"\s*-\s*([^\n]+)", section_text)
            for point in bullet_points:
                # Hledání číselného rozsahu v každé odrážce
                range_match = re.search(r"(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)", point)
                if range_match:
                    try:
                        s_min = float(range_match.group(1).replace(',', '.'))
                        s_max = float(range_match.group(2).replace(',', '.'))
                        # Ověření, zda hodnoty mají smysl pro cenu BTC
                        if s_min > 1000 and s_max > 1000 and s_min < s_max:
                            support_zones.append((s_min, s_max))
                            logger.info(f"Extrahována supportní zóna: {s_min}-{s_max}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Chyba při zpracování supportní zóny '{point}': {str(e)}")
                        continue
        
        # Hledání rezistenčních zón v sekci rezistenčních zón
        resistance_section_pattern = r"Hlavní resistenční zón[^:]*:([^#]+)"
        resistance_section = re.search(resistance_section_pattern, analysis_text, re.IGNORECASE | re.DOTALL)
        
        if resistance_section:
            # Získáme text sekce rezistencí
            section_text = resistance_section.group(1)
            logger.info(f"Nalezena sekce rezistenčních zón: {section_text}")
            
            # Hledání všech odrážek v sekci
            bullet_points = re.findall(r"\s*-\s*([^\n]+)", section_text)
            for point in bullet_points:
                # Hledání číselného rozsahu v každé odrážce
                range_match = re.search(r"(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)", point)
                if range_match:
                    try:
                        r_min = float(range_match.group(1).replace(',', '.'))
                        r_max = float(range_match.group(2).replace(',', '.'))
                        # Ověření, zda hodnoty mají smysl pro cenu BTC
                        if r_min > 1000 and r_max > 1000 and r_min < r_max:
                            resistance_zones.append((r_min, r_max))
                            logger.info(f"Extrahována rezistenční zóna: {r_min}-{r_max}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Chyba při zpracování rezistenční zóny '{point}': {str(e)}")
                        continue
        
        # Pokud nenajdeme zóny v sekcích, zkusíme hledat v celém textu
        if not support_zones:
            # Obecnější vzory pro hledání supportních zón v celém textu
            support_patterns = [
                r"[Ss]upport.*?(\d{4,6}(?:[.,]\d+)?)\s*-\s*(\d{4,6}(?:[.,]\d+)?)",
                r"[Pp]odpora.*?(\d{4,6}(?:[.,]\d+)?)\s*-\s*(\d{4,6}(?:[.,]\d+)?)"
            ]
            
            for pattern in support_patterns:
                support_matches = re.findall(pattern, analysis_text, re.IGNORECASE | re.DOTALL)
                for match in support_matches:
                    try:
                        s_min = float(match[0].replace(',', '.'))
                        s_max = float(match[1].replace(',', '.'))
                        # Ověření, zda hodnoty mají smysl pro cenu BTC
                        if s_min > 1000 and s_max > 1000 and s_min < s_max:
                            support_zones.append((s_min, s_max))
                            logger.info(f"Extrahována supportní zóna z textu: {s_min}-{s_max}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Chyba při zpracování supportní zóny z textu: {str(e)}")
                        continue
        
        if not resistance_zones:
            # Obecnější vzory pro hledání rezistenčních zón v celém textu
            resistance_patterns = [
                r"[Rr]esisten[cč].*?(\d{4,6}(?:[.,]\d+)?)\s*-\s*(\d{4,6}(?:[.,]\d+)?)",
                r"[Rr]ezisten[cč].*?(\d{4,6}(?:[.,]\d+)?)\s*-\s*(\d{4,6}(?:[.,]\d+)?)",
                r"[Oo]dpor.*?(\d{4,6}(?:[.,]\d+)?)\s*-\s*(\d{4,6}(?:[.,]\d+)?)"
            ]
            
            for pattern in resistance_patterns:
                resistance_matches = re.findall(pattern, analysis_text, re.IGNORECASE | re.DOTALL)
                for match in resistance_matches:
                    try:
                        r_min = float(match[0].replace(',', '.'))
                        r_max = float(match[1].replace(',', '.'))
                        # Ověření, zda hodnoty mají smysl pro cenu BTC
                        if r_min > 1000 and r_max > 1000 and r_min < r_max:
                            resistance_zones.append((r_min, r_max))
                            logger.info(f"Extrahována rezistenční zóna z textu: {r_min}-{r_max}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Chyba při zpracování rezistenční zóny z textu: {str(e)}")
                        continue
        
        # Můžeme zkusit hledat i v sekci pro střednědobý kontext
        context_section = re.search(r"STŘEDNĚDOBÝ KONTEXT.*?:([^#]+)", analysis_text, re.IGNORECASE | re.DOTALL)
        if context_section:
            section_text = context_section.group(1)
            
            # Hledání support/resistance v sekci střednědobého kontextu
            support_in_context = re.findall(r"[Ss]upport:?\s*(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)", section_text)
            for match in support_in_context:
                try:
                    s_min = float(match[0].replace(',', '.'))
                    s_max = float(match[1].replace(',', '.'))
                    # Ověření, zda hodnoty mají smysl pro cenu BTC
                    if s_min > 1000 and s_max > 1000 and s_min < s_max:
                        support_zones.append((s_min, s_max))
                        logger.info(f"Extrahována supportní zóna z kontextu: {s_min}-{s_max}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Chyba při zpracování supportní zóny z kontextu: {str(e)}")
                    continue
            
            resistance_in_context = re.findall(r"[Rr]esistance:?\s*(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)", section_text)
            for match in resistance_in_context:
                try:
                    r_min = float(match[0].replace(',', '.'))
                    r_max = float(match[1].replace(',', '.'))
                    # Ověření, zda hodnoty mají smysl pro cenu BTC
                    if r_min > 1000 and r_max > 1000 and r_min < r_max:
                        resistance_zones.append((r_min, r_max))
                        logger.info(f"Extrahována rezistenční zóna z kontextu: {r_min}-{r_max}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Chyba při zpracování rezistenční zóny z kontextu: {str(e)}")
                    continue
        
        # Deduplikace a setřídění zón
        support_zones = list(set(support_zones))
        resistance_zones = list(set(resistance_zones))
        
        # Seřazení zón podle ceny
        support_zones.sort(key=lambda x: x[0])
        resistance_zones.sort(key=lambda x: x[0])
        
        # Omezení počtu zón pro lepší přehlednost (max 8)
        if len(support_zones) > 8:
            support_zones = support_zones[:8]
        if len(resistance_zones) > 8:
            resistance_zones = resistance_zones[:8]
        
        # Odfiltrování nevyhovujících zón (nereálných hodnot pro BTC)
        support_zones = [(min_p, max_p) for min_p, max_p in support_zones if min_p > 1000 and max_p < 200000]
        resistance_zones = [(min_p, max_p) for min_p, max_p in resistance_zones if min_p > 1000 and max_p < 200000]
        
        logger.info(f"Finální supportní zóny: {support_zones}")
        logger.info(f"Finální rezistenční zóny: {resistance_zones}")
            
        return support_zones, resistance_zones
    
    def extract_scenarios_from_text(self, analysis_text, current_price):
        """Extrahuje scénáře pro vizualizaci z textu analýzy."""
        scenarios = []
        
        # Hledat sekci "MOŽNÉ SCÉNÁŘE DALŠÍHO VÝVOJE"
        scenario_section = re.search(r'(MOŽNÉ SCÉNÁŘE|SCÉNÁŘE|SCENÁŘE|VÝVOJE)(.*?)(##|\Z)', 
                                    analysis_text, re.DOTALL | re.IGNORECASE)
        
        if scenario_section:
            scenario_text = scenario_section.group(2)
            logger.info(f"Nalezena sekce scénářů: {scenario_text}")
            
            # Hledání bullish scénáře a ceny
            bullish_section = re.search(r'- [Bb]ullish.*?(\d{4,6}(?:[.,]\d+)?)', scenario_text, re.DOTALL)
            if bullish_section:
                try:
                    bullish_target = float(bullish_section.group(1).replace(',', '.'))
                    # Ověření, zda hodnoty mají smysl pro cenu BTC
                    if bullish_target > 1000 and bullish_target > current_price:
                        scenarios.append(('bullish', bullish_target))
                        logger.info(f"Extrahován bullish scénář s cílem: {bullish_target}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Chyba při zpracování bullish scénáře: {str(e)}")
            
            # Hledání bearish scénáře a ceny
            bearish_section = re.search(r'- [Bb]earish.*?(\d{4,6}(?:[.,]\d+)?)', scenario_text, re.DOTALL)
            if bearish_section:
                try:
                    bearish_target = float(bearish_section.group(1).replace(',', '.'))
                    # Ověření, zda hodnoty mají smysl pro cenu BTC
                    if bearish_target > 1000 and bearish_target < current_price:
                        scenarios.append(('bearish', bearish_target))
                        logger.info(f"Extrahován bearish scénář s cílem: {bearish_target}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Chyba při zpracování bearish scénáře: {str(e)}")
            
            # Hledání neutrálního scénáře (pokud má explicitní cenový rozsah)
            neutral_section = re.search(r'- [Nn]eutrální.*?(\d{4,6}(?:[.,]\d+)?).*?(\d{4,6}(?:[.,]\d+)?)', scenario_text, re.DOTALL)
            if neutral_section:
                try:
                    lower_bound = float(neutral_section.group(1).replace(',', '.'))
                    upper_bound = float(neutral_section.group(2).replace(',', '.'))
                    
                    # Ověření, zda hodnoty mají smysl pro cenu BTC
                    if lower_bound > 1000 and upper_bound > 1000 and lower_bound < upper_bound:
                        scenarios.append(('neutral', (lower_bound, upper_bound)))
                        logger.info(f"Extrahován neutrální scénář s rozsahem: {lower_bound}-{upper_bound}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Chyba při zpracování neutrálního scénáře: {str(e)}")
            
            # Pokud stále nemáme neutrální scénář, zkusíme jiný vzor
            if not any(s[0] == 'neutral' for s in scenarios):
                # Hledáme "oscilovat mezi X a Y"
                oscillation_pattern = re.search(r'oscilovat\s+mezi\s+(\d{4,6}(?:[.,]\d+)?)\s+a\s+(\d{4,6}(?:[.,]\d+)?)', scenario_text, re.IGNORECASE)
                if oscillation_pattern:
                    try:
                        lower_bound = float(oscillation_pattern.group(1).replace(',', '.'))
                        upper_bound = float(oscillation_pattern.group(2).replace(',', '.'))
                        
                        # Ověření, zda hodnoty mají smysl pro cenu BTC
                        if lower_bound > 1000 and upper_bound > 1000 and lower_bound < upper_bound:
                            scenarios.append(('neutral', (lower_bound, upper_bound)))
                            logger.info(f"Extrahován neutrální scénář s oscilací: {lower_bound}-{upper_bound}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Chyba při zpracování neutrálního scénáře (oscilace): {str(e)}")
        
        # Kontrola, že máme scénáře - pokud ne, zkusíme méně striktní přístup
        if not scenarios:
            logger.warning("Standardní extrakce scénářů selhala, zkouším alternativní přístup")
            
            # Hledání všech čísel v textu, které by mohly být cenovými cíli
            price_targets = re.findall(r'(\d{4,6}(?:[.,]\d+)?)', analysis_text)
            price_targets = [float(p.replace(',', '.')) for p in price_targets if float(p.replace(',', '.')) > 1000]
            
            # Najdeme hodnoty nad a pod aktuální cenou, které jsou od ní relativně vzdálené
            higher_targets = [p for p in price_targets if p > current_price * 1.05]  # 5% nad aktuální cenou
            lower_targets = [p for p in price_targets if p < current_price * 0.95]   # 5% pod aktuální cenou
            
            # Pokud najdeme cíle, přidáme je jako scénáře
            if higher_targets:
                bullish_target = min(higher_targets)  # Nejbližší cíl nad aktuální cenou
                scenarios.append(('bullish', bullish_target))
                logger.info(f"Extrahován bullish scénář pomocí alternativní metody: {bullish_target}")
            
            if lower_targets:
                bearish_target = max(lower_targets)  # Nejbližší cíl pod aktuální cenou
                scenarios.append(('bearish', bearish_target))
                logger.info(f"Extrahován bearish scénář pomocí alternativní metody: {bearish_target}")
        
        logger.info(f"Finální extrahované scénáře: {scenarios}")
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
        logger.info(f"Generating chart for {symbol} ({timeframe}), analysis type: {analysis_type}")
        
        # Nastavení výchozí cesty pro uložení grafu
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"charts/{symbol}_{timeframe}_{timestamp}.png"
        
        # Extrakce zón z textu, pokud nebyly předány
        if (not support_zones or not resistance_zones) and analysis_text:
            extracted_support, extracted_resistance = self.extract_zones_from_text(analysis_text)
            
            if not support_zones:
                support_zones = extracted_support
            
            if not resistance_zones:
                resistance_zones = extracted_resistance
        
        # Extrakce scénářů z textu, pokud nebyly předány a jedná se o swing analýzu
        if analysis_type == "swing" and not scenarios and analysis_text:
            current_price = df['close'].iloc[-1] if len(df) > 0 else None
            if current_price:
                scenarios = self.extract_scenarios_from_text(analysis_text, current_price)
        
        # Výběr správného typu grafu podle typu analýzy
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
        return chart.render(filename)
