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
        tuple: (bullish_added, bearish_added, neutral_added) - Indikátory, zda byly přidány scénáře
    """
    if not scenarios:
        logger.warning("Nebyly předány žádné scénáře k vykreslení")
        return False, False, False
    
    # Kontrola, zda máme dostatek dat
    if plot_data is None or len(plot_data) == 0:
        logger.warning("Nedostatek dat pro vykreslení scénářů")
        return False, False, False
    
    bullish_added = False
    bearish_added = False
    neutral_added = False
    
    try:
        # Zjištění aktuální ceny
        current_price = plot_data['Close'].iloc[-1]
        logger.info(f"Aktuální cena pro scénáře: {current_price}")
        
        # Místo převodu na datum získáme přímo pozici v grafu
        x_values = np.arange(len(plot_data))
        last_x = x_values[-1]  # Poslední pozice na ose X
        
        # Určení délky projekce podle timeframe
        if timeframe == '1w':
            num_points = 8
        elif timeframe == '1d':
            num_points = 10
        elif timeframe == '4h':
            num_points = 12
        else:
            num_points = 8
        
        # Vytvoření budoucích X hodnot pro projekci
        future_x = np.linspace(last_x + 1, last_x + num_points, num_points)
        
        # Logování scénářů pro diagnostiku
        for i, (scenario_type, target_info) in enumerate(scenarios):
            logger.info(f"Zpracovávám scénář {i+1}: {scenario_type} - {target_info}")
        
        for scenario_type, target_info in scenarios:
            # BULLISH SCÉNÁŘ
            if scenario_type == 'bullish' and isinstance(target_info, (int, float)) and target_info > current_price:
                target_price = target_info
                logger.info(f"Vykreslování bullish scénáře s cílem {target_price}")
                
                # Výpočet y hodnot pro bullish scénář s mírnou fluktuací
                price_diff = target_price - current_price
                y_values = np.array([
                    current_price,  # První bod - aktuální cena
                    current_price + price_diff * 0.15,
                    current_price + price_diff * 0.25 - price_diff * 0.05,
                    current_price + price_diff * 0.4,
                    current_price + price_diff * 0.55 - price_diff * 0.03,
                    current_price + price_diff * 0.7,
                    current_price + price_diff * 0.85,
                    target_price    # Poslední bod - cílová cena
                ])
                
                # Oříznutí nebo doplnění pole y_values, aby odpovídalo future_x
                if len(y_values) > len(future_x):
                    y_values = y_values[:len(future_x)]
                elif len(y_values) < len(future_x):
                    # Doplnění lineární interpolací
                    step = (target_price - y_values[-1]) / (len(future_x) - len(y_values) + 1)
                    extra_points = [y_values[-1] + step * (i+1) for i in range(len(future_x) - len(y_values))]
                    y_values = np.append(y_values, extra_points)
                
                # Sestavení x souřadnic včetně poslední známé hodnoty
                x_coords = np.concatenate(([last_x], future_x))
                
                # Přidání aktuální ceny k y_values
                y_coords = np.concatenate(([current_price], y_values))
                
                # Kontrola, že oba vektory mají stejný rozměr
                if len(x_coords) != len(y_coords):
                    logger.error(f"Nesouhlasí počet bodů: x={len(x_coords)}, y={len(y_coords)}")
                    logger.error(f"x_coords: {x_coords}")
                    logger.error(f"y_coords: {y_coords}")
                    logger.info(f"Upravuji délky polí pro bullish scénář")
                    
                    # Oříznutí na kratší z obou polí
                    min_len = min(len(x_coords), len(y_coords))
                    x_coords = x_coords[:min_len]
                    y_coords = y_coords[:min_len]
                
                # Vykreslení linie
                ax.plot(x_coords, y_coords, '-', color='green', linewidth=2.5, zorder=5)
                
                # Přidání popisku cíle
                ax.text(
                    future_x[-1],
                    target_price,
                    f"{target_price:.0f}",
                    color='white',
                    fontweight='bold',
                    fontsize=10,
                    bbox=dict(facecolor='green', alpha=0.9, edgecolor='green', boxstyle='round,pad=0.3'),
                    zorder=6
                )
                
                bullish_added = True
                logger.info(f"Bullish scénář úspěšně přidán")
            
            # BEARISH SCÉNÁŘ
            elif scenario_type == 'bearish' and isinstance(target_info, (int, float)) and target_info < current_price:
                target_price = target_info
                logger.info(f"Vykreslování bearish scénáře s cílem {target_price}")
                
                # Výpočet y hodnot pro bearish scénář s mírnou fluktuací
                price_diff = current_price - target_price
                y_values = np.array([
                    current_price,  # První bod - aktuální cena
                    current_price - price_diff * 0.15,
                    current_price - price_diff * 0.25 + price_diff * 0.05,
                    current_price - price_diff * 0.4,
                    current_price - price_diff * 0.55 + price_diff * 0.03,
                    current_price - price_diff * 0.7,
                    current_price - price_diff * 0.85,
                    target_price    # Poslední bod - cílová cena
                ])
                
                # Oříznutí nebo doplnění pole y_values, aby odpovídalo future_x
                if len(y_values) > len(future_x):
                    y_values = y_values[:len(future_x)]
                elif len(y_values) < len(future_x):
                    # Doplnění lineární interpolací
                    step = (target_price - y_values[-1]) / (len(future_x) - len(y_values) + 1)
                    extra_points = [y_values[-1] + step * (i+1) for i in range(len(future_x) - len(y_values))]
                    y_values = np.append(y_values, extra_points)
                
                # Sestavení x souřadnic včetně poslední známé hodnoty
                x_coords = np.concatenate(([last_x], future_x))
                
                # Přidání aktuální ceny k y_values
                y_coords = np.concatenate(([current_price], y_values))
                
                # Kontrola, že oba vektory mají stejný rozměr
                if len(x_coords) != len(y_coords):
                    logger.error(f"Nesouhlasí počet bodů: x={len(x_coords)}, y={len(y_coords)}")
                    logger.error(f"x_coords: {x_coords}")
                    logger.error(f"y_coords: {y_coords}")
                    logger.info(f"Upravuji délky polí pro bearish scénář")
                    
                    # Oříznutí na kratší z obou polí
                    min_len = min(len(x_coords), len(y_coords))
                    x_coords = x_coords[:min_len]
                    y_coords = y_coords[:min_len]
                
                # Vykreslení linie
                ax.plot(x_coords, y_coords, '-', color='red', linewidth=2.5, zorder=5)
                
                # Přidání popisku cíle
                ax.text(
                    future_x[-1],
                    target_price,
                    f"{target_price:.0f}",
                    color='white',
                    fontweight='bold',
                    fontsize=10,
                    bbox=dict(facecolor='red', alpha=0.9, edgecolor='red', boxstyle='round,pad=0.3'),
                    zorder=6
                )
                
                bearish_added = True
                logger.info(f"Bearish scénář úspěšně přidán")
            
            # NEUTRÁLNÍ SCÉNÁŘ
            elif scenario_type == 'neutral' and isinstance(target_info, tuple) and len(target_info) == 2:
                # Pro neutrální scénář - vykreslíme vodorovný pás
                lower_bound, upper_bound = target_info
                logger.info(f"Vykreslování neutrálního scénáře s rozsahem {lower_bound}-{upper_bound}")
                
                # Kontrola, že hranice dávají smysl
                if lower_bound < upper_bound:
                    # Vykreslení horní a dolní hranice
                    x_coords = np.concatenate(([last_x], future_x))
                    
                    # Horní hranice - vodorovná čára
                    upper_y = np.full(len(x_coords), upper_bound)
                    ax.plot(x_coords, upper_y, '--', color='blue', linewidth=1.5, zorder=5, alpha=0.7)
                    
                    # Dolní hranice - vodorovná čára
                    lower_y = np.full(len(x_coords), lower_bound)
                    ax.plot(x_coords, lower_y, '--', color='blue', linewidth=1.5, zorder=5, alpha=0.7)
                    
                    # Vyplnění oblasti mezi hranicemi
                    ax.fill_between(x_coords, lower_y, upper_y, color='blue', alpha=0.1, zorder=4)
                    
                    # Přidání popisků
                    ax.text(
                        future_x[-1],
                        upper_bound,
                        f"{upper_bound:.0f}",
                        color='black',
                        fontweight='bold',
                        fontsize=9,
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='blue'),
                        zorder=6
                    )
                    
                    ax.text(
                        future_x[-1],
                        lower_bound,
                        f"{lower_bound:.0f}",
                        color='black',
                        fontweight='bold',
                        fontsize=9,
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='blue'),
                        zorder=6
                    )
                    
                    neutral_added = True
                    logger.info(f"Neutrální scénář úspěšně přidán")
                else:
                    logger.warning(f"Neutrální scénář má nesmyslný rozsah: {lower_bound}-{upper_bound}")
            else:
                logger.warning(f"Neznámý nebo nesprávný formát scénáře: {scenario_type} - {target_info}")
        
        return bullish_added, bearish_added, neutral_added
    
    except Exception as e:
        logger.error(f"Chyba při vykreslování scénářů: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False, False, False

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
    # Ošetření vstupů - minimální počet bodů
    num_points = max(2, num_points)
    
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
