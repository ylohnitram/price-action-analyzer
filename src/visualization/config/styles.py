def get_chart_style():
    """
    Vrátí styl grafu.
    
    Returns:
        dict: Slovník se styly grafu
    """
    return {
        # Základní styl
        'base_style': 'yahoo',
        
        # Mřížka
        'grid': {
            'style': '-',
            'alpha': 0.3,
            'axis': 'both'
        },
        
        # Popisky
        'labels': {
            'fontsize': {
                'title': 14,
                'axes': 10,
                'ticks': 8,
                'legend': 8,
                'annotation': 9
            },
            'fontweight': {
                'title': 'bold',
                'axes': 'normal',
                'annotation': 'bold'
            }
        },
        
        # Čáry
        'lines': {
            'support': {
                'linewidth': 1.5,
                'alpha': 0.7
            },
            'resistance': {
                'linewidth': 1.5,
                'alpha': 0.7
            },
            'scenario': {
                'linewidth': 2.5,
                'alpha': 0.9
            }
        },
        
        # Průhlednost
        'alpha': {
            'zones': 0.3,
            'volume': 0.7,
            'labels': 0.9
        }
    }
