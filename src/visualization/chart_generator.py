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
        
        Args:
            df (pandas.DataFrame): DataFrame s OHLCV daty
            support_zones (list): Seznam supportních zón [(min1, max1), (min2, max2), ...]
            resistance_zones (list): Seznam resistenčních zón [(min1, max1), (min2, max2), ...]
            symbol (str): Obchodní symbol pro titulek grafu
            filename (str, optional): Vlastní název výstupního souboru
            days_to_show (int, optional): Počet dní dat k zobrazení
            hours_to_show (int, optional): Počet hodin dat k zobrazení (má přednost před days_to_show)
            timeframe (str, optional): Časový rámec pro zobrazení v titulku grafu
            
        Returns:
            str: Cesta k vygenerovanému grafu nebo None při chybě
        """
        # Debug: Kontrola vstupních zón
        logger.debug(f"Support zones: {support_zones}")
        logger.debug(f"Resistance zones: {resistance_zones}")

        # Nastavení cesty a adresáře
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
    
        # Fallback pro málo dat
        if len(plot_data) < 10:
            logger.warning("Používám všechna dostupná data")
            plot_data = df.copy()

        # Příprava stylu
        plt.style.use('ggplot')
        plt.rcParams.update({
            'font.family': 'DejaVu Sans',
            'font.size': 9,
            'axes.titlesize': 10,
            'axes.labelpad': 2
        })

        try:
            # Vytvoření základního grafu
            fig, axes = mpf.plot(
                plot_data,
                type='candle',
                style='yahoo',
                title=f"\n{symbol} ({timeframe}) - Price Action Analysis" if timeframe else f"\n{symbol} - Price Action Analysis",
                ylabel='Price',
                volume=True,
                figsize=(12, 8),
                returnfig=True,
                panel_ratios=(4,1),
                tight_layout=False,
                update_width_config=dict(candle_linewidth=0.8),
                warn_too_much_data=5000
            )

            ax = axes[0]
            ax2 = axes[2] if len(axes) > 2 else axes[1]

            # Přidání support zón
            for s_min, s_max in support_zones[:5]:  # Omezení na 5 zón
                rect = Rectangle(
                    (mdates.date2num(plot_data.index[0]), s_min),
                    mdates.date2num(plot_data.index[-1]) - mdates.date2num(plot_data.index[0]),
                    s_max - s_min,
                    facecolor='#90EE90',
                    alpha=0.4,
                    edgecolor='#006400',
                    linewidth=0.8,
                    zorder=0
                )
                ax.add_patch(rect)

            # Přidání resistance zón
            for r_min, r_max in resistance_zones[:5]:  # Omezení na 5 zón
                rect = Rectangle(
                    (mdates.date2num(plot_data.index[0]), r_min),
                    mdates.date2num(plot_data.index[-1]) - mdates.date2num(plot_data.index[0]),
                    r_max - r_min,
                    facecolor='#FFB6C1',
                    alpha=0.4,
                    edgecolor='#8B0000',
                    linewidth=0.8,
                    zorder=0
                )
                ax.add_patch(rect)

            # Dynamické formátování osy X
            if timeframe in ['5m', '15m', '30m']:
                locator = mdates.HourLocator(interval=2)
                formatter = mdates.DateFormatter('%H:%M\n%d.%m')
            elif timeframe in ['1h', '4h']:
                locator = mdates.DayLocator()
                formatter = mdates.DateFormatter('%d.%m')
            else:
                locator = mdates.AutoDateLocator()
                formatter = mdates.DateFormatter('%d.%m')

            ax.xaxis.set_major_locator(locator)
            ax.xaxis.set_major_formatter(formatter)
            plt.xticks(rotation=35, ha='right', fontsize=8)

            # Úprava osy Y
            # 1. Převod všech cenových dat na numpy array
            price_lows = plot_data['low'].values
            price_highs = plot_data['high'].values
            all_prices = np.concatenate([price_lows, price_highs])

            # 2. Bezpečné zpracování zón
            zone_values = np.array([])
            if support_zones:
                zone_values = np.append(zone_values, np.array(support_zones).flatten())
            if resistance_zones:
                zone_values = np.append(zone_values, np.array(resistance_zones).flatten())

            # 3. Kombinace dat s kontrolou existence
            if zone_values.size > 0:
                combined_data = np.concatenate([all_prices, zone_values])
            else:
                combined_data = all_prices

            # 4. Výpočet min/max s ochranou proti prázdným datům
            y_min = np.min(combined_data) * 0.999 if combined_data.size > 0 else np.min(price_lows)
            y_max = np.max(combined_data) * 1.001 if combined_data.size > 0 else np.max(price_highs)

            # Úprava volumenu
            ax2.set_ylabel('Volume', fontsize=8)
            ax2.tick_params(axis='y', labelsize=7)
            ax2.grid(False)
            ax2.set_facecolor('#f5f5f5')

            # Vodoznak a úpravy layoutu
            plt.figtext(0.01, 0.01, 
                       f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                       fontsize=7,
                       backgroundcolor='white',
                       bbox=dict(facecolor='white', alpha=0.8, pad=2, edgecolor='lightgray'))
        
            plt.subplots_adjust(bottom=0.18, hspace=0.15, right=0.95, top=0.92)

            # Uložení
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Graf uložen: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Chyba generování grafu: {str(e)}")
            try:
                # Fallback: Základní čárový graf
                plt.figure(figsize=(12, 6))
                plt.plot(plot_data.index, plot_data['close'], linewidth=1, color='navy')
                plt.title(f"{symbol} - Line Chart")
                plt.grid(True, alpha=0.3)
                plt.savefig(filename, dpi=150)
                plt.close()
                return filename
            except Exception as fallback_error:
                logger.error(f"Záložní graf selhal: {str(fallback_error)}")
                return None
