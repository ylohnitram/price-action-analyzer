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
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

# Import konfiguračních modulů
from src.visualization.config.colors import get_color_scheme, get_candle_colors, get_zone_colors, get_scenario_colors
from src.visualization.config.timeframes import get_timeframe_config, get_min_candles_by_timeframe, get_days_by_timeframe

logger = logging.getLogger(__name__)

class ChartGenerator:
    """Class for generating candlestick charts with support and resistance zones and trend scenarios."""

    def generate_chart(self, df, support_zones, resistance_zones, symbol, 
                       filename=None, days_to_show=2, hours_to_show=None, 
                       timeframe=None, scenarios=None):
        """
        Generates a candlestick chart with support and resistance zones and trend scenarios.
        
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

        # Získání konfigurace pro timeframe
        tf_config = get_timeframe_config(timeframe)
        min_candles = tf_config['min_candles']
        
        # Adjust days_to_show based on timeframe if not explicitly overridden
        days_by_tf = get_days_by_timeframe()
        if days_to_show == 2 and timeframe in days_by_tf:  # Default value
            days_to_show = days_by_tf[timeframe]
            logger.info(f"Adjusting days_to_show to {days_to_show} for {timeframe} timeframe")

        # Limit the data range to display
        end_date = df.index.max()
        if hours_to_show:
            start_date = end_date - timedelta(hours=hours_to_show)
        else:
            # If days_to_show is really big, we might want to limit this for readable charts
            days_to_use = min(days_to_show, 90)  # Cap at 90 days for readability
            start_date = end_date - timedelta(days=days_to_use)
        
        plot_data = df[df.index >= start_date].copy()
        
        # Ensure we have enough data to plot based on timeframe
        if len(plot_data) < min_candles:
            logger.warning(f"Not enough data ({len(plot_data)} candles) for {timeframe}. Using all available data.")
            
            # Pokud máme více dat než minimum, použijeme poslední N (min_candles) svíček
            if len(df) >= min_candles:
                plot_data = df.tail(min_candles).copy()
                logger.info(f"Using last {min_candles} candles from available data")
            else:
                # Pokud nemáme dostatek dat vůbec, použijeme vše co máme
                plot_data = df.copy()
                logger.warning(f"Only {len(df)} candles available, which is less than minimum {min_candles} for {timeframe}")

        # Get colors from config
        candle_colors = get_candle_colors()
        zone_colors = get_zone_colors()
        scenario_colors = get_scenario_colors()
        
        # Define candlestick style with colors from config
        mc = mpf.make_marketcolors(
            up=candle_colors['up'],
            down=candle_colors['down'],
            edge={'up': candle_colors['edge_up'], 'down': candle_colors['edge_down']},
            wick={'up': candle_colors['wick_up'], 'down': candle_colors['wick_down']},
            volume={'up': candle_colors['volume_up'], 'down': candle_colors['volume_down']}
        )
        
        # Configure figure size and proportions
        figsize = (12, 8)
        height_ratios = [4, 1]  # Main chart 4x the height of volume

        style = mpf.make_mpf_style(
            base_mpf_style='yahoo',
            marketcolors=mc,
            gridstyle='-',
            gridcolor='#e6e6e6',
            gridaxis='both',
            facecolor='white',
            rc={'figure.figsize': figsize}
        )

        try:
            # Create the figure with GridSpec for proper subplot spacing
            fig = plt.figure(figsize=figsize, dpi=100)
            gs = fig.add_gridspec(2, 1, height_ratios=height_ratios, hspace=0.05)
            ax1 = fig.add_subplot(gs[0, 0])  # Main price chart
            ax2 = fig.add_subplot(gs[1, 0], sharex=ax1)  # Volume chart

            # Plot candlesticks with mplfinance
            mpf.plot(
                plot_data, 
                ax=ax1, 
                volume=ax2, 
                type='candle', 
                style=style, 
                show_nontrading=False,
                datetime_format='%Y-%m-%d',
                xrotation=0
            )

            # Calculate date range for future projections
            date_range = (plot_data.index[-1] - plot_data.index[0]).days
            projection_days = tf_config['projection_days']
            last_date = plot_data.index[-1]
            
            # Create future date range for scenario projection
            num_future_points = 10  # Number of points to use for smooth curves
            future_dates = pd.date_range(
                start=last_date, 
                periods=num_future_points + 1, 
                freq=f'{projection_days//num_future_points}D'
            )[1:]  # Skip the first point which is the last existing date
            
            # Combine existing and future dates for the x-axis
            all_dates = plot_data.index.tolist() + future_dates.tolist()
            
            # Set the extended x-axis limit
            ax1.set_xlim(plot_data.index[0], future_dates[-1])
            
            # Adjust y-axis limits for better visibility of all elements
            y_min, y_max = ax1.get_ylim()
            price_range = y_max - y_min
            y_padding = price_range * 0.05
            ax1.set_ylim(y_min - y_padding, y_max + y_padding)

            # Get support and resistance zone colors from config
            support_colors = zone_colors['support']
            resistance_colors = zone_colors['resistance']

            # Sort zones by price level for better labeling
            if support_zones:
                support_zones.sort(key=lambda x: x[0])
            if resistance_zones:
                resistance_zones.sort(key=lambda x: x[0], reverse=True)

            # Current price for reference
            current_price = plot_data['Close'].iloc[-1]

            # Define legend elements
            legend_elements = []
            s_zones_added = 0
            r_zones_added = 0

            # Add support zones
            for i, (s_min, s_max) in enumerate(support_zones or []):
                if not (np.isnan(s_min) or np.isnan(s_max)):
                    # Use a different color for each support zone
                    color_idx = min(i, len(support_colors) - 1)
                    color = support_colors[color_idx]
                    
                    # Add filled area for support zone
                    ax1.axhspan(s_min, s_max, facecolor=color, alpha=0.3, label=f'Support Zone' if i == 0 else "")
                    
                    # Add horizontal lines at zone boundaries for better visibility
                    ax1.axhline(y=s_min, color=color, linestyle='-', linewidth=1.0, alpha=0.7)
                    ax1.axhline(y=s_max, color=color, linestyle='-', linewidth=1.0, alpha=0.7)
                    
                    # Add text label for support zone
                    mid_point = (s_min + s_max) / 2
                    ax1.text(
                        plot_data.index[0], 
                        mid_point, 
                        f"S{i+1}: {mid_point:.0f}", 
                        color='white', 
                        fontweight='bold', 
                        fontsize=9,
                        bbox=dict(
                            facecolor=color, 
                            alpha=0.9, 
                            edgecolor=color, 
                            boxstyle='round,pad=0.3'
                        )
                    )
                    
                    # Add to legend only once
                    if s_zones_added < 1:
                        legend_elements.append(Line2D([0], [0], color=color, lw=4, label='Support Zone'))
                        s_zones_added += 1

            # Add resistance zones
            for i, (r_min, r_max) in enumerate(resistance_zones or []):
                if not (np.isnan(r_min) or np.isnan(r_max)):
                    # Use a different color for each resistance zone
                    color_idx = min(i, len(resistance_colors) - 1)
                    color = resistance_colors[color_idx]
                    
                    # Add filled area for resistance zone
                    ax1.axhspan(r_min, r_max, facecolor=color, alpha=0.3, label=f'Resistance Zone' if i == 0 else "")
                    
                    # Add horizontal lines at zone boundaries for better visibility
                    ax1.axhline(y=r_min, color=color, linestyle='-', linewidth=1.0, alpha=0.7)
                    ax1.axhline(y=r_max, color=color, linestyle='-', linewidth=1.0, alpha=0.7)
                    
                    # Add text label for resistance zone
                    mid_point = (r_min + r_max) / 2
                    ax1.text(
                        plot_data.index[0], 
                        mid_point, 
                        f"R{i+1}: {mid_point:.0f}", 
                        color='white', 
                        fontweight='bold', 
                        fontsize=9,
                        bbox=dict(
                            facecolor=color, 
                            alpha=0.9, 
                            edgecolor=color, 
                            boxstyle='round,pad=0.3'
                        )
                    )
                    
                    # Add to legend only once
                    if r_zones_added < 1:
                        legend_elements.append(Line2D([0], [0], color=color, lw=4, label='Resistance Zone'))
                        r_zones_added += 1
            
            # Add trend scenarios with realistic bounces
            if scenarios:
                # Convert index to numeric values for interpolation
                x_dates = mdates.date2num(plot_data.index.to_pydatetime())
                last_x = x_dates[-1]
                future_x_dates = mdates.date2num(future_dates.to_pydatetime())
                
                # Flag for legend items
                bullish_added = False
                bearish_added = False
                
                for i, (scenario_type, target_price) in enumerate(scenarios):
                    if 'bullish' in scenario_type:
                        # Calculate control points with realistic bounces
                        bounces = []
                        
                        # Find potential resistance levels to bounce from
                        for r_min, r_max in resistance_zones or []:
                            if r_min > current_price and r_min < target_price:
                                bounces.append((r_min + r_max) / 2)
                        
                        # If no resistance zones in range, create artificial bounces
                        if not bounces and target_price > current_price:
                            range_size = target_price - current_price
                            num_bounces = min(2, projection_days // 7)  # One bounce per week, max 2
                            for j in range(1, num_bounces + 1):
                                bounce_level = current_price + (range_size * j) / (num_bounces + 1)
                                bounces.append(bounce_level)
                        
                        # Create x points for the projection - use existing dates + future
                        x_points = np.append(x_dates[-5:], future_x_dates)
                        
                        # Start y points with last few candles for continuity
                        y_start = plot_data['Close'].iloc[-5:].values
                        
                        # Generate path to target with bounces
                        if bounces:
                            # Distribute bounces across the future timeline
                            future_segment = len(future_x_dates) / (len(bounces) + 1)
                            y_future = []
                            
                            for j, bounce in enumerate(bounces):
                                # Position at this bounce
                                pos = int((j + 1) * future_segment)
                                
                                # Add points leading up to the bounce
                                if j == 0:
                                    # From current to first bounce
                                    segment_pts = np.linspace(current_price, bounce, pos+1)[1:]
                                    y_future.extend(segment_pts)
                                else:
                                    # From previous bounce to this bounce
                                    prev_bounce = bounces[j-1]
                                    segment_pts = np.linspace(prev_bounce, bounce, pos - int(j * future_segment) + 1)[1:]
                                    y_future.extend(segment_pts)
                            
                            # Complete the path to the target
                            last_bounce = bounces[-1]
                            remaining_pts = len(future_x_dates) - len(y_future)
                            final_segment = np.linspace(last_bounce, target_price, remaining_pts + 1)[1:]
                            y_future.extend(final_segment)
                            
                            # Combine with beginning points
                            y_points = np.append(y_start, y_future)
                        else:
                            # Simple path directly to target if no bounces
                            y_future = np.linspace(current_price, target_price, len(future_x_dates))
                            y_points = np.append(y_start, y_future)
                        
                        # Plot the trend line
                        if scenario_type == 'bullish':
                            ax1.plot(x_points, y_points, '-', color=scenario_colors['bullish'], linewidth=2.5)
                            
                            # Add price target text at end of line
                            ax1.text(
                                future_dates[-1], 
                                target_price, 
                                f"{target_price:.0f}", 
                                color='white', 
                                fontweight='bold', 
                                fontsize=10,
                                bbox=dict(facecolor=scenario_colors['bullish'], alpha=0.9, edgecolor=scenario_colors['bullish'])
                            )
                            
                            if not bullish_added:
                                legend_elements.append(Line2D([0], [0], color=scenario_colors['bullish'], lw=2.5, label='Bullish Scenario'))
                                bullish_added = True
                    
                    elif 'bearish' in scenario_type:
                        # Calculate control points with realistic bounces
                        bounces = []
                        
                        # Find potential support levels to bounce from
                        for s_min, s_max in support_zones or []:
                            if s_max < current_price and s_max > target_price:
                                bounces.append((s_min + s_max) / 2)
                        
                        # If no support zones in range, create artificial bounces
                        if not bounces and target_price < current_price:
                            range_size = current_price - target_price
                            num_bounces = min(2, projection_days // 7)  # One bounce per week, max 2
                            for j in range(1, num_bounces + 1):
                                bounce_level = current_price - (range_size * j) / (num_bounces + 1)
                                bounces.append(bounce_level)
                        
                        # Create x points for the projection - use existing dates + future
                        x_points = np.append(x_dates[-5:], future_x_dates)
                        
                        # Start y points with last few candles for continuity
                        y_start = plot_data['Close'].iloc[-5:].values
                        
                        # Generate path to target with bounces
                        if bounces:
                            # Distribute bounces across the future timeline
                            future_segment = len(future_x_dates) / (len(bounces) + 1)
                            y_future = []
                            
                            for j, bounce in enumerate(bounces):
                                # Position at this bounce
                                pos = int((j + 1) * future_segment)
                                
                                # Add points leading up to the bounce
                                if j == 0:
                                    # From current to first bounce
                                    segment_pts = np.linspace(current_price, bounce, pos+1)[1:]
                                    y_future.extend(segment_pts)
                                else:
                                    # From previous bounce to this bounce
                                    prev_bounce = bounces[j-1]
                                    segment_pts = np.linspace(prev_bounce, bounce, pos - int(j * future_segment) + 1)[1:]
                                    y_future.extend(segment_pts)
                            
                            # Complete the path to the target
                            last_bounce = bounces[-1]
                            remaining_pts = len(future_x_dates) - len(y_future)
                            final_segment = np.linspace(last_bounce, target_price, remaining_pts + 1)[1:]
                            y_future.extend(final_segment)
                            
                            # Combine with beginning points
                            y_points = np.append(y_start, y_future)
                        else:
                            # Simple path directly to target if no bounces
                            y_future = np.linspace(current_price, target_price, len(future_x_dates))
                            y_points = np.append(y_start, y_future)
                        
                        # Plot the trend line
                        if scenario_type == 'bearish':
                            ax1.plot(x_points, y_points, '-', color=scenario_colors['bearish'], linewidth=2.5)
                            
                            # Add price target text at end of line
                            ax1.text(
                                future_dates[-1], 
                                target_price, 
                                f"{target_price:.0f}", 
                                color='white', 
                                fontweight='bold', 
                                fontsize=10,
                                bbox=dict(facecolor=scenario_colors['bearish'], alpha=0.9, edgecolor=scenario_colors['bearish'])
                            )
                            
                            if not bearish_added:
                                legend_elements.append(Line2D([0], [0], color=scenario_colors['bearish'], lw=2.5, label='Bearish Scenario'))
                                bearish_added = True

            # Add title with symbol and timeframe
            title = f"{symbol} - {timeframe} Timeframe"
            if timeframe in ['1d', '1w']:
                title += " (Long-term Analysis)"
            elif timeframe in ['4h', '1h']:
                title += " (Medium-term Analysis)"
            else:
                title += " (Short-term Analysis)"
            
            ax1.set_title(title, fontsize=14, fontweight='bold')
            
            # Format x-axis dates
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.xticks(rotation=45)
            
            # Add a watermark with generation time
            plt.figtext(
                0.01, 0.01,
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                fontsize=7,
                bbox=dict(facecolor='white', alpha=0.8)
            )
            
            # Add legend at the upper left
            if legend_elements:
                ax1.legend(
                    handles=legend_elements, 
                    loc='upper left', 
                    fontsize=8, 
                    framealpha=0.8, 
                    ncol=len(legend_elements)
                )

            # Save the chart to file with tight layout
            plt.tight_layout()
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close(fig)

            logger.info(f"Chart saved: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error generating chart: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
