#!/usr/bin/env python3

# Nastavení Agg backend pro matplotlib - musí být před importem pyplot
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend pro lepší výkon

from datetime import datetime, timedelta
import os
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import logging

logger = logging.getLogger(__name__)

class ChartGenerator:
    """Třída pro generování cenových grafů s technickými prvky."""

    def generate_chart(self, df, support_zones, resistance_zones, symbol, filename=None, 
                   days_to_show=2, hours_to_show=None, timeframe=None):
        """
        Generuje svíčkový graf s cenovými zónami.
        """
        # Základní setup
        logger.info(f"Generating chart for {symbol} ({timeframe})")
        charts_dir = "charts"
        os.makedirs(charts_dir, exist_ok=True)
    
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(charts_dir, f"{symbol}_{timestamp}.png")

        # Omezení datového rozsahu
        end_date = df.index.max()
        if hours_to_show:
            start_date = end_date - timedelta(hours=hours_to_show)
        else:
            start_date = end_date - timedelta(days=days_to_show)
    
        plot_data = df[df.index >= start_date].copy()
        
        if len(plot_data) < 10:
            plot_data = df.copy()
            
        # Styl svíček
        mc = mpf.make_marketcolors(
            up='#00a061',         
            down='#eb4d5c',       
            edge={'up': '#00a061', 'down': '#eb4d5c'},
            wick={'up': '#00a061', 'down': '#eb4d5c'},
            volume={'up': '#a3e2c5', 'down': '#f1c3c8'}
        )
        style = mpf.make_mpf_style(
            base_mpf_style='yahoo',
            marketcolors=mc,
            gridstyle='-',
            gridcolor='#e6e6e6',
            gridaxis='both',
            facecolor='white'
        )
        
        try:
            # Základní graf
            fig = plt.figure(figsize=(12, 8))
            gs = fig.add_gridspec(5, 1)  # 5 rows, 1 column
            ax1 = fig.add_subplot(gs[0:4, 0])  # První 4 řádky pro cenový graf
            ax2 = fig.add_subplot(gs[4, 0], sharex=ax1)  # Poslední řádek pro volume
            
            # Kreslení svíček
            mpf.plot(plot_data, ax=ax1, volume=ax2, type='candle', style=style)
            
            # Přidání zón podpory/rezistence
            for i, (s_min, s_max) in enumerate(support_zones[:5] if support_zones else []):
                if not (np.isnan(s_min) or np.isnan(s_max)):
                    ax1.axhspan(s_min, s_max, facecolor='#90EE90', edgecolor='#006400', 
                                alpha=0.4, linewidth=1.0, zorder=0)
                    if i < 3:
                        mid_point = (s_min + s_max) / 2
                        ax1.text(plot_data.index[0], mid_point, f"S{i+1}", fontsize=8, color='darkgreen',
                                ha='right', va='center', fontweight='bold',
                                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0))
            
            for i, (r_min, r_max) in enumerate(resistance_zones[:5] if resistance_zones else []):
                if not (np.isnan(r_min) or np.isnan(r_max)):
                    ax1.axhspan(r_min, r_max, facecolor='#FFB6C1', edgecolor='#8B0000', 
                                alpha=0.4, linewidth=1.0, zorder=0)
                    if i < 3:
                        mid_point = (r_min + r_max) / 2
                        ax1.text(plot_data.index[0], mid_point, f"R{i+1}", fontsize=8, color='darkred',
                                ha='right', va='center', fontweight='bold',
                                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0))
            
            # Formátování osy X podle časového rámce - JEDNODUŠE A ČITELNĚ
            if timeframe == '5m':
                # Každé 4 hodiny jen s hodinou
                ax1.xaxis.set_major_locator(mdates.HourLocator(interval=4))
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H'))
                
                # Menší značky pro hodiny mezi tím
                ax1.xaxis.set_minor_locator(mdates.HourLocator())
                
                # Zvýrazněné datum pro změnu dne
                day_locator = mdates.DayLocator()
                for tick in day_locator.tick_values(plot_data.index[0], plot_data.index[-1]):
                    date = mdates.num2date(tick)
                    if date >= plot_data.index[0] and date <= plot_data.index[-1]:
                        ax1.axvline(date, color='gray', linestyle='-', alpha=0.3)
                        ax1.text(date, ax1.get_ylim()[1], date.strftime('%d.%m'), 
                                ha='center', va='bottom', fontsize=9, fontweight='bold',
                                bbox=dict(facecolor='white', alpha=0.8, pad=1))
                
            elif timeframe == '30m':
                # Pro 30m - každé 4 hodiny jen s hodinou
                ax1.xaxis.set_major_locator(mdates.HourLocator(interval=4))
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H'))
                
                # Zvýrazněné datum pro změnu dne
                day_locator = mdates.DayLocator()
                for tick in day_locator.tick_values(plot_data.index[0], plot_data.index[-1]):
                    date = mdates.num2date(tick)
                    if date >= plot_data.index[0] and date <= plot_data.index[-1]:
                        ax1.axvline(date, color='gray', linestyle='-', alpha=0.3)
                        ax1.text(date, ax1.get_ylim()[1], date.strftime('%d.%m'), 
                                ha='center', va='bottom', fontsize=9, fontweight='bold',
                                bbox=dict(facecolor='white', alpha=0.8, pad=1))
                                
            elif timeframe == '4h':
                # Pro 4h - jen dny
                ax1.xaxis.set_major_locator(mdates.DayLocator())
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
                
            elif timeframe == '1d':
                # Pro 1d - týdenní intervaly
                ax1.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
                
            elif timeframe == '1w':
                # Pro 1w - měsíční
                ax1.xaxis.set_major_locator(mdates.MonthLocator())
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%y'))
            
            # Odstraněný popisky X-osy z volume grafu, ale zachovat mřížku
            ax2.set_xlabel('')
            ax2.set_xticklabels([])
            
            # Zachovat viditelné hlavní popisky
            ax1.xaxis.set_tick_params(which='major', length=6, labelsize=9)
            
            # Nastavení títulku
            fig.suptitle(f"{symbol} ({timeframe}) - Price Action Analysis", fontsize=12, y=0.95)
            
            # Popisky os
            ax1.set_ylabel('Price', fontsize=10)
            ax2.set_ylabel('Volume', fontsize=8)
            
            # Vodoznak
            plt.figtext(0.01, 0.01, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                       fontsize=7, backgroundcolor='white',
                       bbox=dict(facecolor='white', alpha=0.8, pad=2, edgecolor='lightgray'))
            
            # Upravit rozložení
            plt.tight_layout()
            plt.subplots_adjust(hspace=0)
            
            # Uložení
            plt.savefig(filename, dpi=150)
            plt.close(fig)
            logger.info(f"Graf uložen: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Chyba generování grafu: {str(e)}")
            
            # Jednoduchý fallback
            try:
                plt.figure(figsize=(10, 6))
                plt.plot(plot_data.index, plot_data['close'], linewidth=1.5, color='navy')
                plt.title(f"{symbol} ({timeframe}) - Line Chart")
                plt.grid(True, alpha=0.3)
                
                # Jednoduché popisky
                if timeframe in ['5m', '30m']:
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                    plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=4))
                else:
                    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
                    plt.gca().xaxis.set_major_locator(mdates.DayLocator())
                
                plt.xticks(rotation=0)
                plt.tight_layout()
                plt.savefig(filename, dpi=100)
                plt.close()
                return filename
                
            except Exception as final_error:
                logger.error(f"Všechny pokusy o vytvoření grafu selhaly: {str(final_error)}")
                return None
