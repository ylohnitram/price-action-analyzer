def get_timeframe_config(timeframe=None):
    """
    Vrátí konfiguraci pro konkrétní timeframe.
    
    Args:
        timeframe (str, optional): Timeframe, pro který chceme konfiguraci
        
    Returns:
        dict: Slovník s konfigurací pro daný timeframe
    """
    # Základní konfigurace pro všechny timeframy
    base_config = {
        'figsize': (12, 8),       # Velikost figury
        'height_ratios': [4, 1],  # Poměr výšky hlavního grafu a volume grafu
        'max_days': 90,           # Maximální počet dní pro zobrazení
        'min_candles': 10,        # Minimální počet svíček pro smysluplný graf
        'projection_days': 10,    # Počet dní projekce pro scénáře
    }
    
    # Specifické konfigurace pro jednotlivé timeframy
    timeframe_configs = {
        # Týdenní timeframe
        '1w': {
            'min_candles': 5,      # Stačí 5 týdenních svíček
            'max_days': 365,       # Až rok dat
            'projection_days': 60, # Projekce 2 měsíce dopředu
        },
        
        # Denní timeframe
        '1d': {
            'min_candles': 5,      # Stačí 5 denních svíček
            'max_days': 180,       # Až 6 měsíců dat
            'projection_days': 30, # Projekce měsíc dopředu
        },
        
        # 4-hodinový timeframe
        '4h': {
            'max_days': 30,        # Až měsíc dat
            'projection_days': 7,  # Projekce týden dopředu
        },
        
        # 30-minutový timeframe
        '30m': {
            'max_days': 14,        # Až dva týdny dat
            'projection_days': 3,  # Projekce 3 dny dopředu
        },
        
        # 5-minutový timeframe
        '5m': {
            'max_days': 5,         # Až 5 dní dat
            'projection_days': 1,  # Projekce den dopředu
        }
    }
    
    # Pokud nemáme specifickou konfiguraci, vrátíme základní
    if not timeframe or timeframe not in timeframe_configs:
        return base_config
        
    # Sloučení základní konfigurace se specifickou
    config = base_config.copy()
    config.update(timeframe_configs[timeframe])
    
    return config
