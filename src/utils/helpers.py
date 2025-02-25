#!/usr/bin/env python3

import os
import logging
from datetime import datetime
import pandas as pd

# Nastavení loggeru
def setup_logging(level=logging.INFO):
    """
    Nastaví základní konfiguraci loggeru.
    
    Args:
        level: Úroveň logování (default: logging.INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def validate_interval(interval):
    """
    Ověří, zda je časový interval platný.
    
    Args:
        interval (str): Časový interval
        
    Returns:
        bool: True pokud je interval platný
        
    Raises:
        ValueError: Pokud interval není platný
    """
    valid_intervals = ['1m','3m','5m','15m','30m','1h','2h','4h','6h','8h','12h','1d','1w']
    
    if interval not in valid_intervals:
        raise ValueError(f"Neplatný interval. Povolené hodnoty: {', '.join(valid_intervals)}")
    
    return True

def validate_days(days):
    """
    Ověří, zda je počet dní platný.
    
    Args:
        days (int): Počet dní
        
    Returns:
        bool: True pokud je počet dní platný
        
    Raises:
        ValueError: Pokud počet dní není platný
    """
    if not isinstance(days, int) or days <= 0 or days > 30:
        raise ValueError("Počet dní musí být kladné celé číslo menší než 30")
    
    return True

def save_data_to_csv(df, symbol, interval):
    """
    Uloží data do CSV souboru.
    
    Args:
        df (pandas.DataFrame): DataFrame k uložení
        symbol (str): Obchodní symbol
        interval (str): Časový interval
        
    Returns:
        str: Název vygenerovaného souboru
    """
    filename = f"PA_{symbol}_{interval}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    df.to_csv(filename)
    return filename

def get_required_env_vars():
    """
    Získá potřebné proměnné prostředí.
    
    Returns:
        dict: Slovník s proměnnými prostředí
        
    Raises:
        ValueError: Pokud chybí některá z potřebných proměnných
    """
    required_vars = {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'TELEGRAM_TOKEN': os.getenv('TELEGRAM_TOKEN'),
        'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID')
    }
    
    missing_vars = [var for var, value in required_vars.items() if not value]
    
    if missing_vars:
        raise ValueError(f"Chybí následující proměnné prostředí: {', '.join(missing_vars)}")
    
    return required_vars
