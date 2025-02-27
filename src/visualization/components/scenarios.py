import numpy as np
import matplotlib.dates as mdates
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

def draw_scenarios(ax, scenarios, plot_data, timeframe):
    """
    Vykreslí scénáře do grafu s realistickými bouncy.
    
    Args:
        ax: Matplotlib osa
        scenarios (list): Seznam scénářů jako (typ, cenový_cíl)
        plot_data (DataFrame): DataFrame s daty pro graf
        timeframe (str): Časový rámec dat
        
    Returns:
        tuple: (bullish_added, bearish_added) - Indikátory, zda byly přidány scénáře
    """
    if not scenarios:
        return False, False
    
    bullish_added = False
    bearish_added = False
    
    # Zjištění aktuální ceny
    current_price = plot_data['Close'].iloc[-1]
    
    # Převod dat na numerické hodnoty pro interpolaci
    x_dates = mdates.date2num(plot_data.index.to_pydatetime())
    last_date = plot_data.index[-1]
    
    # Určení délky projekce podle timeframe
    if timeframe == '1w':
        projection_days = 60  # 2 měsíce
    elif timeframe == '1d':
        projection_days = 30  # 1 měsíc
    elif timeframe == '4h':
        projection_days = 14  # 2 týdny
    elif timeframe == '1h':
        projection_days = 7   # 1 týden
    else:
        projection_days = 3   # 3 dny pro ostatní timeframy
    
    # Vytvoření budoucích dat pro projekci
    future_dates = [last_date + timedelta(days=i) for i in range(1, projection_days + 1)]
    future_x_dates = mdates.date2num(future_dates)
    
    # Počet bodů pro projekci
    num_points = len(future_dates)
    
    for scenario_type, target_price in scenarios:
        if scenario_type == 'bullish' and target_price > current_price:
            # Bullish scénář s bouncy
            bounces = generate_bounces_to_target(current_price, target_price, num_points, 'bullish')
            
            # Vygenerování všech bodů včetně aktuálních
            y_points = np.append([current_price], bounces)
            x_points = np.append([x_dates[-1]], future_x_dates)
            
            # Vykreslení čáry
            ax.plot(x_points, y_points, '-', color='green', linewidth=2.5)
            
            # Přidání popisku cíle
            ax.text(
                future_dates[-1], 
                target_price, 
                f"{target_price:.0f}", 
                color='white', 
                fontweight='bold', 
                fontsize=10,
                bbox=dict(facecolor='green', alpha=0.9, edgecolor='green')
            )
            
            bullish_added = True
            
        elif scenario_type == 'bearish' and target_price < current_price:
            # Bearish scénář s bouncy
            bounces = generate_bounces_to_target(current_price, target_price, num_points, 'bearish')
            
            # Vygenerování všech bodů včetně aktuálních
            y_points = np.append([current_price], bounces)
            x_points = np.append([x_dates[-1]], future_x_dates)
            
            # Vykreslení čáry
            ax.plot(x_points, y_points, '-', color='red', linewidth=2.5)
            
            # Přidání popisku cíle
            ax.text(
                future_dates[-1], 
                target_price, 
                f"{target_price:.0f}", 
                color='white', 
                fontweight='bold', 
                fontsize=10,
                bbox=dict(facecolor='red', alpha=0.9, edgecolor='red')
            )
            
            bearish_added = True
    
    return bullish_added, bearish_added

def generate_bounces_to_target(start_price, target_price, num_points, direction):
    """
    Generuje realistické výkyvy (bouncy) na cestě k cílovému bodu.
    
    Args:
        start_price (float): Počáteční cena
        target_price (float): Cílová cena
        num_points (int): Počet bodů k vygenerování
        direction (str): Směr 'bullish' nebo 'bearish'
        
    Returns:
        numpy.array: Pole cen s bouncy
    """
    # Celkový rozsah ceny
    price_range = abs(target_price - start_price)
    
    # Určení počtu výkyvů (bouncy)
    num_bounces = min(3, max(1, num_points // 7))  # 1-3 výkyvy podle délky projekce
    
    # Určení směru a amplitudy výkyvů
    if direction == 'bullish':
        # Pro bullish - větší výkyvy dolů, menší nahoru
        avg_downward_bounce = price_range * 0.15  # 15% pokles
        avg_upward_bounce = price_range * 0.25    # 25% nárůst
    else:
        # Pro bearish - větší výkyvy nahoru, menší dolů
        avg_downward_bounce = price_range * 0.25  # 25% pokles
        avg_upward_bounce = price_range * 0.15    # 15% nárůst
    
    # Generování základního trendu
    if num_points <= 2:
        # Pro velmi krátké projekce - lineární trasa
        return np.linspace(start_price, target_price, num_points)
    
    # Generování bodů s výkyvy
    points = []
    
    # Vypočítáme mezicíle (intermediate targets)
    if direction == 'bullish':
        # Bullish trend - postupně rostoucí
        intermediate_targets = np.linspace(start_price, target_price, num_bounces + 2)[1:-1]
    else:
        # Bearish trend - postupně klesající
        intermediate_targets = np.linspace(start_price, target_price, num_bounces + 2)[1:-1]
    
    # Rozdělení celkové cesty na segmenty podle počtu výkyvů
    segment_size = num_points // (num_bounces + 1)
    
    # Pro každý segment generujeme bouncy
    for i in range(num_bounces + 1):
        if i == num_bounces:
            # Poslední segment vede přímo k cíli
            segment_target = target_price
            segment_points = num_points - len(points)
        else:
            # Mezisegmenty mají výkyvy
            segment_target = intermediate_targets[i]
            segment_points = segment_size
        
        # Pokud je to segment s výkyvem
        if i < num_bounces:
            # Generování hlavního trendu segmentu
            base_trend = np.linspace(
                start_price if i == 0 else points[-1], 
                segment_target, 
                segment_points
            )
            
            # Přidání výkyvu - polovina segmentu s výkyvem opačným směrem
            bounce_idx = segment_points // 2
            
            # Přidání bodů před výkyvem
            points.extend(base_trend[:bounce_idx].tolist())
            
            # Určení amplitudy výkyvu
            if direction == 'bullish':
                bounce_amplitude = avg_downward_bounce * (1.0 - i/num_bounces)  # Menší výkyvy ke konci
                bounce_value = base_trend[bounce_idx] - bounce_amplitude
            else:
                bounce_amplitude = avg_upward_bounce * (1.0 - i/num_bounces)  # Menší výkyvy ke konci
                bounce_value = base_trend[bounce_idx] + bounce_amplitude
            
            # Přidání bodu výkyvu
            points.append(bounce_value)
            
            # Přidání zbytku bodů segmentu
            points.extend(base_trend[bounce_idx+1:].tolist())
        else:
            # Poslední segment - lineární trasa k cíli
            final_trend = np.linspace(points[-1], segment_target, segment_points)
            points.extend(final_trend.tolist())
    
    # Vrácení jako numpy array
    return np.array(points)
