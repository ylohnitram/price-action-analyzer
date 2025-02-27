#!/usr/bin/env python3

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for rendering charts
from datetime import datetime, timedelta
import os
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import logging
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import re

# Import konfiguračních modulů
from src.visualization.config.colors import get_color_scheme, get_candle_colors, get_zone_colors, get_scenario_colors
from src.visualization.config.timeframes import get_timeframe_config, get_min_candles_by_timeframe, get_days_by_timeframe

logger = logging.getLogger(__name__)

class ChartGenerator:
    """Třída pro generování svíčkových grafů s podporou a odporem zón."""
    
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

    def prepare_data(self, df, timeframe=None, days_to_show=5, hours_to_show=None):
        """Připraví data pro vykreslení grafu."""
        # Příprava dat pro mplfinance
        df_copy = df.copy()
        
        # Převod názvů sloupců na správný formát
        ohlcv_columns = {
            'open': 'Open', 'high': 'High', 'low': 'Low', 
            'close': 'Close', 'volume': 'Volume'
        }
        
        for old_col, new_col in ohlcv_columns.items():
            if old_col in df_copy.columns and new_col not in df_copy.columns:
                df_copy[new_col] = df_copy[old_col]
        
        # Kontrola, zda máme všechny potřebné sloupce
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_columns:
            if col not in df_copy.columns:
                logger.error(f"Chybí sloupec {col} v dataframe")
                if 'Open' not in df_copy.columns and 'Close' in df_copy.columns:
                    df_copy['Open'] = df_copy['Close']
                if 'High' not in df_copy.columns and 'Close' in df_copy.columns:
                    df_copy['High'] = df_copy['Close'] * 1.001  # Mírně vyšší než Close
                if 'Low' not in df_copy.columns and 'Close' in df_copy.columns:
                    df_copy['Low'] = df_copy['Close'] * 0.999   # Mírně nižší než Close
                if 'Close' not in df_copy.columns and 'Open' in df_copy.columns:
                    df_copy['Close'] = df_copy['Open']
                if 'Volume' not in df_copy.columns:
                    df_copy['Volume'] = 0
        
        # Zajištění datetime indexu
        if not isinstance(df_copy.index, pd.DatetimeIndex):
            df_copy.index = pd.to_datetime(df_copy.index)
        
        # Odstranění duplicit v indexu
        if df_copy.index.duplicated().any():
            logger.warning(f"Nalezeny duplicitní indexy! Odstraňuji...")
            df_copy = df_copy[~df_copy.index.duplicated(keep='first')]
        
        # Seřazení dataframe podle indexu
        df_copy = df_copy.sort_index()
        
        # Omezení počtu svíček
        max_candles = 96
        
        # Určení počtu svíček podle timeframe
        if hours_to_show:
            # Pro intraday grafy s hodinami použijeme přímé omezení počtu svíček
            if timeframe == '30m':
                candles_to_show = min(hours_to_show * 2, max_candles)
            elif timeframe == '5m':
                candles_to_show = min(hours_to_show * 12, max_candles)
            else:
                candles_to_show = max_candles
        else:
            # Pro denní grafy použijeme omezení podle počtu dní
            if timeframe == '1d':
                candles_to_show = min(days_to_show, max_candles)
            elif timeframe == '1w':
                candles_to_show = min(days_to_show // 7 + 1, max_candles)
            else:
                candles_to_show = max_candles
        
        # Výběr dat pro vykreslení
        plot_data = df_copy.tail(candles_to_show).copy()
        
        return plot_data

    def draw_support_resistance_zones(self, ax, support_zones, resistance_zones, data_start, zone_colors=None, alpha=0.2):
        """Vykreslí zóny supportů a resistancí."""
        if zone_colors is None:
            zone_colors = {
                'support': '#006400',  # Tmavě zelená pro support
                'resistance': '#8B0000'  # Tmavě červená pro resistance
            }
        
        legend_elements = []
        
        # Vykreslení support zón
        for i, (s_min, s_max) in enumerate(support_zones):
            # Vykreslení obdélníku pro zónu
            rect = Rectangle(
                (0, s_min),  # pozice (x, y)
                1,  # šířka (bude upravena na celou šířku grafu)
                s_max - s_min,  # výška
                facecolor=zone_colors['support'],
                alpha=alpha,  # průhlednost
                edgecolor=zone_colors['support'],
                linestyle='--',
                linewidth=1,
                transform=ax.get_xaxis_transform()  # Transformace pro správné vykreslení přes celou šířku grafu
            )
            ax.add_patch(rect)
            
            # Přidání popisku
            mid_point = (s_min + s_max) / 2
            ax.text(
                0.01,  # x-pozice (blízko levého okraje)
                mid_point,  # y-pozice
                f"S{i+1}: {mid_point:.0f}",
                color='white',
                fontweight='bold',
                fontsize=9,
                transform=ax.get_yaxis_transform(),  # Pro pozicování v y-prostoru grafu
                bbox=dict(
                    facecolor=zone_colors['support'],
                    alpha=0.9,
                    boxstyle='round,pad=0.3'
                )
            )
        
        # Vykreslení resistance zón
        for i, (r_min, r_max) in enumerate(resistance_zones):
            # Vykreslení obdélníku pro zónu
            rect = Rectangle(
                (0, r_min),  # pozice (x, y)
                1,  # šířka (bude upravena na celou šířku grafu)
                r_max - r_min,  # výška
                facecolor=zone_colors['resistance'],
                alpha=alpha,  # průhlednost
                edgecolor=zone_colors['resistance'],
                linestyle='--',
                linewidth=1,
                transform=ax.get_xaxis_transform()  # Transformace pro správné vykreslení přes celou šířku grafu
            )
            ax.add_patch(rect)
            
            # Přidání popisku
            mid_point = (r_min + r_max) / 2
            ax.text(
                0.01,  # x-pozice (blízko levého okraje)
                mid_point,  # y-pozice
                f"R{i+1}: {mid_point:.0f}",
                color='white',
                fontweight='bold',
                fontsize=9,
                transform=ax.get_yaxis_transform(),  # Pro pozicování v y-prostoru grafu
                bbox=dict(
                    facecolor=zone_colors['resistance'],
                    alpha=0.9,
                    boxstyle='round,pad=0.3'
                )
            )
        
        # Přidání legend elementů
        if support_zones:
            legend_elements.append(Line2D([0], [0], color=zone_colors['support'], lw=2, linestyle='--', label='Support Zone'))
        if resistance_zones:
            legend_elements.append(Line2D([0], [0], color=zone_colors['resistance'], lw=2, linestyle='--', label='Resistance Zone'))
        
        return legend_elements

    def draw_future_scenarios(self, ax, scenarios, current_price, last_date, scenario_colors=None):
        """Vykreslí budoucí scénáře."""
        if scenario_colors is None:
            scenario_colors = {
                'bullish': 'green',
                'bearish': 'red'
            }
        
        legend_elements = []
        
        if not scenarios:
            return legend_elements
        
        # Získání časové osy
        xlim = ax.get_xlim()
        # Vytvoření budoucího data (+10% od konce grafu)
        future_x = xlim[1] + (xlim[1] - xlim[0]) * 0.1
        
        for scenario_type, target_price in scenarios:
            if scenario_type == 'bullish' and target_price > current_price:
                # Vykreslení šipky pro bullish scénář
                ax.annotate('', 
                        xy=(future_x, target_price), 
                        xytext=(xlim[1], current_price),
                        arrowprops=dict(
                            facecolor=scenario_colors['bullish'], 
                            edgecolor=scenario_colors['bullish'],
                            width=2, 
                            headwidth=8, 
                            alpha=0.8
                        )
                )
                
                # Přidání popisku cíle
                ax.text(
                    future_x, 
                    target_price, 
                    f"{target_price:.0f}", 
                    color='white',
                    fontweight='bold',
                    fontsize=10,
                    bbox=dict(
                        facecolor=scenario_colors['bullish'], 
                        alpha=0.9,
                        boxstyle='round,pad=0.3'
                    )
                )
                
                legend_elements.append(Line2D([0], [0], color=scenario_colors['bullish'], lw=2.5, label='Bullish Scenario'))
                
            elif scenario_type == 'bearish' and target_price < current_price:
                # Vykreslení šipky pro bearish scénář
                ax.annotate('', 
                        xy=(future_x, target_price), 
                        xytext=(xlim[1], current_price),
                        arrowprops=dict(
                            facecolor=scenario_colors['bearish'], 
                            edgecolor=scenario_colors['bearish'],
                            width=2, 
                            headwidth=8, 
                            alpha=0.8
                        )
                )
                
                # Přidání popisku cíle
                ax.text(
                    future_x, 
                    target_price, 
                    f"{target_price:.0f}", 
                    color='white',
                    fontweight='bold',
                    fontsize=10,
                    bbox=dict(
                        facecolor=scenario_colors['bearish'], 
                        alpha=0.9,
                        boxstyle='round,pad=0.3'
                    )
                )
                
                legend_elements.append(Line2D([0], [0], color=scenario_colors['bearish'], lw=2.5, label='Bearish Scenario'))
        
        return legend_elements

    def draw_chart_for_complete_analysis(self, plot_data, support_zones, resistance_zones, scenarios, symbol, timeframe, title):
        """Vykreslí graf pro kompletní analýzu se všemi prvky."""
        # Získání barevného schématu
        colors = get_color_scheme()
        candle_colors = colors['candle_colors']
        zone_colors = {
            'support': colors['zone_colors']['support'][0],
            'resistance': colors['zone_colors']['resistance'][0]
        }
        scenario_colors = colors['scenario_colors']
        
        # Nastavení stylu grafu
        mc = mpf.make_marketcolors(
            up=candle_colors['up'],
            down=candle_colors['down'],
            edge={'up': candle_colors['edge_up'], 'down': candle_colors['edge_down']},
            wick={'up': candle_colors['wick_up'], 'down': candle_colors['wick_down']},
            volume={'up': candle_colors['volume_up'], 'down': candle_colors['volume_down']}
        )
        
        style = mpf.make_mpf_style(
            base_mpf_style='yahoo',
            marketcolors=mc,
            gridstyle='-',
            gridcolor='#e6e6e6',
            gridaxis='both',
            facecolor='white'
        )
        
        # Příprava argumentů pro mpf.plot
        kwargs = {
            'type': 'candle',
            'style': style,
            'figsize': (12, 8),
            'title': title,
            'volume': True,
            'volume_panel': 1,
            'panel_ratios': (4, 1),  # Poměr velikosti svíček a volume
            'tight_layout': False,
            'figscale': 1.5,
            'figratio': (10, 6),
            'datetime_format': '%m-%d %H:%M',
            'xrotation': 25,
            'returnfig': True,
        }
        
        # Vytvoření základního grafu
        fig, axes = mpf.plot(plot_data, **kwargs)
        
        # Přidání support a resistance zón
        price_ax = axes[0]
        legend_elements = self.draw_support_resistance_zones(
            price_ax, 
            support_zones, 
            resistance_zones, 
            plot_data.index[0],
            zone_colors=zone_colors
        )
        
        # Přidání scénářů s projekcí do budoucna
        if scenarios and len(plot_data) > 0:
            current_price = plot_data['Close'].iloc[-1]
            last_date = plot_data.index[-1]
            
            scenario_legend = self.draw_future_scenarios(
                price_ax, 
                scenarios, 
                current_price, 
                last_date,
                scenario_colors=scenario_colors
            )
            
            legend_elements.extend(scenario_legend)
        
        # Přidání legendy
        if legend_elements:
            price_ax.legend(
                handles=legend_elements,
                loc='upper left',
                fontsize=10,
                framealpha=0.8,
                ncol=min(len(legend_elements), 3)
            )
        
        # Nastavení většího mezery mezi grafy svíček a objemů
        plt.subplots_adjust(hspace=0.3)
        
        return fig, axes

    def draw_chart_for_intraday_analysis(self, plot_data, support_zones, resistance_zones, symbol, timeframe, title):
        """Vykreslí graf pro intraday analýzu bez budoucích scénářů, pouze s S/R zónami."""
        # Získání barevného schématu
        colors = get_color_scheme()
        candle_colors = colors['candle_colors']
        zone_colors = {
            'support': colors['zone_colors']['support'][0],
            'resistance': colors['zone_colors']['resistance'][0]
        }
        
        # Nastavení stylu grafu
        mc = mpf.make_marketcolors(
            up=candle_colors['up'],
            down=candle_colors['down'],
            edge={'up': candle_colors['edge_up'], 'down': candle_colors['edge_down']},
            wick={'up': candle_colors['wick_up'], 'down': candle_colors['wick_down']},
            volume={'up': candle_colors['volume_up'], 'down': candle_colors['volume_down']}
        )
        
        style = mpf.make_mpf_style(
            base_mpf_style='yahoo',
            marketcolors=mc,
            gridstyle='-',
            gridcolor='#e6e6e6',
            gridaxis='both',
            facecolor='white'
        )
        
        # Příprava argumentů pro mpf.plot
        kwargs = {
            'type': 'candle',
            'style': style,
            'figsize': (12, 8),
            'title': title,
            'volume': True,
            'volume_panel': 1,
            'panel_ratios': (4, 1),  # Poměr velikosti svíček a volume
            'tight_layout': False,
            'figscale': 1.5,
            'figratio': (10, 6),
            'datetime_format': '%m-%d %H:%M',
            'xrotation': 25,
            'returnfig': True,
        }
        
        # Vytvoření základního grafu
        fig, axes = mpf.plot(plot_data, **kwargs)
        
        # Přidání support a resistance zón
        price_ax = axes[0]
        legend_elements = self.draw_support_resistance_zones(
            price_ax, 
            support_zones, 
            resistance_zones, 
            plot_data.index[0],
            zone_colors=zone_colors
        )
        
        # Přidání legendy
        if legend_elements:
            price_ax.legend(
                handles=legend_elements,
                loc='upper left',
                fontsize=10,
                framealpha=0.8,
                ncol=min(len(legend_elements), 2)
            )
        
        # Nastavení většího mezery mezi grafy svíček a objemů
        plt.subplots_adjust(hspace=0.3)
        
        return fig, axes

    def draw_chart_for_simple_analysis(self, plot_data, support_zones, resistance_zones, symbol, timeframe, title):
        """Vykreslí jednoduchý graf pouze s S/R zónami."""
        # Stejná implementace jako intraday, ale můžeme přidat specifické prvky v budoucnu
        return self.draw_chart_for_intraday_analysis(plot_data, support_zones, resistance_zones, symbol, timeframe, title)

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
            analysis_type (str, optional): Typ analýzy - "complete", "intraday" nebo "simple"
            
        Returns:
            str: Cesta k vygenerovanému grafickému souboru
        """
        # Nastavení cesty pro uložení grafu
        logger.info(f"Generating chart for {symbol} ({timeframe}), analysis type: {analysis_type}")
        charts_dir = "charts"
        os.makedirs(charts_dir, exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(charts_dir, f"{symbol}_{timeframe}_{timestamp}.png")

        # Logování informací o dataframe
        logger.info(f"Sloupce v dataframe: {df.columns.tolist()}")
        logger.info(f"Celkový počet svíček: {len(df)}")
        
        # Příprava dat pro vykreslení
        plot_data = self.prepare_data(df, timeframe, days_to_show, hours_to_show)
        
        # Logování informací o vybraných datech
        logger.info(f"Vybrán časový úsek od {plot_data.index[0]} do {plot_data.index[-1]} s {len(plot_data)} svíčkami")
        
        if len(plot_data) > 0:
            logger.info(f"První řádek: {plot_data.iloc[0]['Open']}, {plot_data.iloc[0]['High']}, {plot_data.iloc[0]['Low']}, {plot_data.iloc[0]['Close']}")
            logger.info(f"Poslední řádek: {plot_data.iloc[-1]['Open']}, {plot_data.iloc[-1]['High']}, {plot_data.iloc[-1]['Low']}, {plot_data.iloc[-1]['Close']}")
        
        # Extrakce zón z textu, pokud nebyly předány
        if (not support_zones or not resistance_zones) and analysis_text:
            extracted_support, extracted_resistance = self.extract_zones_from_text(analysis_text)
            
            if not support_zones:
                support_zones = extracted_support
            
            if not resistance_zones:
                resistance_zones = extracted_resistance
        
        # Extrakce scénářů z textu, pokud nebyly předány a jedná se o kompletní analýzu
        if analysis_type == "complete" and not scenarios and analysis_text:
            current_price = plot_data['Close'].iloc[-1] if len(plot_data) > 0 else None
            if current_price:
                scenarios = self.extract_scenarios_from_text(analysis_text, current_price)
        
        # Nastavení titulku grafu
        title = f"{symbol} - {timeframe} Timeframe"
        if timeframe in ['1d', '1w']:
            title += " (Long-term Analysis)"
        elif timeframe in ['4h', '1h']:
            title += " (Medium-term Analysis)"
        else:
            title += " (Short-term Analysis)"
        
        # Vykreslení grafu podle typu analýzy
        if analysis_type == "complete":
            fig, axes = self.draw_chart_for_complete_analysis(
                plot_data, support_zones, resistance_zones, scenarios, symbol, timeframe, title
            )
        elif analysis_type == "intraday":
            fig, axes = self.draw_chart_for_intraday_analysis(
                plot_data, support_zones, resistance_zones, symbol, timeframe, title
            )
        else:  # simple
            fig, axes = self.draw_chart_for_simple_analysis(
                plot_data, support_zones, resistance_zones, symbol, timeframe, title
            )
        
        # Přidání časového razítka
        plt.figtext(
            0.01, 0.01,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            fontsize=8,
            bbox=dict(facecolor='white', alpha=0.8)
        )
        
        # Uložení grafu
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        logger.info(f"Graf úspěšně uložen: {filename}")
        
        plt.close(fig)
        
        return filename
