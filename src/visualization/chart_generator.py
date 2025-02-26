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
            # Příprava dodatečných prvků pro vykreslení zón
            support_colors = []
            resistance_colors = []
            rect_collections = []
            
            # Zpracování zón podpory
            if support_zones:
                for i, (s_min, s_max) in enumerate(support_zones[:5]):
                    if np.isnan(s_min) or np.isnan(s_max):
                        continue
                    logger.info(f"Processing support zone {i+1}: {s_min}-{s_max}")
                    
                    # Vytvoření pole bodů pro supportní zónu
                    support_rect = dict(
                        y1=s_min, 
                        y2=s_max, 
                        facecolor='#90EE90', 
                        edgecolor='#006400',
                        alpha=0.6,
                        zorder=0
                    )
                    support_colors.append(support_rect)
            
            # Zpracování rezistenčních zón
            if resistance_zones:
                for i, (r_min, r_max) in enumerate(resistance_zones[:5]):
                    if np.isnan(r_min) or np.isnan(r_max):
                        continue
                    logger.info(f"Processing resistance zone {i+1}: {r_min}-{r_max}")
                    
                    # Vytvoření pole bodů pro rezistenční zónu
                    resistance_rect = dict(
                        y1=r_min, 
                        y2=r_max, 
                        facecolor='#FFB6C1', 
                        edgecolor='#8B0000',
                        alpha=0.6,
                        zorder=0
                    )
                    resistance_colors.append(resistance_rect)
                    
            # Sloučení všech zón
            rect_collections = support_colors + resistance_colors
            
            # Vytvoření aditec pro MPLFinance
            aditec = []
            if rect_collections:
                aditec.append(mpf.make_addplot([], type='rect', plot_ranges=rect_collections))

            # Úprava stylu pro lepší viditelnost zón
            mc = mpf.make_marketcolors(
                up='#00a061',           # Zelená svíčka nahoru
                down='#eb4d5c',         # Červená svíčka dolů
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
                y_on_right=False,
                facecolor='white'
            )

            # Vytvoření základního grafu se svíčkami a zónami
            fig, axes = mpf.plot(
                plot_data,
                type='candle',
                style=style,
                title=f"\n{symbol} ({timeframe}) - Price Action Analysis" if timeframe else f"\n{symbol} - Price Action Analysis",
                ylabel='Price',
                volume=True,
                figsize=(12, 8),
                returnfig=True,
                panel_ratios=(4, 1),
                tight_layout=False,
                addplot=aditec if aditec else None,
                warn_too_much_data=5000
            )

            ax = axes[0]
            ax2 = axes[2] if len(axes) > 2 else axes[1]
            
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

            # Úprava osy Y pro zahrnutí všech zón
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

            # Přidat popisky zón
            try:
                # Získání časového rozsahu pro umístění popisků
                start_x = mdates.date2num(plot_data.index[0])
                
                # Přidání popisků supportních zón
                if support_zones:
                    for i, (s_min, s_max) in enumerate(support_zones[:3]):  # Omezení na 3 popisky
                        if np.isnan(s_min) or np.isnan(s_max):
                            continue
                        mid_point = (s_min + s_max) / 2
                        ax.text(start_x, mid_point, 
                               f"S{i+1}", fontsize=8, color='darkgreen', 
                               ha='right', va='center', fontweight='bold',
                               bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0))

                # Přidání popisků rezistenčních zón
                if resistance_zones:
                    for i, (r_min, r_max) in enumerate(resistance_zones[:3]):  # Omezení na 3 popisky
                        if np.isnan(r_min) or np.isnan(r_max):
                            continue
                        mid_point = (r_min + r_max) / 2
                        ax.text(start_x, mid_point, 
                               f"R{i+1}", fontsize=8, color='darkred', 
                               ha='right', va='center', fontweight='bold',
                               bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=0))
            except Exception as label_error:
                logger.warning(f"Nepovedlo se přidat popisky zón: {str(label_error)}")

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
            plt.savefig(filename, dpi=150)
            plt.close(fig)
            logger.info(f"Graf uložen: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Chyba generování grafu: {str(e)}")
            try:
                # Fallback: Kombinovaný graf se svíčkami a čárami pro zóny
                from matplotlib.finance import candlestick_ohlc
                
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [3, 1]})
                
                # Převedení datetime indexu na čísla pro candlestick
                dates = mdates.date2num(plot_data.index.to_pydatetime())
                ohlc = np.column_stack((dates, 
                                        plot_data['open'].values,
                                        plot_data['high'].values, 
                                        plot_data['low'].values, 
                                        plot_data['close'].values))
                
                # Vykreslení svíček
                candlestick_ohlc(ax1, ohlc, width=0.6, colorup='green', colordown='red')
                
                # Formátování osy X
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
                ax1.set_title(f"{symbol} ({timeframe}) - Price Action Analysis")
                
                # Přidání zón podpory a rezistence
                if support_zones:
                    for i, (s_min, s_max) in enumerate(support_zones[:3]):
                        if np.isnan(s_min) or np.isnan(s_max):
                            continue
                        mid = (s_min + s_max) / 2
                        ax1.axhspan(s_min, s_max, alpha=0.3, color='green', label=f"Support {i+1}" if i==0 else "")
                
                if resistance_zones:
                    for i, (r_min, r_max) in enumerate(resistance_zones[:3]):
                        if np.isnan(r_min) or np.isnan(r_max):
                            continue
                        mid = (r_min + r_max) / 2
                        ax1.axhspan(r_min, r_max, alpha=0.3, color='red', label=f"Resistance {i+1}" if i==0 else "")
                
                # Objem
                ax2.bar(dates, plot_data['volume'].values, width=0.6, 
                       color=np.where(plot_data['close'].values >= plot_data['open'].values, 'green', 'red'))
                ax2.set_ylabel('Volume')
                
                # Sdílená osa X
                fig.autofmt_xdate()
                
                # Přidání legendy
                ax1.legend(loc='best')
                
                plt.tight_layout()
                plt.savefig(filename, dpi=150)
                plt.close(fig)
                logger.info(f"Záložní graf uložen: {filename}")
                return filename
                
            except Exception as fallback_error:
                # Nejjednodušší záložní řešení - pouze čárový graf
                try:
                    plt.figure(figsize=(10, 6))
                    plt.plot(plot_data.index, plot_data['close'], linewidth=1.5, color='navy')
                    plt.title(f"{symbol} ({timeframe}) - Price Action Analysis")
                    plt.grid(True, alpha=0.3)
                    
                    # Horizontální čáry pro zóny
                    if support_zones:
                        for i, (s_min, s_max) in enumerate(support_zones[:3]):
                            if np.isnan(s_min) or np.isnan(s_max):
                                continue
                            mid = (s_min + s_max) / 2
                            plt.axhline(y=mid, color='green', linestyle='--', alpha=0.5, 
                                       label=f"Support {i+1}" if i==0 else None)
                    
                    if resistance_zones:
                        for i, (r_min, r_max) in enumerate(resistance_zones[:3]):
                            if np.isnan(r_min) or np.isnan(r_max):
                                continue
                            mid = (r_min + r_max) / 2
                            plt.axhline(y=mid, color='red', linestyle='--', alpha=0.5, 
                                       label=f"Resistance {i+1}" if i==0 else None)
                    
                    plt.legend()
                    plt.savefig(filename, dpi=100)
                    plt.close()
                    logger.info(f"Jednoduchý záložní graf uložen: {filename}")
                    return filename
                    
                except Exception as final_error:
                    logger.error(f"Všechny pokusy o vytvoření grafu selhaly: {str(final_error)}")
                    return None
