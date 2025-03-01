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
            
            # Ruční vykreslení svíček pro lepší kontrolu nad rozložením
            width = 0.7  # Šířka svíčky
            width2 = 0.1  # Šířka knotu
            
            # Převod datového indexu na numerický pro vykreslení
            x_values = np.arange(len(self.plot_data))
            
            # Rozdělení na stoupající a klesající svíčky
            up = self.plot_data[self.plot_data['Close'] >= self.plot_data['Open']]
            down = self.plot_data[self.plot_data['Close'] < self.plot_data['Open']]
            
            # Bezpečnější způsob získání indexů
            up_indices = []
            for idx in up.index:
                try:
                    up_indices.append(self.plot_data.index.get_loc(idx))
                except:
                    # Pokud nastane problém, zkusíme jiný způsob
                    pos = list(self.plot_data.index).index(idx)
                    up_indices.append(pos)
            
            down_indices = []
            for idx in down.index:
                try:
                    down_indices.append(self.plot_data.index.get_loc(idx))
                except:
                    # Pokud nastane problém, zkusíme jiný způsob
                    pos = list(self.plot_data.index).index(idx)
                    down_indices.append(pos)
            
            # Vykreslení stoupajících svíček
            if len(up_indices) > 0:
                # Těla svíček
                self.ax1.bar(
                    up_indices, 
                    up['Close'] - up['Open'], 
                    width, 
                    bottom=up['Open'], 
                    color=candle_colors['up'], 
                    zorder=3
                )
                # Horní knoty
                self.ax1.bar(
                    up_indices, 
                    up['High'] - up['Close'], 
                    width2, 
                    bottom=up['Close'], 
                    color=candle_colors['wick_up'], 
                    zorder=3
                )
                # Dolní knoty
                self.ax1.bar(
                    up_indices, 
                    up['Open'] - up['Low'], 
                    width2, 
                    bottom=up['Low'], 
                    color=candle_colors['wick_up'], 
                    zorder=3
                )
                
                # Volume pro stoupající svíčky
                self.ax2.bar(
                    up_indices, 
                    up['Volume'], 
                    width, 
                    color=candle_colors['volume_up']
                )
                
            # Vykreslení klesajících svíček
            if len(down_indices) > 0:
                # Těla svíček
                self.ax1.bar(
                    down_indices, 
                    down['Close'] - down['Open'], 
                    width, 
                    bottom=down['Open'], 
                    color=candle_colors['down'], 
                    zorder=3
                )
                # Horní knoty
                self.ax1.bar(
                    down_indices, 
                    down['High'] - down['Open'], 
                    width2, 
                    bottom=down['Open'], 
                    color=candle_colors['wick_down'], 
                    zorder=3
                )
                # Dolní knoty
                self.ax1.bar(
                    down_indices, 
                    down['Low'] - down['Close'], 
                    width2, 
                    bottom=down['Close'], 
                    color=candle_colors['wick_down'], 
                    zorder=3
                )
                
                # Volume pro klesající svíčky
                self.ax2.bar(
                    down_indices, 
                    down['Volume'], 
                    width, 
                    color=candle_colors['volume_down']
                )
            
            # Nastavení os
            # Omezení počtu zobrazených ticků na ose X pro přehlednost
            max_ticks = min(len(self.plot_data), 10)  # Maximálně 10 popisků na ose X
            step = max(1, len(self.plot_data) // max_ticks)
            
            # Nastavení ticků na ose X
            tick_positions = x_values[::step]
            tick_labels = [self.plot_data.index[i].strftime('%Y-%m-%d') for i in tick_positions]
            
            self.ax1.set_xticks(tick_positions)
            self.ax1.set_xticklabels(tick_labels, rotation=45, ha='right')
            
            # Zajistit, že osa X má správný rozsah - ponecháme 20% místo vpravo pro scénáře
            extra_space = len(self.plot_data) * 0.2
            self.ax1.set_xlim(-0.5, len(self.plot_data) - 0.5 + extra_space)
            
            # Stejné nastavení pro osu volume
            self.ax2.set_xticks(tick_positions)
            self.ax2.set_xticklabels(tick_labels, rotation=45, ha='right')
            self.ax2.set_xlim(-0.5, len(self.plot_data) - 0.5 + extra_space)
            
            # Přidání mřížky
            self.ax1.grid(True, alpha=0.3)
            self.ax2.grid(True, alpha=0.3)
            
            logger.info("Ruční vykreslení svíčkového grafu s objemy úspěšně dokončeno")
            
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
            
            # Manuální vykreslení zón přes celou šířku grafu
            xlim = self.ax1.get_xlim()
            xmin, xmax = xlim
            width = xmax - xmin
            
            # Přidání do legendy
            self.legend_elements.append(Line2D([0], [0], color=zone_colors[0], lw=2, linestyle='--', label='Support Zone'))
            
            # Vykreslení zón
            for i, (zone_min, zone_max) in enumerate(zones):
                color_idx = min(i, len(zone_colors) - 1)
                color = zone_colors[color_idx]
                
                # Vytvoření obdélníku pro zónu
                height = zone_max - zone_min
                rect = plt.Rectangle(
                    (xmin, zone_min),
                    width,
                    height,
                    facecolor=color,
                    alpha=0.2,
                    edgecolor=color,
                    linestyle='--',
                    linewidth=1,
                    zorder=1
                )
                self.ax1.add_patch(rect)
                
                # Přidání popisku
                midpoint = (zone_min + zone_max) / 2
                self.ax1.text(
                    xmin + width * 0.02,
                    midpoint,
                    f"S{i+1}: {midpoint:.0f}",
                    color='white',
                    fontweight='bold',
                    fontsize=9,
                    bbox=dict(
                        facecolor=color,
                        alpha=0.7,
                        boxstyle='round,pad=0.3'
                    ),
                    zorder=4
                )
                
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
            # Explicitně definujeme červené barvy pro rezistenci
            zone_colors = ['#B22222', '#CC0000', '#FF0000', '#FF3333']
            
            # Manuální vykreslení zón přes celou šířku grafu
            xlim = self.ax1.get_xlim()
            xmin, xmax = xlim
            width = xmax - xmin
            
            # Přidání do legendy
            self.legend_elements.append(Line2D([0], [0], color=zone_colors[0], lw=2, linestyle='--', label='Resistance Zone'))
            
            # Vykreslení zón
            for i, (zone_min, zone_max) in enumerate(zones):
                color_idx = min(i, len(zone_colors) - 1)
                color = zone_colors[color_idx]
                
                # Vytvoření obdélníku pro zónu
                height = zone_max - zone_min
                rect = plt.Rectangle(
                    (xmin, zone_min),
                    width,
                    height,
                    facecolor=color,
                    alpha=0.2,
                    edgecolor=color,
                    linestyle='--',
                    linewidth=1,
                    zorder=1
                )
                self.ax1.add_patch(rect)
                
                # Přidání popisku
                midpoint = (zone_min + zone_max) / 2
                self.ax1.text(
                    xmin + width * 0.02,
                    midpoint,
                    f"R{i+1}: {midpoint:.0f}",
                    color='white',
                    fontweight='bold',
                    fontsize=9,
                    bbox=dict(
                        facecolor=color,
                        alpha=0.7,
                        boxstyle='round,pad=0.3'
                    ),
                    zorder=4
                )
                
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
            
            # Vykreslení scénářů s projekcí do budoucnosti pomocí komponenty
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
