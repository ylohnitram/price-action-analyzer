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

        # Zobrazení všech sloupců v dataframe pro debugging
        logger.info(f"Sloupce v dataframe: {df.columns.tolist()}")
        logger.info(f"Celkový počet svíček: {len(df)}")
        
        # Ensure we have correct OHLCV data
        df_copy = df.copy()
        
        # Make sure all column names are correct for mplfinance - dvojitá kontrola pro jistotu
        ohlcv_columns = {
            'open': 'Open', 'high': 'High', 'low': 'Low', 
            'close': 'Close', 'volume': 'Volume'
        }
        
        for old_col, new_col in ohlcv_columns.items():
            if old_col in df_copy.columns and new_col not in df_copy.columns:
                df_copy[new_col] = df_copy[old_col]
        
        # Důležitá kontrola - zajistí, že máme všechny potřebné sloupce
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in df_copy.columns:
                logger.error(f"Chybí sloupec {col} v dataframe")
                # Pokud chybí, zkusíme ho vytvořit ze zbývajících dat (nouzové řešení)
                if col == 'Open' and 'Close' in df_copy.columns:
                    df_copy['Open'] = df_copy['Close']
                elif col == 'High' and 'Close' in df_copy.columns:
                    df_copy['High'] = df_copy['Close']
                elif col == 'Low' and 'Close' in df_copy.columns:
                    df_copy['Low'] = df_copy['Close']
                elif col == 'Close' and 'Open' in df_copy.columns:
                    df_copy['Close'] = df_copy['Open']
                elif col == 'Volume':
                    df_copy['Volume'] = 0
        
        # Ensure datetime index
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            df_copy.index = pd.to_datetime(df_copy.index)
        
        # Kontrola a vyčištění dat - velmi důležité!
        # Odstraníme duplicitní indexy, které by mohly způsobit problémy
        if df_copy.index.duplicated().any():
            logger.warning(f"Nalezeny duplicitní indexy! Odstraňuji...")
            df_copy = df_copy[~df_copy.index.duplicated(keep='first')]
        
        # Seřadíme dataframe podle indexu pro jistotu
        df_copy = df_copy.sort_index()
        
        # Omezení počtu svíček, aby byly dobře viditelné
        max_candles = 50  # Sníženo pro lepší výkon - 96 je příliš mnoho
        
        # Determine number of candles to show based on timeframe
        if hours_to_show:
            # Pro intraday grafy s hodinami použijeme přímé omezení počtu svíček
            if timeframe == '30m':
                candles_to_show = min(hours_to_show * 2, max_candles)
            elif timeframe == '5m':
                candles_to_show = min(hours_to_show * 12, max_candles)
            else:
                candles_to_show = max_candles
                
            logger.info(f"Omezení na {candles_to_show} svíček pro intraday")
        else:
            # Pro denní grafy použijeme omezení podle počtu dní
            if timeframe == '1d':
                candles_to_show = min(days_to_show, max_candles)
            else:
                candles_to_show = max_candles
        
        # Select data to plot - vybereme jen poslední omezený počet svíček
        plot_data = df_copy.tail(candles_to_show).copy()
        
        # Kontrola vybraných dat
        logger.info(f"Vybrán časový úsek od {plot_data.index[0]} do {plot_data.index[-1]} s {len(plot_data)} svíčkami")
        
        # Výpis prvních a posledních řádků pro kontrolu
        if len(plot_data) > 0:
            logger.info(f"První řádek: {plot_data.iloc[0]['Open']}, {plot_data.iloc[0]['High']}, {plot_data.iloc[0]['Low']}, {plot_data.iloc[0]['Close']}")
            logger.info(f"Poslední řádek: {plot_data.iloc[-1]['Open']}, {plot_data.iloc[-1]['High']}, {plot_data.iloc[-1]['Low']}, {plot_data.iloc[-1]['Close']}")
        
        # Extract zones from analysis text if none were provided
        if (not support_zones or not resistance_zones) and analysis_text:
            extracted_support, extracted_resistance = self.extract_zones_from_text(analysis_text)
            
            if not support_zones:
                support_zones = extracted_support
            
            if not resistance_zones:
                resistance_zones = extracted_resistance
        
        # Extract scenarios from analysis text if none were provided
        if not scenarios and analysis_text:
            current_price = plot_data['Close'].iloc[-1] if len(plot_data) > 0 else None
            if current_price:
                scenarios = self.extract_scenarios_from_text(analysis_text, current_price)
        
        # Příprava samostatného grafu pro lepší kontrolu
        plt.close('all')  # Zavřeme všechny existující grafy
        
        # Create figure and axes
        fig = plt.figure(figsize=(12, 8), dpi=100)
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
        
        # Disable automatic locator adjustment to prevent excessive tick generation
        locator = mdates.AutoDateLocator(maxticks=10)  # Drasticky omezíme počet značek na ose x
        formatter = mdates.ConciseDateFormatter(locator)
        
        ax1.xaxis.set_major_locator(locator)
        ax1.xaxis.set_major_formatter(formatter)
        
        # Draw candles directly using matplotlib for better control and performance
        try:
            # Místo mplfinance použijeme přímé vykreslení svíček pomocí matplotlib - mnohem výkonnější
            dates = mdates.date2num(plot_data.index.to_pydatetime())
            
            # Vytvoření OHLC dat pro candlestick
            ohlc = []
            for date, row in zip(dates, plot_data.itertuples()):
                open_price, high, low, close = row.Open, row.High, row.Low, row.Close
                ohlc.append([date, open_price, high, low, close])
            
            # Přímé vykreslení svíček
            from matplotlib.collections import LineCollection, PolyCollection
            
            # Vytvoření svíček
            width = 0.6  # Šířka svíček
            delta = width / 2
            
            up = plot_data['Close'] > plot_data['Open']
            down = ~up
            
            # Svislé čáry (knoty)
            wicks_up = [((x, l), (x, h)) for x, l, h in zip(dates[up], plot_data['Open'][up], plot_data['High'][up])]
            wicks_down = [((x, l), (x, h)) for x, l, h in zip(dates[up], plot_data['Low'][up], plot_data['Close'][up])]
            wicks_up_collection = LineCollection(wicks_up, colors='#00a061', linewidths=1)
            wicks_down_collection = LineCollection(wicks_down, colors='#00a061', linewidths=1)
            ax1.add_collection(wicks_up_collection)
            ax1.add_collection(wicks_down_collection)
            
            wicks_up = [((x, l), (x, h)) for x, l, h in zip(dates[down], plot_data['Close'][down], plot_data['High'][down])]
            wicks_down = [((x, l), (x, h)) for x, l, h in zip(dates[down], plot_data['Low'][down], plot_data['Open'][down])]
            wicks_up_collection = LineCollection(wicks_up, colors='#eb4d5c', linewidths=1)
            wicks_down_collection = LineCollection(wicks_down, colors='#eb4d5c', linewidths=1)
            ax1.add_collection(wicks_up_collection)
            ax1.add_collection(wicks_down_collection)
            
            # Těla svíček
            rect_up = [((x - delta, o), (x + delta, c)) for x, o, c in zip(dates[up], plot_data['Open'][up], plot_data['Close'][up])]
            rect_down = [((x - delta, o), (x + delta, c)) for x, o, c in zip(dates[down], plot_data['Open'][down], plot_data['Close'][down])]
            
            # Vytvoření obdélníků pro těla svíček
            def path_rect(x0, y0, x1, y1):
                return [(x0, y0), (x0, y1), (x1, y1), (x1, y0), (x0, y0)]
            
            barups = [path_rect(x - delta, o, x + delta, c) for x, o, c in zip(dates[up], plot_data['Open'][up], plot_data['Close'][up])]
            bardowns = [path_rect(x - delta, o, x + delta, c) for x, o, c in zip(dates[down], plot_data['Open'][down], plot_data['Close'][down])]
            
            # Kolekce pro matplotlib
            poly_up = PolyCollection(barups, facecolors='#00a061', edgecolors='#00a061', linewidths=1)
            poly_down = PolyCollection(bardowns, facecolors='#eb4d5c', edgecolors='#eb4d5c', linewidths=1)
            
            # Přidání svíček do grafu
            ax1.add_collection(poly_up)
            ax1.add_collection(poly_down)
            
            # Vykreslení objemů
            width = 0.8
            delta = width / 2
            
            # Zelená barva pro volume, pokud close > open
            volume_up = plot_data['Volume'].copy()
            volume_up[~up] = 0
            volume_down = plot_data['Volume'].copy()
            volume_down[up] = 0
            
            # Vytvoření barplotů pro volume
            ax2.bar(dates[up], volume_up[up], width=width, color='#a3e2c5')
            ax2.bar(dates[down], volume_down[down], width=width, color='#f1c3c8')
            
            # Nastavení autoscale pro zobrazení dat
            ax1.autoscale_view()
            ax2.autoscale_view()
            
            # Nastavení rozsahu osy x pro lepší zobrazení
            start_date = plot_data.index[0] - timedelta(hours=2)
            end_date = plot_data.index[-1] + timedelta(hours=2)
            ax1.set_xlim(mdates.date2num(start_date), mdates.date2num(end_date))
            
            # Nastavení y-limitů pro price (přidat margin)
            price_min = plot_data['Low'].min() * 0.995
            price_max = plot_data['High'].max() * 1.005
            ax1.set_ylim(price_min, price_max)
            
        except Exception as e:
            logger.error(f"Chyba při vykreslování svíček: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Nouzové vykreslení jako čárový graf
            ax1.plot(plot_data.index, plot_data['Close'], label='Close Price')
            ax2.bar(plot_data.index, plot_data['Volume'], color='gray', alpha=0.3)
        
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
        if scenarios and len(plot_data) > 0:
            current_price = plot_data['Close'].iloc[-1]
            
            # Define projection days based on timeframe
            if timeframe == '1w':
                projection_hours = 30 * 24  # 1 měsíc
            elif timeframe == '1d':
                projection_hours = 14 * 24  # 2 týdny
            elif timeframe == '4h':
                projection_hours = 7 * 24   # 1 týden
            elif timeframe == '1h':
                projection_hours = 3 * 24   # 3 dny
            else:
                projection_hours = 2 * 24   # 2 dny pro ostatní timeframy
            
            # Zjednodušení pro scénáře - použijeme jen začátek a konec
            last_date = plot_data.index[-1]
            future_date = last_date + timedelta(hours=projection_hours)

            # Vykreslení scénářů zjednodušeně - jen linka od posledního bodu k cíli
            for scenario_type, target_price in scenarios:
                if scenario_type == 'bullish' and target_price > current_price:
                    # Bullish scénář - jednoduchá zelená čára
                    ax1.plot(
                        [last_date, future_date],
                        [current_price, target_price],
                        '-', color='green', linewidth=2.5
                    )

                    # Popisek cíle
                    ax1.text(
                        future_date,
                        target_price,
                        f"{target_price:.0f}",
                        color='white',
                        fontweight='bold',
                        fontsize=10,
                        bbox=dict(facecolor='green', alpha=0.9, edgecolor='green')
                    )

                    # Přidání do legendy
                    legend_elements.append(Line2D([0], [0], color='green', lw=2.5, label='Bullish Scenario'))

                elif scenario_type == 'bearish' and target_price < current_price:
                    # Bearish scénář - jednoduchá červená čára
                    ax1.plot(
                        [last_date, future_date],
                        [current_price, target_price],
                        '-', color='red', linewidth=2.5
                    )

                    # Popisek cíle
                    ax1.text(
                        future_date,
                        target_price,
                        f"{target_price:.0f}",
                        color='white',
                        fontweight='bold',
                        fontsize=10,
                        bbox=dict(facecolor='red', alpha=0.9, edgecolor='red')
                    )

                    # Přidání do legendy
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

        # Add proper tick formatting
        # Zásadní změna - nastavíme vlastní jednoduchý formátovač s malým počtem tiků
        # Pro timeframe 30m použijeme vyšší intervaly značek
        days_shown = (plot_data.index[-1] - plot_data.index[0]).total_seconds() / (24 * 3600)

        if days_shown > 5:
            # Pro více než 5 dní - zobrazení po dnech
            ax1.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        elif days_shown > 2:
            # Pro 2-5 dní - zobrazení po 12 hodinách
            ax1.xaxis.set_major_locator(mdates.HourLocator(interval=12))
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        else:
            # Pro méně než 2 dny - zobrazení po 6 hodinách
            ax1.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))

        # Nastavení popisků os
        ax1.set_ylabel('Price')
        ax2.set_ylabel('Volume')

        # Add generation timestamp
        plt.figtext(
            0.01, 0.01,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            fontsize=7,
            bbox=dict(facecolor='white', alpha=0.8)
        )

        # Uložení grafu bez tight_layout (to způsobuje problémy)
        try:
            # Explicitně nastavíme správné okraje
            plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15, hspace=0.05)
            plt.savefig(filename, dpi=150)
            logger.info(f"Graf úspěšně uložen: {filename}")
        except Exception as e:
            logger.error(f"Chyba při ukládání grafu: {str(e)}")
            # Pokusíme se uložit do záložního souboru
            backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            try:
                plt.savefig(backup_filename, dpi=100)
                logger.info(f"Graf uložen do záložního souboru: {backup_filename}")
                filename = backup_filename
            except:
                logger.error("Nelze uložit ani do záložního souboru!")

        plt.close(fig)

        return filename
