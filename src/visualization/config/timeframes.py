#!/usr/bin/env python3

"""
Konfigurace pro jednotlivé časové rámce používané při generování grafů.
"""

def get_min_candles_by_timeframe():
    """
    Vrátí minimální počet svíček pro smysluplný graf pro každý timeframe.
    
    Returns:
        dict: Slovník {timeframe: min_candles}
    """
    return {
        '1w': 8,     # Pro týdenní graf chceme alespoň 8 svíček
        '1d': 20,    # Pro denní graf chceme alespoň 20 svíček
        '4h': 30,    # Pro 4h graf chceme alespoň 30 svíček
        '1h': 48,    # Pro hodinový graf chceme alespoň 48 svíček
        '30m': 60,   # Pro 30m graf chceme alespoň 60 svíček
        '15m': 80,   # Pro 15m graf chceme alespoň 80 svíček
        '5m': 100,   # Pro 5m graf chceme alespoň 100 svíček
        '1m': 120    # Pro 1m graf chceme alespoň 120 svíček
    }

def get_days_by_timeframe():
    """
    Vrátí výchozí počet dní pro zobrazení v grafu pro každý timeframe.
    
    Returns:
        dict: Slovník {timeframe: days_to_show}
    """
    return {
        '1w': 180,  # 6 měsíců pro týdenní timeframe
        '1d': 60,   # 2 měsíce pro denní timeframe
        '4h': 14,   # 2 týdny pro 4h timeframe
        '1h': 7,    # 1 týden pro hodinový timeframe
        '30m': 5,   # 5 dní pro 30m timeframe
        '15m': 3,   # 3 dny pro 15m timeframe
        '5m': 2,    # 2 dny pro 5m timeframe
        '1m': 1     # 1 den pro 1m timeframe
    }

def get_projection_days_by_timeframe():
    """
    Vrátí počet dní pro projekci scénářů pro každý timeframe.
    
    Returns:
        dict: Slovník {timeframe: projection_days}
    """
    return {
        '1w': 60,   # 2 měsíce projekce pro týdenní timeframe
        '1d': 30,   # 1 měsíc projekce pro denní timeframe
        '4h': 14,   # 2 týdny projekce pro 4h timeframe
        '1h': 7,    # 1 týden projekce pro hodinový timeframe
        '30m': 4,   # 4 dny projekce pro 30m timeframe
        '15m': 2,   # 2 dny projekce pro 15m timeframe
        '5m': 1,    # 1 den projekce pro 5m timeframe
        '1m': 0.5   # 12 hodin projekce pro 1m timeframe
    }

def get_timeframe_config(timeframe):
    """
    Vrátí kompletní konfiguraci pro zadaný timeframe.
    
    Args:
        timeframe (str): Časový rámec ('1w', '1d', '4h', atd.)
        
    Returns:
        dict: Konfigurace pro zadaný timeframe
    """
    min_candles = get_min_candles_by_timeframe()
    days_by_tf = get_days_by_timeframe()
    projection_days = get_projection_days_by_timeframe()
    
    # Výchozí hodnoty pro případ, že timeframe není v konfiguraci
    config = {
        'min_candles': 10,
        'days_to_show': 2,
        'projection_days': 5
    }
    
    # Aktualizujeme konfiguraci podle timeframe
    if timeframe in min_candles:
        config['min_candles'] = min_candles[timeframe]
    
    if timeframe in days_by_tf:
        config['days_to_show'] = days_by_tf[timeframe]
    
    if timeframe in projection_days:
        config['projection_days'] = projection_days[timeframe]
    
    return config
