#!/usr/bin/env python3

import time
import requests
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
import random

# Vypnout SSL varování
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BinanceClient:
    """Klient pro komunikaci s Binance API."""
    
    def __init__(self):
        self.session = self._create_session()
        
        # Seznam alternativních domén a API endpointů pro obejití regionálních omezení
        self.api_domains = [
            "https://api1.binance.com",
            "https://api2.binance.com",
            "https://api3.binance.com",
            "https://api.binance.com"
        ]
        
        # Alternativně můžeme použít Binance Futures API, které může být přístupné i při blokování hlavního API
        self.futures_domains = [
            "https://fapi.binance.com",
            "https://dapi.binance.com"
        ]
        
        # Výchozí nastavení - začínáme se standardním API
        self.base_url = self.api_domains[0]
        self.use_futures_api = False
        
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

    def _try_next_domain(self):
        """Zkusí další doménu, pokud je aktuální blokovaná."""
        if not self.use_futures_api:
            # Zkusíme nejprve další standardní API doménu
            current_index = self.api_domains.index(self.base_url)
            next_index = (current_index + 1) % len(self.api_domains)
            self.base_url = self.api_domains[next_index]
            print(f"Zkouším alternativní API doménu: {self.base_url}")
            
            # Pokud jsme prošli všechny API domény, přejdeme na Futures API
            if next_index == 0:
                self.use_futures_api = True
                self.base_url = self.futures_domains[0]
                print(f"Přepínám na Futures API: {self.base_url}")
        else:
            # Zkusíme další Futures API doménu
            current_index = self.futures_domains.index(self.base_url)
            next_index = (current_index + 1) % len(self.futures_domains)
            self.base_url = self.futures_domains[next_index]
            print(f"Zkouším alternativní Futures API doménu: {self.base_url}")

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
        max_retries = 5  # Maximální počet pokusů s různými doménami
        retries = 0
        
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
                retries = 0  # Reset počtu pokusů po úspěšném stažení
                
            except Exception as e:
                error_msg = f"Chyba při stahování dat: {str(e)}"
                if show_progress:
                    tqdm.write(f"\n{error_msg}")
                
                # Zkusíme použít jinou doménu, pokud došlo k chybě 451 (regionální blokování)
                if "451" in str(e) and retries < max_retries:
                    self._try_next_domain()
                    retries += 1
                    time.sleep(1)  # Chvíli počkáme před dalším pokusem
                    continue  # Zkusíme znovu se stejným časovým úsekem
                
                time.sleep(5)  # Delší pauza při jiných chybách
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
            # Různé endpointy podle typu API (standardní vs futures)
            endpoint = "/fapi/v1/klines" if self.use_futures_api else "/api/v3/klines"
            url = f"{self.base_url}{endpoint}"
            
            params = {
                'symbol': symbol,
                'interval': interval,
                'startTime': start_time,
                'endTime': end_time,
                'limit': limit
            }
            
            # Přidáme náhodný User-Agent pro snížení šance detekce automatizovaného přístupu
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
            ]
            
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'application/json'
            }

            response = self.session.get(
                url,
                params=params,
                headers=headers,
                verify=True,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Chyba při stahování dat: {str(e)}")
