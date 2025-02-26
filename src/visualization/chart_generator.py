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
        # Podrobné logování vstupních dat
        logger.info(f"Generating chart for {symbol} ({timeframe})")
        logger.info(f"Support zones: {support_zones}")
        logger.info(f"Resistance zones: {resistance_zones}")

        # Ověření dat zón pro lepší diagnostiku
        if not support_zones:
            logger.warning("No support zones detected for display")
        if not resistance_zones:
            logger.warning("No resistance zones detected for display")

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
            
        # Logování rozsahu cen pro kontrolu viditelnosti zón
        price_min = plot_data['low'].min()
        price_max = plot_data['high'].max()
        logger.info(f"Price range in data: {price_min} - {price_max}")

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
            
            # Konvertujeme časové indexy pouze jednou pro všechny obdélníky
            # Tím zabráníme opakovanému konvertování, které může způsobit problémy s přesností
            start_x = mdates.date2num(plot_data.index[0])
            end_x = mdates.date2num(plot_data.index[-1])
            width_x = end_x - start_x
            
            # Explicitně ověříme, zda šířka obdélníku není příliš velká
            if width_x > 65000:  # Preventivní omezení pro zabránění chyby překročení limitů obrázku
                logger.warning(f"Date range too large: {width_x}, limiting width")
                width_x = 65000
                
            # Vylepšené vykreslování supportních zón
            if support_zones:
                for i, (s_min, s_max) in enumerate(support_zones[:5]):  # Omezení na 5 zón
                    try:
                        # Kontrola zda jsou hodnoty validní
                        if np.isnan(s_min) or np.isnan(s_max):
                            logger.warning(f"Ignoring invalid support zone: ({s_min}, {s_max})")
                            continue
                            
                        # Logování jednotlivých vykreslovaných zón
                        logger.info(f"Drawing support zone {i+1}: {s_min}-{s_max}")
                        
                        rect = Rectangle(
                            (start_x, s_min),
                            width_x,
                            s_max - s_min,
                            facecolor='#90EE90',
                            alpha=0.6,  # Zvýšeno pro lepší viditelnost
                            edgecolor='#006400',
                            linewidth=1.2,  # Zvýšeno pro lepší viditelnost
                            zorder=0
                        )
                        ax.add_patch(rect)
                    except Exception as ze:
                        logger.error(f"Error drawing support zone {i+1}: {ze}")

            # Vylepšené vykreslování rezistenčních zón
            if resistance_zones:
                for i, (r_min, r_max) in enumerate(resistance_zones[:5]):  # Omezení na 5 zón
                    try:
                        # Kontrola zda jsou hodnoty validní
                        if np.isnan(r_min) or np.isnan(r_max):
                            logger.warning(f"Ignoring invalid resistance zone: ({r_min}, {r_max})")
                            continue
                            
                        # Logování jednotlivých vykreslovaných zón
                        logger.info(f"Drawing resistance zone {i+1}: {r_min}-{r_max}")
                        
                        rect = Rectangle(
                            (start_x, r_min),
                            width_x,
                            r_max - r_min,
                            facecolor='#FFB6C1',
                            alpha=0.6,  # Zvýšeno pro lepší viditelnost
                            edgecolor='#8B0000',
                            linewidth=1.2,  # Zvýšeno pro lepší viditelnost
                            zorder=0
                        )
                        ax.add_patch(rect)
                    except Exception as ze:
                        logger.error(f"Error drawing resistance zone {i+1}: {ze}")

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

            # 2. Bezpečné zpracování zón s validací
            zone_values = np.array([])
            if support_zones:
                valid_supports = np.array([z for z in support_zones if not np.isnan(z[0]) and not np.isnan(z[1])])
                if valid_supports.size > 0:
                    zone_values = np.append(zone_values, valid_supports.flatten())
            
            if resistance_zones:
                valid_resistances = np.array([z for z in resistance_zones if not np.isnan(z[0]) and not np.isnan(z[1])])
                if valid_resistances.size > 0:
                    zone_values = np.append(zone_values, valid_resistances.flatten())

            # 3. Kombinace dat s kontrolou existence
            if zone_values.size > 0:
                combined_data = np.concatenate([all_prices, zone_values])
                # Rozšířit rozsah lehce pro zahrnutí všech zón
                y_min = np.min(combined_data) * 0.998
                y_max = np.max(combined_data) * 1.002
            else:
                y_min = np.min(price_lows) * 0.998
                y_max = np.max(price_highs) * 1.002
            
            # Explicitně nastavit rozsah osy Y, aby byly vidět všechny zóny
            logger.info(f"Setting Y-axis range to: {y_min} - {y_max}")
            ax.set_ylim(y_min, y_max)

            # Explicitně nastavit rozsah osy X, aby nedocházelo k příliš širokým obrázkům
            ax.set_xlim(start_x, end_x)

            # Úprava volumenu
            ax2.set_ylabel('Volume', fontsize=8)
            ax2.tick_params(axis='y', labelsize=7)
            ax2.grid(False)
            ax2.set_facecolor('#f5f5f5')

            # Přidat popisky zón - volitelné pro lepší čitelnost
            if support_zones:
                for i, (s_min, s_max) in enumerate(support_zones[:3]):  # Omezení na 3 popisky
                    if np.isnan(s_min) or np.isnan(s_max):
                        continue
                    mid_point = (s_min + s_max) / 2
                    ax.text(start_x, mid_point, 
                           f"S{i+1}", fontsize=8, color='darkgreen', 
                           ha='right', va='center', fontweight='bold',
                           bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0))

            if resistance_zones:
                for i, (r_min, r_max) in enumerate(resistance_zones[:3]):  # Omezení na 3 popisky
                    if np.isnan(r_min) or np.isnan(r_max):
                        continue
                    mid_point = (r_min + r_max) / 2
                    ax.text(start_x, mid_point, 
                           f"R{i+1}", fontsize=8, color='darkred', 
                           ha='right', va='center', fontweight='bold',
                           bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0))

            # Vodoznak a úpravy layoutu
            plt.figtext(0.01, 0.01, 
                       f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                       fontsize=7,
                       backgroundcolor='white',
                       bbox=dict(facecolor='white', alpha=0.8, pad=2, edgecolor='lightgray'))
        
            plt.subplots_adjust(bottom=0.18, hspace=0.15, right=0.95, top=0.92)

            # Nastavení limitů DPI a velikosti pro plátno
            # Toto pomáhá předejít chybě s příliš velkým obrázkem
            fig.set_dpi(150)
            fig.set_size_inches(12, 8)

            # Uložení s explicitním nastavením DPI a bez bbox_inches='tight', který může způsobit problémy
            plt.savefig(filename, dpi=150)
            plt.close(fig)
            logger.info(f"Graf uložen: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Chyba generování grafu: {str(e)}")
            try:
                # Fallback: Jednoduchý čárový graf s menšími požadavky na paměť
                plt.figure(figsize=(10, 6), dpi=100)
                plt.plot(plot_data.index, plot_data['close'], linewidth=1, color='navy')
                plt.title(f"{symbol} - Line Chart")
                plt.grid(True, alpha=0.3)
                
                # Vykreslení podpor a rezistencí jako horizontální čáry
                if support_zones:
                    for i, (s_min, s_max) in enumerate(support_zones[:3]):
                        if np.isnan(s_min) or np.isnan(s_max):
                            continue
                        mid_point = (s_min + s_max) / 2
                        plt.axhline(y=mid_point, color='green', linestyle='--', alpha=0.5, 
                                   label=f"Support {i+1}" if i == 0 else None)
                        
                if resistance_zones:
                    for i, (r_min, r_max) in enumerate(resistance_zones[:3]):
                        if np.isnan(r_min) or np.isnan(r_max):
                            continue
                        mid_point = (r_min + r_max) / 2
                        plt.axhline(y=mid_point, color='red', linestyle='--', alpha=0.5, 
                                   label=f"Resistance {i+1}" if i == 0 else None)
                
                plt.savefig(filename, dpi=100)
                plt.close()
                logger.info(f"Záložní graf uložen: {filename}")
                return filename
            except Exception as fallback_error:
                logger.error(f"Záložní graf selhal: {str(fallback_error)}")
                return None
