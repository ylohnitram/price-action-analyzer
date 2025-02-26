#!/usr/bin/env python3

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for rendering charts
from datetime import datetime, timedelta
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter
import logging

logger = logging.getLogger(__name__)

class ChartGenerator:
    """Class for generating candlestick charts with support and resistance zones."""

    def generate_chart(self, df, support_zones, resistance_zones, symbol, filename=None,
                       days_to_show=2, hours_to_show=None, timeframe=None):
        """
        Generates a candlestick chart with support and resistance zones.
        """
        # Setup directories and filename
        logger.info(f"Generating chart for {symbol} ({timeframe})")
        charts_dir = "charts"
        os.makedirs(charts_dir, exist_ok=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(charts_dir, f"{symbol}_{timestamp}.png")

        # Ensure the dataframe has the required columns for mplfinance (OHLCV)
        required_columns = {'open', 'high', 'low', 'close', 'volume'}
        if not required_columns.issubset(df.columns):
            logger.error("Dataframe does not contain the required OHLCV columns.")
            return None

        # Limit the data range to display
        end_date = df.index.max()
        if hours_to_show:
            start_date = end_date - timedelta(hours=hours_to_show)
        else:
            start_date = end_date - timedelta(days=days_to_show)
        plot_data = df[df.index >= start_date].copy()
        
        if len(plot_data) < 10:
            plot_data = df.copy()

        # Define candlestick style
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
            # Create the figure and subplots
            fig = plt.figure(figsize=(12, 8))
            gs = fig.add_gridspec(5, 1)
            ax1 = fig.add_subplot(gs[0:4, 0])  # Main price chart
            ax2 = fig.add_subplot(gs[4, 0], sharex=ax1)  # Volume chart

            # Plot candlesticks and volume bars
            mpf.plot(plot_data, ax=ax1, volume=ax2, type='candle', style=style)

            # Move price values back to the right side and keep "Price" label on the left side
            ax1.yaxis.tick_right()
            ax1.yaxis.set_label_position("right")
            ax1.set_ylabel('Price', fontsize=10)

            # Move volume values to the right side and keep "Volume" label on the left side
            ax2.yaxis.tick_right()
            ax2.yaxis.set_label_position("right")
            ax2.set_ylabel('Volume', fontsize=8)

            # Automatic formatting of the time axis
            locator = AutoDateLocator()
            ax1.xaxis.set_major_locator(locator)
            ax1.xaxis.set_major_formatter(ConciseDateFormatter(locator))

            # Rotate X-axis labels for better readability
            plt.xticks(rotation=45, ha='right', rotation_mode='anchor')
            
            # Set X-axis limits based on data range
            ax1.set_xlim(plot_data.index[0], plot_data.index[-1])

            # Add support and resistance zones without numbers (only "S" or "R")
            for s_min, s_max in (support_zones or []):
                if not (np.isnan(s_min) or np.isnan(s_max)):
                    ax1.axhspan(s_min, s_max, facecolor='#90EE90', edgecolor='#006400', alpha=0.4)
                    mid_point = (s_min + s_max) / 2
                    ax1.text(plot_data.index[0], mid_point, "S",
                             fontsize=8, color='darkgreen', ha='right', va='center',
                             fontweight='bold', bbox=dict(facecolor='white', alpha=0.7))

            for r_min, r_max in (resistance_zones or []):
                if not (np.isnan(r_min) or np.isnan(r_max)):
                    ax1.axhspan(r_min, r_max, facecolor='#FFB6C1', edgecolor='#8B0000', alpha=0.4)
                    mid_point = (r_min + r_max) / 2
                    ax1.text(plot_data.index[0], mid_point, "R",
                             fontsize=8, color='darkred', ha='right', va='center',
                             fontweight='bold', bbox=dict(facecolor='white', alpha=0.7))

            # Adjust layout for better readability
            plt.subplots_adjust(bottom=0.15, hspace=0.05)

            # Add a watermark with generation time
            plt.figtext(0.01, 0.01,
                        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        fontsize=7, backgroundcolor='white',
                        bbox=dict(facecolor='white', alpha=0.8))

            # Save the chart to file
            plt.savefig(filename, dpi=150)
            plt.close(fig)

            logger.info(f"Chart saved: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error generating chart: {str(e)}")
