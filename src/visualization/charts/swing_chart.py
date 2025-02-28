#!/usr/bin/env python3

import matplotlib
# Nastavení neinteraktivního backend před importem pyplot
matplotlib.use('Agg')

import logging
import matplotlib.pyplot as plt
import mplfinance as mpf
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

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
        
        # Vykreslení svíček
        mpf.plot(
            self.plot_data, 
            ax=self.ax1, 
            volume=self.ax2, 
            type='candle', 
            style=style,
            show_nontrading=False,
            datetime_format='%Y-%m-%d',
            xrotation=25
        )
        
        # Formátování x-osy pro lepší zobrazení dat
        if self.timeframe == '1w':
            self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            self.ax1.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0))  # Každé pondělí
        elif self.timeframe == '1d':
            self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            self.ax1.xaxis.set_major_locator(mdates.DayLocator(interval=5))  # Každý 5. den
        else:
            self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
            self.ax1.xaxis.set_major_locator(mdates.HourLocator(interval=12))  # Každých 12 hodin
        
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
            
    def add_scenarios(self, scenarios):
        """
        Přidá scénáře vývoje ceny do grafu.
        
        Args:
            scenarios (list): Seznam scénářů k vizualizaci jako (typ, cena)
        """
        if not scenarios:
            return
            
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
                ncol=min(len(self.legend_elements), 3)
            )
        
        # Volání render metody ze základní třídy
        return super().render(filename)
