from datetime import datetime, timedelta
import pandas as pd

def extend_dates_for_projection(last_date, projection_days):
    """
    Vytvoří seznam budoucích dat pro projekci.
    
    Args:
        last_date: Poslední datum v datech
        projection_days (int): Počet dní projekce
        
    Returns:
        list: Seznam datetime objektů pro projekci
    """
    return [last_date + timedelta(days=i) for i in range(1, projection_days + 1)]

def get_timeframe_delta(timeframe):
    """
    Vrátí timedeltu odpovídající danému timeframu.
    
    Args:
        timeframe (str): Časový rámec (např. '1d', '4h', '30m')
        
    Returns:
        timedelta: Odpovídající časový interval
    """
    # Parsování hodnoty a jednotky
    value = int(timeframe[:-1])
    unit = timeframe[-1]
    
    if unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    elif unit == 'w':
        return timedelta(weeks=value)
    else:
        raise ValueError(f"Neznámý timeframe: {timeframe}")

def limit_data_by_time(df, days=None, hours=None):
    """
    Ořízne DataFrame na požadovaný časový rozsah.
    
    Args:
        df (pandas.DataFrame): DataFrame s datetime indexem
        days (int, optional): Počet dní dat
        hours (int, optional): Počet hodin dat
        
    Returns:
        pandas.DataFrame: Oříznutý DataFrame
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
        
    end_date = df.index.max()
    
    if hours:
        start_date = end_date - timedelta(hours=hours)
    elif days:
        start_date = end_date - timedelta(days=days)
    else:
        return df  # Bez omezení
    
    return df[df.index >= start_date].copy()
