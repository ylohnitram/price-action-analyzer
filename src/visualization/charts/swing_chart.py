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
            
            # Použijeme mpf.plot pro vykreslení grafu včetně volume
            fig_ohlc = mpf.plot(
                self.plot_data,
                ax=self.ax1,
                volume=self.ax2,
                type='candle',
                style=style,
                show_nontrading=False,
                returnfig=True  # Vrátit figuru místo zobrazení
            )
            
            # Nastavení formátu datumu a rotace popisků
            date_format = '%Y-%m-%d' if self.timeframe in ['1d', '1w'] else '%m-%d %H:%M'
            
            # Nastavení X osy - ponecháme 20% místo vpravo pro scénáře
            x_values = np.arange(len(self.plot_data))
            max_ticks = min(len(self.plot_data), 10)
            step = max(1, len(self.plot_data) // max_ticks)
            
            tick_positions = x_values[::step]
            tick_labels = [self.plot_data.index[i].strftime(date_format) for i in tick_positions]
            
            # Zajistit, že osa X má správný rozsah s prostorem pro scénáře
            extra_space = len(self.plot_data) * 0.2
            x_max = len(self.plot_data) - 1 + extra_space
            
            # Nastavení os pro hlavní graf i volume
            self.ax1.set_xlim(0, x_max)
            self.ax2.set_xlim(0, x_max)
            
            self.ax1.set_xticks(tick_positions)
            self.ax1.set_xticklabels(tick_labels, rotation=45, ha='right')
            
            self.ax2.set_xticks(tick_positions)
            self.ax2.set_xticklabels(tick_labels, rotation=45, ha='right')
            
            # Přidání mřížky
            self.ax1.grid(True, alpha=0.3)
            self.ax2.grid(True, alpha=0.3)
            
            logger.info("Svíčkový graf s objemy úspěšně vykreslen")
            
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
            # Vykreslení scénářů s projekcí do budoucnosti pomocí komponenty
            bullish_added, bearish_added, neutral_added = draw_scenarios(
                self.ax1, 
                scenarios, 
                self.plot_data, 
                self.timeframe
            )
            
            # Přidání do legendy
            if bullish_added:
                self.legend_elements.append(Line2D([0], [0], color='green', lw=2.5, label='Bullish Scenario'))
            if bearish_added:
                self.legend_elements.append(Line2D([0], [0], color='red', lw=2.5, label='Bearish Scenario'))
            if neutral_added:
                self.legend_elements.append(Line2D([0], [0], color='blue', lw=1.5, linestyle='--', label='Neutral Range'))
                
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
