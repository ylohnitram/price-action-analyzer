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
from matplotlib.patches import FancyArrowPatch

logger = logging.getLogger(__name__)

class ChartGenerator:
    """Class for generating candlestick charts with support and resistance zones."""

    def generate_chart(self, df, support_zones, resistance_zones, symbol, 
                       filename=None, days_to_show=2, hours_to_show=None, 
                       timeframe=None, scenarios=None):
        """
        Generates a candlestick chart with support and resistance zones and scenario arrows.
        
        Args:
            df (pandas.DataFrame): DataFrame with OHLCV data
            support_zones (list): List of support zones as (min, max) tuples
            resistance_zones (list): List of resistance zones as (min, max) tuples
            symbol (str): Trading symbol
            filename (str, optional): Output filename
            days_to_show (int, optional): Number of days to show
            hours_to_show (int, optional): Number of hours to show
            timeframe (str, optional): Timeframe of the data
            scenarios (list, optional): List of potential scenarios to visualize
        
        Returns:
            str: Path to the generated chart file
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
            # Create the figure and subplots
            fig = plt.figure(figsize=(12, 8))
            gs = fig.add_gridspec(5, 1)
            ax1 = fig.add_subplot(gs[0:4, 0])  # Main price chart
            ax2 = fig.add_subplot(gs[4, 0], sharex=ax1)  # Volume chart

            # Plot candlesticks and volume bars using mplfinance
            mpf.plot(plot_data, ax=ax1, volume=ax2, type='candle', style=style)

            # Add support zones (green rectangles)
            for s_min, s_max in (support_zones or []):
                if not (np.isnan(s_min) or np.isnan(s_max)):
                    ax1.axhspan(s_min, s_max, facecolor='#90EE90', alpha=0.3)
                    # Add text label for support zone
                    ax1.text(plot_data.index[-1], s_min, f"S:{s_min:.0f}", 
                             color='green', fontweight='bold', fontsize=8,
                             bbox=dict(facecolor='white', alpha=0.7))

            # Add resistance zones (red rectangles)
            for r_min, r_max in (resistance_zones or []):
                if not (np.isnan(r_min) or np.isnan(r_max)):
                    ax1.axhspan(r_min, r_max, facecolor='#FFB6C1', alpha=0.3)
                    # Add text label for resistance zone
                    ax1.text(plot_data.index[-1], r_max, f"R:{r_max:.0f}", 
                             color='red', fontweight='bold', fontsize=8,
                             bbox=dict(facecolor='white', alpha=0.7))
            
            # Add potential scenario arrows if provided
            if scenarios:
                current_price = plot_data['Close'].iloc[-1]
                # Most recent date as a starting point for arrows
                last_idx = plot_data.index[-1]
                
                # Calculate arrow extensions based on data span
                date_range = plot_data.index[-1] - plot_data.index[0]
                arrow_extend = date_range * 0.2  # Extend 20% into the future
                
                for scenario_type, target_price in scenarios:
                    if scenario_type == 'bullish':
                        # Bold bullish arrow in green
                        arrow = FancyArrowPatch(
                            (last_idx, current_price),
                            (last_idx + arrow_extend, target_price),
                            arrowstyle='-|>', linewidth=2, color='green',
                            mutation_scale=15, shrinkA=0, shrinkB=0
                        )
                        ax1.add_patch(arrow)
                        ax1.text(last_idx + arrow_extend, target_price, 
                                f"↑ {target_price:.0f}", color='green', fontweight='bold',
                                bbox=dict(facecolor='white', alpha=0.7))
                    
                    elif scenario_type == 'bullish_mid':
                        # Thinner intermediate bullish arrow
                        arrow = FancyArrowPatch(
                            (last_idx, current_price),
                            (last_idx + arrow_extend*0.7, target_price),
                            arrowstyle='->', linewidth=1.5, color='green',
                            mutation_scale=12, shrinkA=0, shrinkB=0
                        )
                        ax1.add_patch(arrow)
                    
                    elif scenario_type == 'bearish':
                        # Bold bearish arrow in red
                        arrow = FancyArrowPatch(
                            (last_idx, current_price),
                            (last_idx + arrow_extend, target_price),
                            arrowstyle='-|>', linewidth=2, color='red',
                            mutation_scale=15, shrinkA=0, shrinkB=0
                        )
                        ax1.add_patch(arrow)
                        ax1.text(last_idx + arrow_extend, target_price, 
                                f"↓ {target_price:.0f}", color='red', fontweight='bold',
                                bbox=dict(facecolor='white', alpha=0.7))
                    
                    elif scenario_type == 'bearish_mid':
                        # Thinner intermediate bearish arrow
                        arrow = FancyArrowPatch(
                            (last_idx, current_price),
                            (last_idx + arrow_extend*0.7, target_price),
                            arrowstyle='->', linewidth=1.5, color='red',
                            mutation_scale=12, shrinkA=0, shrinkB=0
                        )
                        ax1.add_patch(arrow)

            # Add Fair Value Gaps if they exist in the zones
            for s_min, s_max in (support_zones or []):
                if 'FVG' in str(s_min) + str(s_max):  # Simple check if this is an FVG zone
                    ax1.axhspan(s_min, s_max, facecolor='#32CD32', alpha=0.4, hatch='///')
                    ax1.text(plot_data.index[0], (s_min + s_max)/2, "Bullish FVG", 
                            color='green', fontweight='bold', fontsize=9,
                            bbox=dict(facecolor='white', alpha=0.7))
                    
            for r_min, r_max in (resistance_zones or []):
                if 'FVG' in str(r_min) + str(r_max):  # Simple check if this is an FVG zone
                    ax1.axhspan(r_min, r_max, facecolor='#FF6347', alpha=0.4, hatch='///')
                    ax1.text(plot_data.index[0], (r_min + r_max)/2, "Bearish FVG", 
                            color='red', fontweight='bold', fontsize=9,
                            bbox=dict(facecolor='white', alpha=0.7))

            # Add title with symbol and timeframe
            title = f"{symbol} - {timeframe} Timeframe"
            if timeframe in ['1d', '1w']:
                title += " (Long-term Analysis)"
            elif timeframe in ['4h', '1h']:
                title += " (Medium-term Analysis)"
            else:
                title += " (Short-term Analysis)"
            
            ax1.set_title(title, fontsize=14, fontweight='bold')
            
            # Adjust layout for better readability
            plt.subplots_adjust(bottom=0.15, hspace=0.05)

            # Add a watermark with generation time
            plt.figtext(0.01, 0.01,
                        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        fontsize=7, backgroundcolor='white',
                        bbox=dict(facecolor='white', alpha=0.8))
            
            # Add legend for key elements
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='#90EE90', alpha=0.3, label='Support Zone'),
                Patch(facecolor='#FFB6C1', alpha=0.3, label='Resistance Zone'),
            ]
            
            if scenarios:
                legend_elements.extend([
                    Patch(facecolor='green', label='Bullish Scenario'),
                    Patch(facecolor='red', label='Bearish Scenario'),
                ])
                
            ax1.legend(handles=legend_elements, loc='upper left', fontsize=8)

            # Save the chart to file
            plt.savefig(filename, dpi=150)
            plt.close(fig)

            logger.info(f"Chart saved: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error generating chart: {str(e)}")
            return None
