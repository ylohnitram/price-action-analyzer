#!/usr/bin/env python3

import matplotlib
# Nastavení neinteraktivního backend před importem pyplot
matplotlib.use('Agg')

import logging
import matplotlib.pyplot as plt
import mplfinance as mpf
from matplotlib.lines import Line2D

from src.visualization.charts.base_chart import BaseChart
from src.visualization.components.zones import draw_support_zones, draw_resistance_zones

logger = logging.getLogger(__name__)

class SimpleChart(BaseChart):
    """Třída pro vykreslování jednoduchých grafů bez pokročilých funkci."""
    
    def __init__(self, df, symbol, timeframe=None, days_to_show=5):
        """
        Inicializace jednoduchého grafu.
        
        Args:
            df (pandas.DataFrame): DataFrame s OHLCV daty
            symbol (str): Obchodní symbol
            timeframe (str, optional): Časový rámec dat
            days_to_show (int, optional): Počet dní dat k zobrazení
        """
        # Volání konstruktoru předka
        super().__init__(df, symbol, timeframe, days_to_show=days_to_show, hours_to_show=None)
        
        # Inicializace legend elementů
        self.legend_elements = []
        
        # Vykreslení svíček
        self.draw_candlesticks()
        
    def draw_candlesticks(self):
        """Vykreslí základní svíčkový graf s objemy."""
        # Definice barev pro svíčky z konfigurace
        candle_colors = self.colors['candle_colors']
        
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
        
        # Jednoduchý styl formátování času
        datetime_format = '%m-%d' if self.timeframe in ['1d', '1w'] else '%m-%d %H:%M'
        
        # Vykreslení svíček
        mpf.plot(
            self.plot_data, 
            ax=self.ax1, 
            volume=self.ax2, 
            type='candle', 
            style=style, 
            show_nontrading=False,
            datetime_format=datetime_format,
            xrotation=25
        )
        
    def add_support_zones(self, zones):
        """
        Přidá supportní zóny do grafu.
        
        Args:
            zones (list): Seznam zón jako (min, max) tuples
        """
        if not zones:
            return
            
        # Získání barevného schématu
        zone_colors = self.colors['zone_colors']['support']
        
        # Vykreslení zón
        support_zone_added = draw_support_zones(self.ax1, zones, self.plot_data.index[0], zone_colors)
        
        # Přidání do legendy
        if support_zone_added:
            self.legend_elements.append(Line2D([0], [0], color=zone_colors[0], lw=2, linestyle='--', label='Support Zone'))
            
    def add_resistance_zones(self, zones):
        """
        Přidá resistenční zóny do grafu.
        
        Args:
            zones (list): Seznam zón jako (min, max) tuples
        """
        if not zones:
            return
            
        # Získání barevného schématu
        zone_colors = self.colors['zone_colors']['resistance']
        
        # Vykreslení zón
        resistance_zone_added = draw_resistance_zones(self.ax1, zones, self.plot_data.index[0], zone_colors)
        
        # Přidání do legendy
        if resistance_zone_added:
            self.legend_elements.append(Line2D([0], [0], color=zone_colors[0], lw=2, linestyle='--', label='Resistance Zone'))
            
    def render(self, filename=None):
        """
        Vykreslí graf a uloží do souboru.
        
        Args:
            filename (str, optional): Cesta k souboru pro uložení grafu
            
        Returns:
            str: Cesta k vygenerovanému souboru nebo None v případě chyby
        """
        # Přidání legendy pokud máme nějaké elementy
        if self.legend_elements:
            self.ax1.legend(
                handles=self.legend_elements,
                loc='upper left',
                fontsize=10,
                framealpha=0.8,
                ncol=min(len(self.legend_elements), 2)
            )
        
        # Volání render metody ze základní třídy
        return super().render(filename)
