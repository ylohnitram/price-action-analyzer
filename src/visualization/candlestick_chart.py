import logging
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

from src.visualization.base_chart import BaseChart
from src.visualization.components.zones import draw_support_zones, draw_resistance_zones
from src.visualization.components.scenarios import draw_scenarios
from src.visualization.config.colors import get_color_scheme

logger = logging.getLogger(__name__)

class CandlestickChart(BaseChart):
    """Třída pro generování svíčkových grafů."""
    
    def __init__(self, df, symbol, timeframe=None, days_to_show=2, hours_to_show=None):
        """
        Inicializace svíčkového grafu.
        
        Args:
            df (pandas.DataFrame): DataFrame s OHLCV daty
            symbol (str): Obchodní symbol
            timeframe (str, optional): Časový rámec dat
            days_to_show (int, optional): Počet dní dat k zobrazení
            hours_to_show (int, optional): Počet hodin dat k zobrazení
        """
        # Volání konstruktoru předka
        super().__init__(df, symbol, timeframe, days_to_show, hours_to_show)
        
        # Příprava dat specifických pro OHLCV
        self.prepare_ohlcv_data()
        
        # Vykreslení svíček
        self.draw_candlesticks()
        
        # Inicializace legend elementů
        self.legend_elements = []
        
    def prepare_ohlcv_data(self):
        """Připraví data pro OHLCV svíčkový graf."""
        # Standardizace názvů sloupců pro mplfinance
        column_map = {
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        }
        
        # Pokud existují sloupce s malými písmeny, přejmenujeme je
        for old_name, new_name in column_map.items():
            if old_name in self.plot_data.columns and new_name not in self.plot_data.columns:
                self.plot_data[new_name] = self.plot_data[old_name]
                
        # Kontrola, zda máme všechny potřebné sloupce
        required_cols = {'Open', 'High', 'Low', 'Close', 'Volume'}
        if not required_cols.issubset(self.plot_data.columns):
            missing = required_cols - set(self.plot_data.columns)
            logger.error(f"Missing required columns for candlestick chart: {missing}")
            
    def draw_candlesticks(self):
        """Vykreslí svíčkový graf s objemy."""
        # Definice barev pro svíčky
        mc = mpf.make_marketcolors(
            up='#00a061',
            down='#eb4d5c',
            edge={'up': '#00a061', 'down': '#eb4d5c'},
            wick={'up': '#00a061', 'down': '#eb4d5c'},
            volume={'up': '#a3e2c5', 'down': '#f1c3c8'}
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
            xrotation=0
        )
        
        # Formátování x-osy
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        
    def add_support_zones(self, zones):
        """
        Přidá supportní zóny do grafu.
        
        Args:
            zones (list): Seznam zón jako (min, max) tuples
        """
        if not zones:
            return
            
        # Získání barevného schématu
        colors = get_color_scheme()
        support_colors = colors['support_zone_colors']
        
        # Vykreslení zón
        support_zone_added = draw_support_zones(self.ax1, zones, self.plot_data.index[0], support_colors)
        
        # Přidání do legendy
        if support_zone_added:
            self.legend_elements.append(Line2D([0], [0], color=support_colors[0], lw=4, label='Support Zone'))
            
    def add_resistance_zones(self, zones):
        """
        Přidá resistenční zóny do grafu.
        
        Args:
            zones (list): Seznam zón jako (min, max) tuples
        """
        if not zones:
            return
            
        # Získání barevného schématu
        colors = get_color_scheme()
        resistance_colors = colors['resistance_zone_colors']
        
        # Vykreslení zón
        resistance_zone_added = draw_resistance_zones(self.ax1, zones, self.plot_data.index[0], resistance_colors)
        
        # Přidání do legendy
        if resistance_zone_added:
            self.legend_elements.append(Line2D([0], [0], color=resistance_colors[0], lw=4, label='Resistance Zone'))
            
    def add_scenarios(self, scenarios):
        """
        Přidá scénáře do grafu.
        
        Args:
            scenarios (list): Seznam scénářů k vizualizaci
        """
        if not scenarios:
            return
            
        # Vykreslení scénářů s projekcí do budoucnosti
        bullish_added, bearish_added = draw_scenarios(
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
            
        # Přidání legendy
        if self.legend_elements:
            self.ax1.legend(
                handles=self.legend_elements, 
                loc='upper left', 
                fontsize=8, 
                framealpha=0.8, 
                ncol=len(self.legend_elements)
            )
