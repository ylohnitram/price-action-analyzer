def get_color_scheme():
    """
    Vrátí barevné schéma pro grafy.
    
    Returns:
        dict: Slovník s barevnými schématy
    """
    return {
        # Barvy pro svíčky
        'candle_colors': {
            'up': '#00a061',
            'down': '#eb4d5c',
        },
        
        # Barvy pro zóny
        'support_zone_colors': ['#006400', '#008000', '#228B22', '#32CD32', '#3CB371', '#66CDAA'],
        'resistance_zone_colors': ['#8B0000', '#B22222', '#CD5C5C', '#DC143C', '#FF0000', '#FF4500'],
        
        # Barvy pro scénáře
        'bullish_color': 'green',
        'bearish_color': 'red',
        
        # Barvy pro popisky
        'label_bg_color': 'white',
        'label_text_color': 'black',
        
        # Barvy pro graf
        'grid_color': '#e6e6e6',
        'bg_color': 'white',
    }
