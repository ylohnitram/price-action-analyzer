def format_price(price, precision=0):
    """
    Formátuje cenovou hodnotu.
    
    Args:
        price (float): Cena k formátování
        precision (int): Počet desetinných míst
        
    Returns:
        str: Formátovaná cena
    """
    return f"{price:.{precision}f}"

def get_price_precision(price):
    """
    Určí vhodnou přesnost pro danou cenu.
    
    Args:
        price (float): Cena
        
    Returns:
        int: Počet desetinných míst
    """
    if price < 0.1:
        return 6  # Pro velmi malé hodnoty (např. některé altcoiny)
    elif price < 1:
        return 4
    elif price < 100:
        return 2
    else:
        return 0  # Pro větší hodnoty (např. BTC) stačí celá čísla

def format_volume(volume):
    """
    Formátuje objem do čitelného formátu (K, M, B).
    
    Args:
        volume (float): Objem
        
    Returns:
        str: Formátovaný objem
    """
    if volume >= 1_000_000_000:
        return f"{volume / 1_000_000_000:.1f}B"
    elif volume >= 1_000_000:
        return f"{volume / 1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"{volume / 1_000:.1f}K"
    else:
        return f"{volume:.0f}"
