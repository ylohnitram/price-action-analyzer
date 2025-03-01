#!/usr/bin/env python3

import matplotlib
# Nastavení neinteraktivního backend před importem pyplot
matplotlib.use('Agg')

import logging
import matplotlib.pyplot as plt
import mplfinance as mpf
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
import pandas as pd
import numpy as np

from src.visualization.charts.base_chart import BaseChart
from src.visualization.components.zones import draw_support_zones, draw_resistance_zones
from src.visualization.components.scenarios import draw_scenarios

logger = logging.getLogger(__name__)

class SwingChart(BaseChart):
    """Třída pro vykreslování swing grafů s dlouhodobou analýzou."""
    
    def __init__(self, df, symbol, timeframe=None, days_to_show=30):
        """
        Inicializace swing grafu.
        
        Args:
            df (pandas.DataFrame): DataFrame s OHLCV daty
            symbol (str): Obchodní symbol
            timeframe (str, optional): Časový rámec dat
            days_to_show (int, optional): Počet dní dat k zobrazení
        """
        # Nastavení výchozích dnů pro zobrazení pokud není specifikováno
        if timeframe == '1d':
            days_to_show = min(days_to_show, 60)  # Pro denní data maximálně 60 dní
        elif timeframe == '1w':
            days_to_show = min(days_to_show, 180)  # Pro týdenní data maximálně 180 dní
        elif timeframe == '4h':
            days_to_show = min(days_to_show, 30)  # Pro 4h data maximálně 30 dní
        
        # Volání konstruktoru předka
        super().__init__(df, symbol, timeframe, days_to_show=days_to_show, hours_to_show=None)
        
        # Inicializace legend elementů
        self.legend_elements = []
        
        # Vykreslení svíček
        self.draw_candlesticks()
        
    def draw_candlesticks(self):
        """Vykreslí svíčkový graf s objemy."""
        # Definice barev pro svíčky z konfigurace
        candle_colors = self.colors['candle_colors']
        
        # Kontrola, zda máme dostatek dat
        if len(self.plot_data) < 2:
            logger.error(f"Nedostatek dat pro vykreslení svíčkového grafu: {len(self.plot_data)} svíček")
            return
        
        try:
            # Kontrola, že dataframe má správnou strukturu
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in self.plot_data.columns for col in required_columns):
                missing_cols = [col for col in required_columns if col not in self.plot_data.columns]
                logger.error(f"Chybí sloupce v dataframe: {missing_cols}")
                return
            
            # Kompletní info o datech pro ladění
            logger.info(f"Svíčkový graf dat: {len(self.plot_data)} svíček od {self.plot_data.index[0]} do {self.plot_data.index[-1]}")
            logger.info(f"První svíčka: Open={self.plot_data['Open'].iloc[0]}, High={self.plot_data['High'].iloc[0]}, Low={self.plot_data['Low'].iloc[0]}, Close={self.plot_data['Close'].iloc[0]}")
            logger.info(f"Poslední svíčka: Open={self.plot_data['Open'].iloc[-1]}, High={self.plot_data['High'].iloc[-1]}, Low={self.plot_data['Low'].iloc[-1]}, Close={self.plot_data['Close'].iloc[-1]}")
            
            # Omezení dat pro lepší zobrazení
            if self.timeframe == '1d' and len(self.plot_data) > 30:
                logger.info(f"Omezuji počet svíček pro denní graf na max 30 (aktuálně {len(self.plot_data)})")
                self.plot_data = self.plot_data.tail(30).copy()
            
            # Vytvoření marketcolors pro mplfinance
            mc = mpf.make_marketcolors(
                up=candle_colors['up'],
                down=candle_colors['down'],
                edge={'up': candle_colors['edge_up'], 'down': candle_colors['edge_down']},
                wick={'up': candle_colors['wick_up'], 'down': candle_colors['wick_down']},
                volume={'up': candle_colors['volume_up'], 'down': candle_colors['volume_down']}
            )
            
            # Definice stylu grafu
            style = mpf.make_mpf_style(
                base_mpf_style='yahoo',
                marketcolors=mc,
                gridstyle='-',
                gridcolor='#e6e6e6',
                gridaxis='both',
                facecolor='white'
            )
            
            # Nastavení fontů - menší písmo pro lepší kompatibilitu
            plt.rcParams['font.size'] = 8
            
            # Ořez dat na přesný počet obchodních dnů pro 1d timeframe
            if self.timeframe == '1d':
                # Určení počtu svíček pro zobrazení
                num_candles = min(len(self.plot_data), 30)
                self.plot_data = self.plot_data.tail(num_candles).copy()
            
            # Vykreslení svíček pomocí mplfinance
            fig_ohlc = mpf.plot(
                self.plot_data, 
                type='candle', 
                style=style,
                show_nontrading=False,
                returnfig=True  # Vrátit figuru místo zobrazení
            )
            
            # Extrakce obrázku
            ohlc_ax = fig_ohlc[1][0]  # Získat osu s OHLC daty
            
            # Zkopírování svíček do našeho grafu
            for collection in ohlc_ax.collections:
                self.ax1.add_collection(collection.copy())
            
            for line in ohlc_ax.lines:
                self.ax1.add_line(line)
            
            # Přenesení Y dat a limitů
            y_min, y_max = ohlc_ax.get_ylim()
            y_range = y_max - y_min
            y_padding = y_range * 0.1  # Přidání 10% padding
            self.ax1.set_ylim(y_min - y_padding, y_max + y_padding)
            
            # Odstranění původního grafu
            plt.close(fig_ohlc[0])
            
            # Nastavení vhodných formátovačů pro osy
            if self.timeframe == '1w':
                self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                self.ax1.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=1))
            elif self.timeframe == '1d':
                self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                # Pro denní data nastavit minimální počet bodů na ose
                self.ax1.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(self.plot_data) // 10)))
            elif self.timeframe == '4h':
                self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
                self.ax1.xaxis.set_major_locator(mdates.HourLocator(interval=24))
            
            # Natočení popisků a omezení počtu značek
            self.ax1.tick_params(axis='x', rotation=45, labelsize=8)
            self.ax1.tick_params(axis='y', labelsize=8)
            
            # Vypnutí mřížky
            self.ax1.grid(False)
            self.ax2.grid(False)
            
            logger.info("Svíčkový graf úspěšně vykreslen")
            
        except Exception as e:
            logger.error(f"Chyba při vykreslování svíčkového grafu: {str(e)}")
            # Logujeme detailní stack trace pro lepší diagnostiku
            import traceback
            logger.error(traceback.format_exc())
        
    def add_support_zones(self, zones):
        """
        Přidá supportní zóny do grafu.
        
        Args:
            zones (list): Seznam zón jako (min, max) tuples
        """
        if not zones:
            return
            
        try:
            # Získání barevného schématu
            zone_colors = self.colors['zone_colors']['support']
            
            # Vykreslení zón
            support_zone_added = draw_support_zones(self.ax1, zones, self.plot_data.index[0], zone_colors)
            
            # Přidání do legendy
            if support_zone_added:
                self.legend_elements.append(Line2D([0], [0], color=zone_colors[0], lw=2, linestyle='--', label='Support Zone'))
                
            logger.info(f"Přidáno {len(zones)} supportních zón")
            
        except Exception as e:
            logger.error(f"Chyba při přidávání supportních zón: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
    def add_resistance_zones(self, zones):
        """
        Přidá resistenční zóny do grafu.
        
        Args:
            zones (list): Seznam zón jako (min, max) tuples
        """
        if not zones:
            return
            
        try:
            # Získání barevného schématu
            zone_colors = self.colors['zone_colors']['resistance']
            
            # Vykreslení zón
            resistance_zone_added = draw_resistance_zones(self.ax1, zones, self.plot_data.index[0], zone_colors)
            
            # Přidání do legendy
            if resistance_zone_added:
                self.legend_elements.append(Line2D([0], [0], color=zone_colors[0], lw=2, linestyle='--', label='Resistance Zone'))
                
            logger.info(f"Přidáno {len(zones)} rezistenčních zón")
            
        except Exception as e:
            logger.error(f"Chyba při přidávání rezistenčních zón: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
    def add_scenarios(self, scenarios):
        """
        Přidá scénáře vývoje ceny do grafu.
        
        Args:
            scenarios (list): Seznam scénářů k vizualizaci jako (typ, cena)
        """
        if not scenarios:
            return
            
        try:
            # Získání barevného schématu pro scénáře
            scenario_colors = self.colors['scenario_colors']
            
            # Vykreslení scénářů s projekcí do budoucnosti
            bullish_added, bearish_added = draw_scenarios(
                self.ax1, 
                scenarios, 
                self.plot_data, 
                self.timeframe
            )
            
            # Přidání do legendy
            if bullish_added:
                self.legend_elements.append(Line2D([0], [0], color=scenario_colors['bullish'], lw=2.5, label='Bullish Scenario'))
            if bearish_added:
                self.legend_elements.append(Line2D([0], [0], color=scenario_colors['bearish'], lw=2.5, label='Bearish Scenario'))
                
            logger.info(f"Přidáno {len(scenarios)} scénářů")
            
        except Exception as e:
            logger.error(f"Chyba při přidávání scénářů: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
    def render(self, filename=None):
        """
        Vykreslí graf a uloží do souboru.
        
        Args:
            filename (str, optional): Cesta k souboru pro uložení grafu
            
        Returns:
            str: Cesta k vygenerovanému souboru nebo None v případě chyby
        """
        try:
            # Přidání legendy pokud máme nějaké elementy
            if self.legend_elements:
                self.ax1.legend(
                    handles=self.legend_elements,
                    loc='upper left',
                    fontsize=10,
                    framealpha=0.8,
                    ncol=min(len(self.legend_elements), 3)
                )
            
            # Volání render metody ze základní třídy
            return super().render(filename)
            
        except Exception as e:
            logger.error(f"Chyba při renderování grafu: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
