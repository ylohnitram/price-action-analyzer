#!/usr/bin/env python3

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend pro lepší výkon
from datetime import datetime, timedelta
import os
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter
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
            gs = fig.add_gridspec(5, 1)  # 5 řádků, 1 sloupec
            ax1 = fig.add_subplot(gs[0:4, 0])  # První 4 řádky pro cenový graf
            ax2 = fig.add_subplot(gs[4, 0], sharex=ax1)  # Poslední řádek pro objemy

            # Kreslení svíček a objemů
            mpf.plot(plot_data, ax=ax1, volume=ax2, type='candle', style=style)

            # Přesun hodnot ceny na levou stranu
            ax1.yaxis.tick_left()
            ax1.yaxis.set_label_position("left")
            
            # Automatické formátování časové osy
            locator = AutoDateLocator()
            ax1.xaxis.set_major_locator(locator)
            ax1.xaxis.set_major_formatter(
                ConciseDateFormatter(locator)
            )

            # Rotace a zarovnání popisků osy X
            plt.xticks(rotation=45, ha='right', rotation_mode='anchor')
            
            # Nastavení mezí osy X podle dat
            ax1.set_xlim(plot_data.index[0], plot_data.index[-1])

            # Nastavení gridu
            ax1.grid(True, linestyle='--', alpha=0.7)
            ax1.grid(which='minor', alpha=0.4, linestyle=':')

            # Přidání zón podpory/rezistence s číslováním od 1
            for i, (s_min, s_max) in enumerate(support_zones[:5] if support_zones else []):
                if not (np.isnan(s_min) or np.isnan(s_max)):
                    ax1.axhspan(s_min, s_max, facecolor='#90EE90', edgecolor='#006400',
                                alpha=0.4, linewidth=1.0, zorder=0)
                    mid_point = (s_min + s_max) / 2
                    ax1.text(plot_data.index[0], mid_point, f"S{i+1}", fontsize=8, color='darkgreen',
                             ha='right', va='center', fontweight='bold',
                             bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0))

            for i, (r_min, r_max) in enumerate(resistance_zones[:5] if resistance_zones else []):
                if not (np.isnan(r_min) or np.isnan(r_max)):
                    ax1.axhspan(r_min, r_max, facecolor='#FFB6C1', edgecolor='#8B0000',
                                alpha=0.4, linewidth=1.0, zorder=0)
                    mid_point = (r_min + r_max) / 2
                    ax1.text(plot_data.index[0], mid_point, f"R{i+1}", fontsize=8, color='darkred',
                             ha='right', va='center', fontweight='bold',
                             bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0))

            # Popisky os
            ax1.set_ylabel('Price', fontsize=10)
            ax2.set_ylabel('Volume', fontsize=8)

            # Úprava layoutu pro lepší čitelnost
            plt.subplots_adjust(bottom=0.15, hspace=0.05)
            
            # Vodoznak s časem generování grafu
            plt.figtext(0.01, 0.01, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                        fontsize=7, backgroundcolor='white',
                        bbox=dict(facecolor='white', alpha=0.8, pad=2, edgecolor='lightgray'))

            # Uložení grafu do souboru
            plt.savefig(filename, dpi=150)
            plt.close(fig)
            
            logger.info(f"Graf uložen: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Chyba generování grafu: {str(e)}")

