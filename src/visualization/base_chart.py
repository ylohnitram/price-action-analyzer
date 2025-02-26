import os
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from src.visualization.config.colors import get_color_scheme
from src.visualization.config.styles import get_chart_style
from src.visualization.config.timeframes import get_timeframe_config

logger = logging.getLogger(__name__)

class BaseChart:
    """Základní třída pro všechny typy grafů."""
    
    def __init__(self, df, symbol, timeframe=None, days_to_show=2, hours_to_show=None):
        """
        Inicializace základního grafu.
        
        Args:
            df (pandas.DataFrame): DataFrame s daty
            symbol (str): Obchodní symbol
            timeframe (str, optional): Časový rámec dat
            days_to_show (int, optional): Počet dní dat k zobrazení
            hours_to_show (int, optional): Počet hodin dat k zobrazení
        """
        self.df = df
        self.symbol = symbol
        self.timeframe = timeframe
        self.days_to_show = days_to_show
        self.hours_to_show = hours_to_show
        
        # Nastavení podle timeframe
        self.tf_config = get_timeframe_config(timeframe)
        
        # Připravení dat pro zobrazení
        self.prepare_data()
        
        # Inicializace grafu
        self.init_figure()
        
    def prepare_data(self):
        """Připraví data pro zobrazení."""
        # Kontrola DataFrame
        if not isinstance(self.df.index, pd.DatetimeIndex):
            self.df.index = pd.to_datetime(self.df.index)
            
        self.df.sort_index(inplace=True)
            
        # Limitace dat podle časového rozsahu
        end_date = self.df.index.max()
        
        if self.hours_to_show:
            start_date = end_date - timedelta(hours=self.hours_to_show)
        else:
            days_to_use = min(self.days_to_show, self.tf_config.get('max_days', 90))
            start_date = end_date - timedelta(days=days_to_use)
            
        self.plot_data = self.df[self.df.index >= start_date].copy()
        
        # Kontrola dostatku dat
        min_candles = self.tf_config.get('min_candles', 10)
        if len(self.plot_data) < min_candles:
            logger.warning(f"Not enough data ({len(self.plot_data)} candles) for {self.timeframe}. Using all available data.")
            self.plot_data = self.df.copy()
            
    def init_figure(self):
        """Inicializace figury a os."""
        # Nastavení velikosti a proporcí
        figsize = self.tf_config.get('figsize', (12, 8))
        height_ratios = self.tf_config.get('height_ratios', [4, 1])
        
        self.fig = plt.figure(figsize=figsize, dpi=100)
        self.gs = self.fig.add_gridspec(2, 1, height_ratios=height_ratios, hspace=0.05)
        self.ax1 = self.fig.add_subplot(self.gs[0, 0])  # Hlavní graf
        self.ax2 = self.fig.add_subplot(self.gs[1, 0], sharex=self.ax1)  # Volume
        
        # Přidání titulku
        title = f"{self.symbol} - {self.timeframe} Timeframe"
        if self.timeframe in ['1d', '1w']:
            title += " (Long-term Analysis)"
        elif self.timeframe in ['4h', '1h']:
            title += " (Medium-term Analysis)"
        else:
            title += " (Short-term Analysis)"
            
        self.ax1.set_title(title, fontsize=14, fontweight='bold')
        
        # Přidání informace o generování
        plt.figtext(
            0.01, 0.01,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            fontsize=7,
            bbox=dict(facecolor='white', alpha=0.8)
        )
    
    def add_support_zones(self, zones):
        """
        Přidá supportní zóny do grafu.
        
        Args:
            zones (list): Seznam zón jako (min, max) tuples
        """
        # Implementováno v podtřídách
        pass
        
    def add_resistance_zones(self, zones):
        """
        Přidá resistenční zóny do grafu.
        
        Args:
            zones (list): Seznam zón jako (min, max) tuples
        """
        # Implementováno v podtřídách
        pass
        
    def add_scenarios(self, scenarios):
        """
        Přidá scénáře do grafu.
        
        Args:
            scenarios (list): Seznam scénářů
        """
        # Implementováno v podtřídách
        pass
    
    def render(self, filename=None):
        """
        Vykreslí graf a uloží do souboru.
        
        Args:
            filename (str, optional): Cesta k souboru pro uložení grafu
            
        Returns:
            str: Cesta k vygenerovanému souboru nebo None v případě chyby
        """
        # Příprava jména souboru
        if not filename:
            charts_dir = "charts"
            os.makedirs(charts_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(charts_dir, f"{self.symbol}_{timestamp}.png")
        
        try:
            # Doladění rozložení
            plt.tight_layout(pad=1.0)
            
            # Uložení grafu
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close(self.fig)
            
            return filename
            
        except Exception as e:
            logger.error(f"Error generating chart: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return None
