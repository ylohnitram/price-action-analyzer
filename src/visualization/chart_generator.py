#!/usr/bin/env python3

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
        
        # Vyhledávání support zón
        support_pattern = r"[Ss]upport.*?(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)"
        support_matches = re.findall(support_pattern, analysis_text, re.IGNORECASE | re.DOTALL)
        
        for match in support_matches:
            try:
                s_min = float(match[0].replace(',', '.'))
                s_max = float(match[1].replace(',', '.'))
                support_zones.append((s_min, s_max))
            except (ValueError, IndexError):
                pass
                
        # Alternativní pattern pro supportní zóny
        alt_support_pattern = r"(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*\([Ss]upport"
        alt_support_matches = re.findall(alt_support_pattern, analysis_text)
        for match in alt_support_matches:
            try:
                s_min = float(match[0].replace(',', '.'))
                s_max = float(match[1].replace(',', '.'))
                support_zones.append((s_min, s_max))
            except (ValueError, IndexError):
                pass
        
        # Vyhledávání resistance zón
        resistance_pattern = r"[Rr]esist.*?(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)"
        resistance_matches = re.findall(resistance_pattern, analysis_text, re.IGNORECASE | re.DOTALL)
        
        for match in resistance_matches:
            try:
                r_min = float(match[0].replace(',', '.'))
                r_max = float(match[1].replace(',', '.'))
                resistance_zones.append((r_min, r_max))
            except (ValueError, IndexError):
                pass
                
        # Alternativní pattern pro resistenční zóny
        alt_resistance_pattern = r"(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*\([Rr]esist"
        alt_resistance_matches = re.findall(alt_resistance_pattern, analysis_text)
        for match in alt_resistance_matches:
            try:
                r_min = float(match[0].replace(',', '.'))
                r_max = float(match[1].replace(',', '.'))
                resistance_zones.append((r_min, r_max))
            except (ValueError, IndexError):
                pass
        
        # Deduplikace a další zpracování pokud potřeba...
        support_zones = list(set(support_zones))
        resistance_zones = list(set(resistance_zones))
        
        return support_zones, resistance_zones
    
    def extract_scenarios_from_text(self, analysis_text, current_price):
        """Extrahuje scénáře pro vizualizaci z textu analýzy."""
        scenarios = []
        
        # Hledat sekci "MOŽNÉ SCÉNÁŘE DALŠÍHO VÝVOJE" nebo podobnou
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
        
        # Další hledání scénářů v celém textu pokud nebyly nalezeny...
        
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
