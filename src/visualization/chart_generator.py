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
        
        # Hledání resistencí
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
        
        # Deduplikace a seřazení
        support_zones = list(set(support_zones))
        resistance_zones = list(set(resistance_zones))
        
        # Pokud jsme nenašli žádné zóny, zkusíme parsovat čísla ze sekce supportů/resistancí
        if not support_zones:
            support_section = re.search(r'[Ss]upportní zón[ay](.*?)(?:[Rr]esist|##|\Z)', 
                                      analysis_text, re.DOTALL | re.IGNORECASE)
            if support_section:
                # Hledáme čísla a vytváříme z nich rozsahy
                numbers = re.findall(r'(\d{4,6}(?:[.,]\d+)?)', support_section.group(1))
                numbers = [float(n.replace(',', '.')) for n in numbers]
                
                # Z každého čísla vytvoříme malou zónu (±0.5%)
                for num in numbers:
                    margin = num * 0.005
                    support_zones.append((num - margin, num + margin))
                
        if not resistance_zones:
            resist_section = re.search(r'[Rr]esisten[cč]ní zón[ay](.*?)(?:[Ss]upport|##|\Z)', 
                                      analysis_text, re.DOTALL | re.IGNORECASE)
            if resist_section:
                # Hledáme čísla a vytváříme z nich rozsahy
                numbers = re.findall(r'(\d{4,6}(?:[.,]\d+)?)', resist_section.group(1))
                numbers = [float(n.replace(',', '.')) for n in numbers]
                
                # Z každého čísla vytvoříme malou zónu (±0.5%)
                for num in numbers:
                    margin = num * 0.005
                    resistance_zones.append((num - margin, num + margin))
        
        return support_zones, resistance_zones

    def extract_scenarios_from_text(self, analysis_text, current_price):
        """
        Extrahuje scénáře pro vizualizaci z textu analýzy.
        
        Args:
            analysis_text (str): Text analýzy
            current_price (float): Aktuální cena
            
        Returns:
            list: Seznam scénářů ve formátu [('bullish', target_price), ('bearish', target_price), ...]
        """
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
        
        # Pokud jsme nenašli žádné scénáře, zkusíme prohledat celý text
        if not scenarios:
            # Hledání bullish cílů
            bullish_patterns = [
                r"[Bb]ullish.*?[Cc]íl.*?(\d{4,6}(?:[.,]\d+)?)",
                r"[Bb]ýčí.*?[Cc]íl.*?(\d{4,6}(?:[.,]\d+)?)",
                r"[Bb]ýčí scénář.*?(\d{4,6}(?:[.,]\d+)?)",
                r"[Dd]osáhnout.*?(\d{4,6}(?:[.,]\d+)?)"
            ]
            
            for pattern in bullish_patterns:
                bullish_matches = re.findall(pattern, analysis_text, re.IGNORECASE | re.DOTALL)
                for match in bullish_matches:
                    try:
                        price = float(match.replace(',', '.'))
                        if price > current_price * 1.005:  # Musí být aspoň 0.5% nad aktuální cenou
                            scenarios.append(('bullish', price))
                            break
                    except (ValueError, IndexError):
                        continue
                if len(scenarios) > 0 and scenarios[-1][0] == 'bullish':
                    break
            
            # Hledání bearish cílů
            bearish_patterns = [
                r"[Bb]earish.*?[Cc]íl.*?(\d{4,6}(?:[.,]\d+)?)",
                r"[Mm]edvědí.*?[Cc]íl.*?(\d{4,6}(?:[.,]\d+)?)",
                r"[Mm]edvědí scénář.*?(\d{4,6}(?:[.,]\d+)?)",
                r"[Pp]okles.*?(\d{4,6}(?:[.,]\d+)?)"
            ]
            
            for pattern in bearish_patterns:
                bearish_matches = re.findall(pattern, analysis_text, re.IGNORECASE | re.DOTALL)
                for match in bearish_matches:
                    try:
                        price = float(match.replace(',', '.'))
                        if price < current_price * 0.995:  # Musí být aspoň 0.5% pod aktuální cenou
                            scenarios.append(('bearish', price))
                            break
                    except (ValueError, IndexError):
                        continue
                if len(scenarios) > 0 and scenarios[-1][0] == 'bearish':
                    break
        
        return scenarios

    def generate_chart(self, df, support_zones, resistance_zones, symbol, 
                      filename=None, days_to_show=5, hours_to_show=None, 
                      timeframe=None, scenarios=None, analysis_text=None):
        """
        Generates a candlestick chart with support and resistance zones and trend scenarios.
        
        Args:
            df (pandas.DataFrame): DataFrame with OHLCV data
            support_zones (list): List of support zones as (min, max) tuples
            resistance_zones (list): List of resistance zones as (min, max) tuples
            symbol (str): Trading symbol
            filename (str, optional): Path to save the chart
            days_to_show (int, optional): Number of days to display (default: 5)
            hours_to_show (int, optional): Number of hours to display (overrides days_to_show)
            timeframe (str, optional): Timeframe of the data
            scenarios (list, optional): List of scenarios as (type, price) tuples
            analysis_text (str, optional): Analysis text for extracting zones
            
        Returns:
            str: Path to the generated chart file
        """
        # Setup directories and filename
        logger.info(f"Generating chart for {symbol} ({timeframe})")
        charts_dir = "charts"
        os.makedirs(charts_dir, exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(charts_dir, f"{symbol}_{timeframe}_{timestamp}.png")

        # Ensure we have correct OHLCV data
        df_copy = df.copy()
        
        # Make sure all column names are correct for mplfinance
        ohlcv_columns = {
            'open': 'Open', 'high': 'High', 'low': 'Low', 
            'close': 'Close', 'volume': 'Volume'
        }
        
        for old_col, new_col in ohlcv_columns.items():
            if old_col in df_copy.columns and new_col not in df_copy.columns:
                df_copy[new_col] = df_copy[old_col]
        
        # Ensure datetime index
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            df_copy.index = pd.to_datetime(df_copy.index)
        
        # Determine number of candles to show based on timeframe
        candles_to_show = None
        if timeframe == '1w':
            candles_to_show = max(10, min(52, len(df_copy)))
        elif timeframe == '1d':
            candles_to_show = max(20, min(60, len(df_copy)))
        elif timeframe == '4h':
            candles_to_show = max(30, min(6 * days_to_show, len(df_copy)))
        elif timeframe == '1h':
            candles_to_show = max(48, min(24 * days_to_show, len(df_copy)))
        elif timeframe == '30m':
            candles_to_show = max(60, min(48 * days_to_show, len(df_copy)))
        elif timeframe == '15m':
            candles_to_show = max(80, min(96 * days_to_show, len(df_copy)))
        elif timeframe == '5m':
            candles_to_show = max(100, min(288 * days_to_show, len(df_copy)))
        else:
            # Default - use at least 60 candles but not more than available
            candles_to_show = max(60, min(len(df_copy), 150))
            
        if hours_to_show:
            # Override with hours if provided
            if timeframe == '1h':
                candles_to_show = min(hours_to_show, len(df_copy))
            elif timeframe == '30m':
                candles_to_show = min(hours_to_show * 2, len(df_copy))
            elif timeframe == '15m':
                candles_to_show = min(hours_to_show * 4, len(df_copy))
            elif timeframe == '5m':
                candles_to_show = min(hours_to_show * 12, len(df_copy))
            elif timeframe == '1m':
                candles_to_show = min(hours_to_show * 60, len(df_copy))
        
        # Select data to plot
        plot_data = df_copy.tail(candles_to_show).copy()
        
        # Extract zones from analysis text if none were provided
        if (not support_zones or not resistance_zones) and analysis_text:
            extracted_support, extracted_resistance = self.extract_zones_from_text(analysis_text)
            
            if not support_zones:
                support_zones = extracted_support
            
            if not resistance_zones:
                resistance_zones = extracted_resistance
        
        # Extract scenarios from analysis text if none were provided
        if not scenarios and analysis_text:
            current_price = plot_data['Close'].iloc[-1]
            scenarios = self.extract_scenarios_from_text(analysis_text, current_price)
        
        # Create figure and axes
        fig = plt.figure(figsize=(12, 8))
        gs = fig.add_gridspec(2, 1, height_ratios=[4, 1], hspace=0.05)
        ax1 = fig.add_subplot(gs[0, 0])  # Price chart
        ax2 = fig.add_subplot(gs[1, 0], sharex=ax1)  # Volume
        
        # Set title
        title = f"{symbol} - {timeframe} Timeframe"
        if timeframe in ['1d', '1w']:
            title += " (Long-term Analysis)"
        elif timeframe in ['4h', '1h']:
            title += " (Medium-term Analysis)"
        else:
            title += " (Short-term Analysis)"
            
        ax1.set_title(title, fontsize=14, fontweight='bold')
        
        # Define colors for candles
        mc = mpf.make_marketcolors(
            up='#00a061',
            down='#eb4d5c',
            edge={'up': '#00a061', 'down': '#eb4d5c'},
            wick={'up': '#00a061', 'down': '#eb4d5c'},
            volume={'up': '#a3e2c5', 'down': '#f1c3c8'}
        )
        
        # Define style
        style = mpf.make_mpf_style(
            base_mpf_style='yahoo',
            marketcolors=mc,
            gridstyle='-',
            gridcolor='#e6e6e6',
            gridaxis='both',
            facecolor='white'
        )
        
        # Draw candles
        mpf.plot(
            plot_data, 
            ax=ax1, 
            volume=ax2, 
            type='candle', 
            style=style, 
            show_nontrading=False
        )
        
        # Draw support zones
        legend_elements = []
        if support_zones:
            zone_colors = get_zone_colors()
            support_colors = zone_colors['support']
            
            for i, (s_min, s_max) in enumerate(support_zones):
                color_idx = min(i, len(support_colors) - 1)
                color = support_colors[color_idx]
                
                # Add filled area
                ax1.axhspan(s_min, s_max, facecolor=color, alpha=0.3)
                
                # Add horizontal lines at zone boundaries
                ax1.axhline(y=s_min, color=color, linestyle='-', linewidth=1.0, alpha=0.7)
                ax1.axhline(y=s_max, color=color, linestyle='-', linewidth=1.0, alpha=0.7)
                
                # Add text label
                mid_point = (s_min + s_max) / 2
                ax1.text(
                    plot_data.index[0], 
                    mid_point, 
                    f"S{i+1}: {mid_point:.0f}", 
                    color='white', 
                    fontweight='bold', 
                    fontsize=9,
                    bbox=dict(
                        facecolor=color, 
                        alpha=0.9, 
                        edgecolor=color, 
                        boxstyle='round,pad=0.3'
                    )
                )
            
            # Add to legend
            legend_elements.append(Line2D([0], [0], color=support_colors[0], lw=4, label='Support Zone'))
        
        # Draw resistance zones
        if resistance_zones:
            zone_colors = get_zone_colors()
            resistance_colors = zone_colors['resistance']
            
            for i, (r_min, r_max) in enumerate(resistance_zones):
                color_idx = min(i, len(resistance_colors) - 1)
                color = resistance_colors[color_idx]
                
                # Add filled area
                ax1.axhspan(r_min, r_max, facecolor=color, alpha=0.3)
                
                # Add horizontal lines at zone boundaries
                ax1.axhline(y=r_min, color=color, linestyle='-', linewidth=1.0, alpha=0.7)
                ax1.axhline(y=r_max, color=color, linestyle='-', linewidth=1.0, alpha=0.7)
                
                # Add text label
                mid_point = (r_min + r_max) / 2
                ax1.text(
                    plot_data.index[0], 
                    mid_point, 
                    f"R{i+1}: {mid_point:.0f}", 
                    color='white', 
                    fontweight='bold', 
                    fontsize=9,
                    bbox=dict(
                        facecolor=color, 
                        alpha=0.9, 
                        edgecolor=color, 
                        boxstyle='round,pad=0.3'
                    )
                )
            
            # Add to legend
            legend_elements.append(Line2D([0], [0], color=resistance_colors[0], lw=4, label='Resistance Zone'))
        
        # Draw scenarios
        if scenarios:
            current_price = plot_data['Close'].iloc[-1]
            
            # Define projection days based on timeframe
            if timeframe == '1w':
                projection_days = 60  # 2 months
            elif timeframe == '1d':
                projection_days = 30  # 1 month
            elif timeframe == '4h':
                projection_days = 14  # 2 weeks
            elif timeframe == '1h':
                projection_days = 7   # 1 week
            else:
                projection_days = 3   # 3 days for other timeframes
            
            # Create future dates for projection
            last_date = plot_data.index[-1]
            future_dates = [last_date + timedelta(days=i) for i in range(1, projection_days + 1)]
            future_x_dates = mdates.date2num(future_dates)
            
            # Number of points for projection
            num_points = len(future_dates)
            
            # Draw each scenario
            for scenario_type, target_price in scenarios:
                bullish_added = False
                bearish_added = False
                
                if scenario_type == 'bullish' and target_price > current_price:
                    # Generate bounces to target (simplified for now)
                    y_values = np.linspace(current_price, target_price, num_points)
                    
                    # Add some randomness for more realistic path
                    noise = np.random.normal(0, (target_price - current_price) * 0.05, num_points)
                    y_values = y_values + noise
                    
                    # Ensure target price remains the target
                    y_values[-1] = target_price
                    
                    # Convert dates to numbers for plotting
                    x_dates = mdates.date2num(plot_data.index[-1:].to_pydatetime())
                    x_values = np.append(x_dates, future_x_dates)
                    y_values = np.append([current_price], y_values)
                    
                    # Plot bullish scenario
                    ax1.plot(x_values, y_values, '-', color='green', linewidth=2.5)
                    
                    # Add target label
                    ax1.text(
                        future_dates[-1], 
                        target_price, 
                        f"{target_price:.0f}", 
                        color='white', 
                        fontweight='bold', 
                        fontsize=10,
                        bbox=dict(facecolor='green', alpha=0.9, edgecolor='green')
                    )
                    
                    bullish_added = True
                
                elif scenario_type == 'bearish' and target_price < current_price:
                    # Generate bounces to target (simplified for now)
                    y_values = np.linspace(current_price, target_price, num_points)
                    
                    # Add some randomness for more realistic path
                    noise = np.random.normal(0, (current_price - target_price) * 0.05, num_points)
                    y_values = y_values + noise
                    
                    # Ensure target price remains the target
                    y_values[-1] = target_price
                    
                    # Convert dates to numbers for plotting
                    x_dates = mdates.date2num(plot_data.index[-1:].to_pydatetime())
                    x_values = np.append(x_dates, future_x_dates)
                    y_values = np.append([current_price], y_values)
                    
                    # Plot bearish scenario
                    ax1.plot(x_values, y_values, '-', color='red', linewidth=2.5)
                    
                    # Add target label
                    ax1.text(
                        future_dates[-1], 
                        target_price, 
                        f"{target_price:.0f}", 
                        color='white', 
                        fontweight='bold', 
                        fontsize=10,
                        bbox=dict(facecolor='red', alpha=0.9, edgecolor='red')
                    )
                    
                    bearish_added = True
                
                # Add to legend
                if bullish_added:
                    legend_elements.append(Line2D([0], [0], color='green', lw=2.5, label='Bullish Scenario'))
                if bearish_added:
                    legend_elements.append(Line2D([0], [0], color='red', lw=2.5, label='Bearish Scenario'))
        
        # Add legend if there are elements
        if legend_elements:
            ax1.legend(
                handles=legend_elements, 
                loc='upper left', 
                fontsize=8, 
                framealpha=0.8, 
                ncol=len(legend_elements)
            )
        
        # Format date axis
        if timeframe in ['1w', '1d']:
            date_format = '%Y-%m-%d'
        else:
            date_format = '%m-%d %H:%M'
        
        # Set major formatter
        ax1.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
        
        # Add generation timestamp
        plt.figtext(
            0.01, 0.01,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            fontsize=7,
            bbox=dict(facecolor='white', alpha=0.8)
        )
        
        # Save the chart
        plt.tight_layout(pad=1.0)
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"Chart saved: {filename}")
        return filename
