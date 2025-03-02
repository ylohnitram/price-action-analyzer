#!/usr/bin/env python3

import matplotlib
# Nastavení neinteraktivního backend před importem pyplot
matplotlib.use('Agg')

import os
import logging
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from src.visualization.config.colors import get_color_scheme
from src.visualization.config.styles import get_chart_style
from src.visualization.config.timeframes import get_timeframe_config

logger = logging.getLogger(__name__)

class BaseChart:
    """Základní třída pro všechny typy grafů."""
    
    def __init__(self, df, symbol, timeframe=None, days_to_show=5, hours_to_show=None):
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
        
        # Získání barevného schématu
        self.colors = get_color_scheme()
        
        # Připravení dat pro zobrazení
        self.prepare_data()
        
        # Inicializace grafu
        self.init_figure()
        
    def prepare_data(self):
        """Připraví data pro zobrazení."""
        try:
            # Kontrola DataFrame
            if self.df is None or len(self.df) == 0:
                raise ValueError("Vstupní DataFrame je prázdný")
                
            if not isinstance(self.df.index, pd.DatetimeIndex):
                logger.info("Převádím index na datetime")
                self.df.index = pd.to_datetime(self.df.index)
                
            self.df.sort_index(inplace=True)
            
            # Standardizace názvů sloupců
            column_map = {
                'open': 'Open', 'high': 'High', 'low': 'Low', 
                'close': 'Close', 'volume': 'Volume'
            }
            
            df_copy = self.df.copy()
            
            # Zachování původních názvů sloupců
            for old_col, new_col in column_map.items():
                if old_col in df_copy.columns and new_col not in df_copy.columns:
                    df_copy[new_col] = df_copy[old_col]
                    logger.info(f"Mapování sloupce {old_col} na {new_col}")
            
            # Kontrola, zda máme všechny potřebné sloupce
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_columns = [col for col in required_columns if col not in df_copy.columns]
            
            if missing_columns:
                logger.warning(f"Chybí sloupce v dataframe: {missing_columns}")
                
                # Vytvoření chybějících sloupců
                if 'Open' not in df_copy.columns and 'Close' in df_copy.columns:
                    df_copy['Open'] = df_copy['Close']
                    logger.info("Vytvořen sloupec Open z Close")
                    
                if 'High' not in df_copy.columns and 'Close' in df_copy.columns:
                    df_copy['High'] = df_copy['Close'] * 1.001  # Mírně vyšší než Close
                    logger.info("Vytvořen sloupec High z Close")
                    
                if 'Low' not in df_copy.columns and 'Close' in df_copy.columns:
                    df_copy['Low'] = df_copy['Close'] * 0.999   # Mírně nižší než Close
                    logger.info("Vytvořen sloupec Low z Close")
                    
                if 'Close' not in df_copy.columns and 'Open' in df_copy.columns:
                    df_copy['Close'] = df_copy['Open']
                    logger.info("Vytvořen sloupec Close z Open")
                    
                if 'Volume' not in df_copy.columns:
                    df_copy['Volume'] = 0
                    logger.info("Vytvořen sloupec Volume s nulovými hodnotami")
            
            # Ověření, že DataFrame má všechny potřebné sloupce po úpravách
            for col in required_columns:
                if col not in df_copy.columns:
                    logger.error(f"Sloupec {col} stále chybí po úpravách")
                
            # Limitace dat podle časového rozsahu
            end_date = df_copy.index.max()
            
            if self.hours_to_show:
                start_date = end_date - timedelta(hours=self.hours_to_show)
                logger.info(f"Používám {self.hours_to_show} hodin dat")
            else:
                days_to_use = min(self.days_to_show, self.tf_config.get('max_days', 90))
                start_date = end_date - timedelta(days=days_to_use)
                logger.info(f"Používám {days_to_use} dní dat")
                
            filtered_data = df_copy[df_copy.index >= start_date].copy()
            
            # Kontrola dostatku dat
            min_candles = self.tf_config.get('min_candles', 10)
            if len(filtered_data) < min_candles:
                logger.warning(f"Not enough data ({len(filtered_data)} candles) for {self.timeframe}. Using all available data.")
                self.plot_data = df_copy.copy()
            else:
                self.plot_data = filtered_data
                
            # Ověření, že máme indexy správně setříděné
            self.plot_data = self.plot_data.sort_index()
            
            # Konverze číselných sloupců na float
            for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
                if col in self.plot_data.columns:
                    self.plot_data[col] = self.plot_data[col].astype(float)
            
            # Poslední kontrola dat
            logger.info(f"Připraveno {len(self.plot_data)} svíček pro graf od {self.plot_data.index[0]} do {self.plot_data.index[-1]}")
            
        except Exception as e:
            logger.error(f"Chyba při přípravě dat: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Vytvoříme alespoň jeden základní záznam pro kritický případ
            logger.warning("Vytvářím základní DataFrame pro záchranu")
            index = pd.DatetimeIndex([datetime.now()])
            self.plot_data = pd.DataFrame({
                'Open': [100], 'High': [105], 'Low': [95], 'Close': [101], 'Volume': [1000]
            }, index=index)
    
    def init_figure(self):
        """Inicializace figury a os."""
        try:
            # Nastavení velikosti a proporcí
            figsize = self.tf_config.get('figsize', (12, 8))
            height_ratios = self.tf_config.get('height_ratios', [4, 1])
            
            self.fig = plt.figure(figsize=figsize, dpi=100)
            self.gs = self.fig.add_gridspec(2, 1, height_ratios=height_ratios, hspace=0.3)  # Větší mezera
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
            
            # Nastavení popisků os
            self.ax1.set_ylabel('Price', fontsize=12)
            self.ax2.set_ylabel('Volume', fontsize=12)
            
            # Přidání informace o generování
            plt.figtext(
                0.01, 0.01,
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                fontsize=8,
                bbox=dict(facecolor='white', alpha=0.8)
            )
            
            # Nastavení limitů osy Y pro volume
            self.ax2.set_ylim(0, None)  # Minimální hodnota 0, maximum automaticky
            
        except Exception as e:
            logger.error(f"Chyba při inicializaci grafu: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
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
        try:
            # Příprava jména souboru
            if not filename:
                charts_dir = "charts"
                os.makedirs(charts_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(charts_dir, f"{self.symbol}_{self.timeframe}_{timestamp}.png")
            
            # Nastavení správných formátů pro osy
            # Skip tight_layout which can cause warnings with unsupported plot types
            # plt.tight_layout()
            
            # Uložení grafu
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close(self.fig)
            
            logger.info(f"Graf úspěšně uložen: {filename}")
            return filename
                
        except Exception as e:
            logger.error(f"Error generating chart: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
                
            return None
