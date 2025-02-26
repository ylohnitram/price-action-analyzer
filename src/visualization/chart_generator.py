#!/usr/bin/env python3

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for rendering charts
from datetime import datetime, timedelta
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
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
        if not required_columns.issubset(df.columns.str.lower()):
            logger.error("Dataframe does not contain the required OHLCV columns.")
            return None

        # Rename columns to match mplfinance requirements
        df = df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })

        # Ensure the index is in datetime format and sorted
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)

        # Limit the data range to display
        end_date = df.index.max()
        if hours_to_show:
            start_date = end_date - timedelta(hours=hours_to_show)
        else:
            start_date = end_date - timedelta(days=days_to_show)
        plot_data = df[df.index >= start_date].copy()
        
        if len(plot_data) < 10:
            logger.warning("Not enough data to generate a meaningful chart. Using all available data.")
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
            # Create additional plots for S/R zones
            add_plots = []
            
            # Add support zones (green rectangles)
            for s_min, s_max in (support_zones or []):
                if not (np.isnan(s_min) or np.isnan(s_max)):
                    add_plots.append(mpf.make_addplot(
                        [s_min] * len(plot_data), color='green', alpha=0.3))
                    add_plots.append(mpf.make_addplot(
                        [s_max] * len(plot_data), color='green', alpha=0.3))

            # Add resistance zones (red rectangles)
            for r_min, r_max in (resistance_zones or []):
                if not (np.isnan(r_min) or np.isnan(r_max)):
                    add_plots.append(mpf.make_addplot(
                        [r_min] * len(plot_data), color='red', alpha=0.3))
                    add_plots.append(mpf.make_addplot(
                        [r_max] * len(plot_data), color='red', alpha=0.3))

            # Plot candlesticks and volume bars using mplfinance
            mpf.plot(
                plot_data,
                type='candle',
                volume=True,
                style=style,
                addplot=add_plots,
                savefig=dict(fname=filename, dpi=150, bbox_inches='tight')
            )

            logger.info(f"Chart saved: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error generating chart: {str(e)}")
