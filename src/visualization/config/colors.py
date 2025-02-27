#!/usr/bin/env python3

"""
Definice barevných schémat pro vizualizace.
"""

def get_candle_colors():
    """
    Vrátí barvy pro svíčkový graf.
    
    Returns:
        dict: Slovník s barvami pro svíčky
    """
    return {
        'up': '#00a061',       # Zelená pro rostoucí svíčky
        'down': '#eb4d5c',     # Červená pro klesající svíčky
        'edge_up': '#00a061',  # Okraj rostoucích svíček
        'edge_down': '#eb4d5c',# Okraj klesajících svíček
        'wick_up': '#00a061',  # Knoty rostoucích svíček
        'wick_down': '#eb4d5c',# Knoty klesajících svíček
        'volume_up': '#a3e2c5',# Objem pro rostoucí svíčky
        'volume_down': '#f1c3c8'# Objem pro klesající svíčky
    }

def get_zone_colors():
    """
    Vrátí barvy pro supportní a resistenční zóny.
    
    Returns:
        dict: Slovník s barvami pro zóny
    """
    return {
        'support': ['#006400', '#008000', '#228B22', '#32CD32'], # Různé odstíny zelené
        'resistance': ['#8B0000', '#B22222', '#CD5C5C', '#DC143C'] # Různé odstíny červené
    }

def get_scenario_colors():
    """
    Vrátí barvy pro scénáře.
    
    Returns:
        dict: Slovník s barvami pro scénáře
    """
    return {
        'bullish': 'green',   # Barva pro býčí scénář
        'bearish': 'red'      # Barva pro medvědí scénář
    }

def get_chart_colors():
    """
    Vrátí barvy pro obecné prvky grafu.
    
    Returns:
        dict: Slovník s barvami pro graf
    """
    return {
        'grid': '#e6e6e6',     # Barva mřížky
        'background': 'white', # Barva pozadí
        'text': 'black',       # Barva textu
        'title': 'black',      # Barva nadpisu
        'border': '#cccccc'    # Barva okraje
    }

def get_color_scheme():
    """
    Vrátí kompletní barevné schéma.
    
    Returns:
        dict: Kompletní barevné schéma
    """
    return {
        'candle_colors': get_candle_colors(),
        'zone_colors': get_zone_colors(),
        'scenario_colors': get_scenario_colors(),
        'chart_colors': get_chart_colors()
    }
