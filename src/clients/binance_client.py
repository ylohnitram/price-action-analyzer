#!/usr/bin/env python3

import time
import requests
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3

# Vypnout SSL varování
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BinanceClient:
    """Klient pro komunikaci s Binance API."""
    
    def __init__(self):
        self.session = self._create_session()
        self.base_url = "https://api.binance.com"

    def _create_session(self):
        """Vytvoří HTTP session s retry strategií."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def fetch_historical_data(self, symbol, interval, days, progress_callback=None):
        """
        Stáhne historická OHLCV data z Binance pro jeden časový rámec.
        
        Args:
            symbol (str): Obchodní symbol (např. 'BTCUSDT')
            interval (str): Časový interval (např. '1h', '15m')
            days (int): Počet dní historie ke stažení
            progress_callback (callable, optional): Funkce pro zpětné volání s informací o průběhu
            
        Returns:
            list: Seznam stažených svíček
        """
        end_time = int(time.time() * 1000)
        start_time = end_time - (days * 24 * 60 * 60 * 1000)
        
        all_klines = []
        chunk_size = 6 * 60 * 60 * 1000  # 6 hodin v milisekundách
        total_chunks = (end_time - start_time) // chunk_size + 1
        
        show_progress = progress_callback is None
        pbar = tqdm(total=total_chunks, desc=f"Stahování {symbol} {interval}", unit="chunk") if show_progress else None
        
        current_start = start_time
        while current_start < end_time:
            chunk_end = min(current_start + chunk_size, end_time)
            
            try:
                klines = self.get_klines(
                    symbol=symbol,
                    interval=interval,
                    start_time=current_start,
                    end_time=chunk_end
                )
                
                if klines:
                    all_klines.extend(klines)
                    current_start = klines[-1][0] + 1
                else:
                    current_start = chunk_end + 1
                
                if show_progress:
                    pbar.update(1)
                elif progress_callback:
                    progress_callback(len(all_klines))
                    
                time.sleep(0.5)  # Předejití rate limitu
                
            except Exception as e:
                error_msg = f"Chyba při stahování dat: {str(e)}"
                if show_progress:
                    tqdm.write(f"\n{error_msg}")
                time.sleep(5)  # Delší pauza při chybě
                current_start = chunk_end + 1
                if show_progress:
                    pbar.update(1)
        
        if show_progress:
            pbar.close()
            
        if not all_klines:
            raise Exception("Nepodařilo se stáhnout žádná data")
            
        return all_klines

    def fetch_intraday_data(self, symbol):
    """
    Stáhne OHLCV data pro intraday analýzu s přesně specifikovanými timeframy.
    
    Args:
        symbol (str): Obchodní symbol (např. 'BTCUSDT')
        
    Returns:
        dict: Slovník DataFrame s daty pro intraday timeframy
    """
    print(f"Stahuji intraday data pro {symbol}...")
    
    # Definice časových rámců přesně dle zadání uživatele
    timeframes = {
        "4h": 30,     # 4-hodinová data - období 1 měsíce
        "30m": 7,     # 30-minutová data - období 1 týdne 
        "5m": 3       # 5-minutová data - období 3 dnů
    }
    
    results = {}
    
    for interval, days in timeframes.items():
        try:
            print(f"Stahuji {interval} data za posledních {days} dní...")
            klines_data = self.fetch_historical_data(symbol, interval, days)
            results[interval] = klines_data
            print(f"Staženo {len(klines_data)} svíček pro {interval}")
            
            # Pauza mezi požadavky
            time.sleep(1)
            
        except Exception as e:
            print(f"Chyba při stahování {interval} dat: {str(e)}")
    
    return results

    def fetch_multi_timeframe_data(self, symbol):
        """
        Stáhne OHLCV data pro specifické časové rámce dle zadání.
        
        Args:
            symbol (str): Obchodní symbol (např. 'BTCUSDT')
            
        Returns:
            dict: Slovník DataFrame s daty pro různé časové rámce
        """
        print(f"Stahuji multi-timeframe data pro {symbol}...")
        
        # Definice časových rámců přesně dle požadavku
        timeframes = {
            "1w": 52,     # Weekly data - 1 rok
            "1d": 90,     # Daily data - 3 měsíce
            "4h": 30,     # 4-hodinová data - 1 měsíc
            "30m": 7,     # 30-minutová data - 1 týden
            "5m": 3       # 5-minutová data - 3 dny
        }
        
        results = {}
        
        for interval, days in timeframes.items():
            try:
                print(f"Stahuji {interval} data za posledních {days} dní...")
                klines_data = self.fetch_historical_data(symbol, interval, days)
                results[interval] = klines_data
                print(f"Staženo {len(klines_data)} svíček pro {interval}")
                
                # Pauza mezi požadavky
                time.sleep(1)
                
            except Exception as e:
                print(f"Chyba při stahování {interval} dat: {str(e)}")
        
        return results

    def get_klines(self, symbol, interval, start_time, end_time, limit=1000):
        """
        Stáhne svíčková data pro daný symbol a interval.
        
        Args:
            symbol (str): Obchodní symbol
            interval (str): Časový interval
            start_time (int): Počáteční čas v milisekundách
            end_time (int): Koncový čas v milisekundách
            limit (int, optional): Maximální počet svíček (default: 1000)
            
        Returns:
            list: Seznam svíček
        """
        try:
            url = f"{self.base_url}/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': start_time,
                'endTime': end_time,
                'limit': limit
            }

            response = self.session.get(
                url,
                params=params,
                verify=True,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Chyba při stahování dat: {str(e)}")
