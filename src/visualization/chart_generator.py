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
        
        # Vylepšený pattern pro podpory a rezistence, který zachytí různé formáty
        patterns = [
            # Formát "78258.5-80000"
            r"(?:support|Support).*?(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)",
            r"(?:resistance|Resistance|rezistence|Rezistence).*?(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)",
            
            # Speciální formát pro odrážky v Markdown
            r"- .*?(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)(?=\n)",
            
            # Formát pro případ, kdy je zóna uvedena ve větě
            r"[Ss]upport\D+(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)",
            r"[Rr]esistance\D+(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)",
            
            # Formát pro hledání zón v sekci supportních nebo rezistenčních zón
            r"Hlavní supportní zón[^:]*:[^\n]*\n(?:\s*-\s*(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)[^\n]*\n)+",
            r"Hlavní resistenční zón[^:]*:[^\n]*\n(?:\s*-\s*(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)[^\n]*\n)+"
        ]
        
        # Zvlášť provedeme hledání pro supporty a rezistence
        # Hledat supportní zóny v celém textu
        support_pattern = r"[Ss]upport.*?(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)"
        support_matches = re.findall(support_pattern, analysis_text, re.IGNORECASE | re.DOTALL)
        
        # Hledání v sekci supportních zón
        support_section_pattern = r"Hlavní supportní zón[^:]*:([^#]+)"
        support_section = re.search(support_section_pattern, analysis_text, re.IGNORECASE | re.DOTALL)
        if support_section:
            section_text = support_section.group(1)
            # Hledání všech odrážek v sekci
            bullet_points = re.findall(r"\s*-\s*([^\n]+)", section_text)
            for point in bullet_points:
                # Hledání číselného rozsahu v každé odrážce
                range_match = re.search(r"(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)", point)
                if range_match:
                    try:
                        s_min = float(range_match.group(1).replace(',', '.'))
                        s_max = float(range_match.group(2).replace(',', '.'))
                        support_zones.append((s_min, s_max))
                    except (ValueError, IndexError):
                        pass
        
        # Přidání nalezených zón do seznamu supportů
        for match in support_matches:
            try:
                s_min = float(match[0].replace(',', '.'))
                s_max = float(match[1].replace(',', '.'))
                support_zones.append((s_min, s_max))
            except (ValueError, IndexError):
                pass
                
        # Hledat resistenční zóny v celém textu
        resistance_pattern = r"[Rr]esisten[cč].*?(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)"
        resistance_matches = re.findall(resistance_pattern, analysis_text, re.IGNORECASE | re.DOTALL)
        
        # Hledání v sekci resistenčních zón
        resistance_section_pattern = r"Hlavní resistenční zón[^:]*:([^#]+)"
        resistance_section = re.search(resistance_section_pattern, analysis_text, re.IGNORECASE | re.DOTALL)
        if resistance_section:
            section_text = resistance_section.group(1)
            # Hledání všech odrážek v sekci
            bullet_points = re.findall(r"\s*-\s*([^\n]+)", section_text)
            for point in bullet_points:
                # Hledání číselného rozsahu v každé odrážce
                range_match = re.search(r"(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)", point)
                if range_match:
                    try:
                        r_min = float(range_match.group(1).replace(',', '.'))
                        r_max = float(range_match.group(2).replace(',', '.'))
                        resistance_zones.append((r_min, r_max))
                    except (ValueError, IndexError):
                        pass
        
        # Přidání nalezených zón do seznamu resistencí
        for match in resistance_matches:
            try:
                r_min = float(match[0].replace(',', '.'))
                r_max = float(match[1].replace(',', '.'))
                resistance_zones.append((r_min, r_max))
            except (ValueError, IndexError):
                pass
        
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
            
        return support_zones, resistance_zones
    
    def extract_scenarios_from_text(self, analysis_text, current_price):
        """Extrahuje scénáře pro vizualizaci z textu analýzy."""
        scenarios = []
        
        # Hledat sekci "MOŽNÉ SCÉNÁŘE DALŠÍHO VÝVOJE"
        scenario_section = re.search(r'(MOŽNÉ SCÉNÁŘE|SCÉNÁŘE|SCENÁŘE|VÝVOJE)(.*?)(##|\Z)', 
                                    analysis_text, re.DOTALL | re.IGNORECASE)
        
        if scenario_section:
            scenario_text = scenario_section.group(2)
            
            # Hledání bullish scénáře a ceny
            bullish_section = re.search(r'[Bb]ullish.*?(\d{4,6}(?:[.,]\d+)?)', scenario_text, re.DOTALL)
            if bullish_section:
                try:
                    bullish_target = float(bullish_section.group(1).replace(',', '.'))
                    if bullish_target > current_price * 1.005:  # Musí být aspoň 0.5% nad aktuální cenou
                        scenarios.append(('bullish', bullish_target))
                except (ValueError, IndexError):
                    pass
            
            # Hledání bearish scénáře a ceny
            bearish_section = re.search(r'[Bb]earish.*?(\d{4,6}(?:[.,]\d+)?)', scenario_text, re.DOTALL)
            if bearish_section:
                try:
                    bearish_target = float(bearish_section.group(1).replace(',', '.'))
                    if bearish_target < current_price * 0.995:  # Musí být aspoň 0.5% pod aktuální cenou
                        scenarios.append(('bearish', bearish_target))
                except (ValueError, IndexError):
                    pass
            
            # Hledání neutrálního scénáře (pokud má explicitní cenový rozsah)
            neutral_section = re.search(r'[Nn]eutrální.*?(\d{4,6}(?:[.,]\d+)?)[^\d]*(\d{4,6}(?:[.,]\d+)?)', scenario_text, re.DOTALL)
            if neutral_section:
                try:
                    lower_bound = float(neutral_section.group(1).replace(',', '.'))
                    upper_bound = float(neutral_section.group(2).replace(',', '.'))
                    
                    # Pro neutrální scénář vytvoříme pouze hranice pokud dávají smysl
                    if lower_bound < upper_bound:
                        scenarios.append(('neutral', (lower_bound, upper_bound)))
                except (ValueError, IndexError):
                    pass
        
        # Logování nalezených scénářů pro ladění
        logger.info(f"Nalezené scénáře: {scenarios}")
        
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
