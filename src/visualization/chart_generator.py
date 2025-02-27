#!/usr/bin/env python3

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for rendering charts
from datetime import datetime, timedelta
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import logging
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
import re

# Import konfiguračních modulů
from src.visualization.config.colors import get_color_scheme, get_candle_colors, get_zone_colors, get_scenario_colors
from src.visualization.config.timeframes import get_timeframe_config, get_min_candles_by_timeframe, get_days_by_timeframe
from src.visualization.components.zones import draw_support_zones, draw_resistance_zones
from src.visualization.components.scenarios import draw_scenarios
from src.visualization.utils.layout import adjust_y_limits, optimize_chart_area
from src.visualization.utils.formatting import format_price, get_price_precision

logger = logging.getLogger(__name__)

class ChartGenerator:
    """Class for generating candlestick charts with support and resistance zones and trend scenarios."""
    
    def extract_zones_from_text(self, analysis_text):
        """
        Extrahuje supportní a resistenční zóny přímo z textu analýzy.
        
        Args:
            analysis_text (str): Text analýzy
            
        Returns:
            tuple: (support_zones, resistance_zones)
        """
        support_zones = []
        resistance_zones = []
        
        # Hledání supportů
        support_pattern = r"[Ss]upport.*?(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)"
        support_matches = re.findall(support_pattern, analysis_text, re.IGNORECASE | re.DOTALL)
        
        for match in support_matches:
            try:
                s_min = float(match[0].replace(',', '.'))
                s_max = float(match[1].replace(',', '.'))
                support_zones.append((s_min, s_max))
            except (ValueError, IndexError):
                pass
                
        # Alternativní pattern pro supportní zóny
        alt_support_pattern = r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*\([Ss]upport"
        alt_support_matches = re.findall(alt_support_pattern, analysis_text)
        for match in alt_support_matches:
            try:
                s_min = float(match[0].replace(',', '.'))
                s_max = float(match[1].replace(',', '.'))
                support_zones.append((s_min, s_max))
            except (ValueError, IndexError):
                pass
        
        # Hledání resistencí
        resistance_pattern = r"[Rr]esist.*?(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)"
        resistance_matches = re.findall(resistance_pattern, analysis_text, re.IGNORECASE | re.DOTALL)
        
        for match in resistance_matches:
            try:
                r_min = float(match[0].replace(',', '.'))
                r_max = float(match[1].replace(',', '.'))
                resistance_zones.append((r_min, r_max))
            except (ValueError, IndexError):
                pass
                
        # Alternativní pattern pro resistenční zóny
        alt_resistance_pattern = r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*\([Rr]esist"
        alt_resistance_matches = re.findall(alt_resistance_pattern, analysis_text)
        for match in alt_resistance_matches:
            try:
                r_min = float(match[0].replace(',', '.'))
                r_max = float(match[1].replace(',', '.'))
                resistance_zones.append((r_min, r_max))
            except (ValueError, IndexError):
                pass
        
        # Deduplikace a seřazení
        support_zones = list(set(support_zones))
        resistance_zones = list(set(resistance_zones))
        
        return support_zones, resistance_zones

    def generate_chart(self, df, support_zones, resistance_zones, symbol, 
                       filename=None, days_to_show=2, hours_to_show=None, 
                       timeframe=None, scenarios=None, analysis_text=None):
        """
        Generates a candlestick chart with support and resistance zones and trend scenarios.
        """
        # Setup directories and filename
        logger.info(f"Generating chart for {symbol} ({timeframe})")
        charts_dir = "charts"
        os.makedirs(charts_dir, exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(charts_dir, f"{symbol}_{timestamp}.png")

        # Ensure we have correct OHLCV data
        df_copy = df.copy()
        
        # Make sure all column names are correct for mplfinance
        if 'open' in df_copy and 'Open' not in df_copy:
            df_copy['Open'] = df_copy['open']
        if 'high' in df_copy and 'High' not in df_copy:
            df_copy['High'] = df_copy['high']
        if 'low' in df_copy and 'Low' not in df_copy:
            df_copy['Low'] = df_copy['low']
        if 'close' in df_copy and 'Close' not in df_copy:
            df_copy['Close'] = df_copy['close']
        if 'volume' in df_copy and 'Volume' not in df_copy:
            df_copy['Volume'] = df_copy['volume']
        
        # Ensure datetime index
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            df_copy.index = pd.to_datetime(df_copy.index)
        
        # Trim data to the requested time range - POUŽIJ POSLEDNÍCH N SVÍČEK MÍSTO ČASOVÉHO ROZSAHU
        if hours_to_show:
            # Pro intraday použijme fixní počet svíček místo času
            # Oprava - používáme integer místo float
            num_candles = min(int(hours_to_show * 2), len(df_copy))  # Přibližný odhad - 2 svíčky na hodinu
            plot_data = df_copy.tail(num_candles).copy()
        else:
            # Pro denní grafy použijeme fixní počet svíček odpovídající přibližně počtu dnů
            candles_per_day = 24
            if timeframe == '1d':
                candles_per_day = 1
            elif timeframe == '4h':
                candles_per_day = 6
            elif timeframe == '1h':
                candles_per_day = 24
            elif timeframe == '30m':
                candles_per_day = 48
            
            # Oprava - používáme integer místo float
            num_candles = min(int(days_to_show * candles_per_day), len(df_copy))
            plot_data = df_copy.tail(num_candles).copy()
        
        # Nastavení parametrů pro mplfinance
        kwargs = dict(
            type='candle',
            volume=True,
            figsize=(12, 8),
            title=f"{symbol} - {timeframe} Timeframe",
            tight_layout=True,
            style='yahoo'
        )
        
        # Vynutit rozložení svíček po celé šířce grafu
        kwargs['show_nontrading'] = False  # Nezobrazovat nepřítomné časové body
        
        if len(plot_data) > 0:
            # Přidání support a resistance zón
            if support_zones or resistance_zones:
                # Extrahovat zóny z analysis_text pokud chybí
                if not support_zones and analysis_text:
                    s_zones, _ = self.extract_zones_from_text(analysis_text)
                    support_zones = s_zones
                if not resistance_zones and analysis_text:
                    _, r_zones = self.extract_zones_from_text(analysis_text)
                    resistance_zones = r_zones
                
                # Příprava apds pro zóny
                apds = []
                
                # Barvy pro zóny
                zone_colors = get_zone_colors()
                support_colors = zone_colors['support']
                resistance_colors = zone_colors['resistance']
                
                # Nastavení parametrů pro vykreslení zón
                kwargs['addplot'] = apds
            
            # Vykreslení grafu s mplfinance
            mpf.plot(
                plot_data,
                **kwargs,
                savefig=dict(fname=filename, dpi=150, bbox_inches='tight')
            )
        
        logger.info(f"Chart saved: {filename}")
        return filename
