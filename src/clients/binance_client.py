#!/usr/bin/env python3

import time
import requests
import os
import random
import logging
from tqdm import tqdm
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import urllib3
import socket

# Vypnout SSL varování
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)

class BinanceClient:
    """Klient pro komunikaci s Binance API s vylepšeným ošetřením chyb."""
    
    def __init__(self):
        self.session = self._create_session()
        
        # Seznam alternativních domén a API endpointů pro obejití regionálních omezení
        self.api_domains = [
            "https://api1.binance.com",
            "https://api2.binance.com",
            "https://api3.binance.com",
            "https://api.binance.com",
            "https://api-gcp.binance.com",
            "https://api-aws.binance.com",
            "https://public.bnbstatic.com/api" # Záložní alternativa
        ]
        
        # Alternativní Binance Futures API
        self.futures_domains = [
            "https://fapi.binance.com",
            "https://dapi.binance.com",
            "https://fapi1.binance.com",
            "https://fapi2.binance.com"
        ]
        
        # Binance Spot API domény pro různé regiony
        self.regional_domains = [
            "https://api.binance.us",     # US
            "https://api.binance.je",     # Jersey
            "https://api.binance.co.uk",  # UK
            "https://api.binance.de",     # Germany
            "https://api.binance.it",     # Italy
            "https://api.binance.fr"      # France
        ]
        
        # Výchozí nastavení - začínáme se standardním API
        self.base_url = self.api_domains[0]
        self.use_futures_api = False
        self.tried_domains = set()
        
        # Timeout konfigurace - prodloužíme timeout
        self.connect_timeout = 15  # Timeout pro navázání spojení
        self.read_timeout = 60     # Timeout pro čtení dat
        
        # Náhodné rozložení pokusů
        self.retry_min_wait = 1    # Minimální doba čekání mezi pokusy v sekundách
        self.retry_max_wait = 10   # Maximální doba čekání mezi pokusy v sekundách
        self.max_consecutive_errors = 5  # Maximum po sobě jdoucích chyb
        
        logger.info(f"Binance klient inicializován s první API doménou: {self.base_url}")
        
    def _create_session(self):
        """Vytvoří HTTP session s vylepšenou retry strategií a proxy podporou."""
        session = requests.Session()
        
        # Přidání proxy pro GitHub Actions
        proxy_url = os.environ.get('PROXY_URL')
        if proxy_url:
            session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            # Bezpečný výpis bez hesla
            safe_proxy = proxy_url.replace('http://', '').replace('https://', '')
            if '@' in safe_proxy:
                safe_proxy = safe_proxy.split('@')[1]
            logger.info(f"Používám proxy: {safe_proxy}")
        
        # Vylepšená retry strategie
        retry_strategy = Retry(
            total=5,  # Zvýšení celkového počtu pokusů
            backoff_factor=2,  # Exponenciální backoff faktor zvýšen
            status_forcelist=[429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525],
            allowed_methods=["GET", "POST"],  # Povolené metody pro retry
            respect_retry_after_header=True,  # Respektovat Retry-After hlavičku
            # Pro HTTP/1.1 (defaultní) je výchozí počet redirection 30, pro HTTP/2 je 0.
            # Zvýšíme redirect limit pro HTTP/2 pokud by byl použit
            redirect=10
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Nastavení user-agent
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        session.headers.update(default_headers)
        
        return session

    def _get_next_domain(self):
        """
        Získá další doménu pro pokus, zajišťuje že projdeme všechny dostupné domény.
        
        Returns:
            str: URL další domény k vyzkoušení
        """
        # Kombinace všech možných domén
        all_domains = self.api_domains + self.futures_domains + self.regional_domains
        
        # Odstranění již vyzkoušených domén
        available_domains = [d for d in all_domains if d not in self.tried_domains]
        
        # Pokud už jsme vyzkoušeli všechny domény, resetujeme seznam a začneme znovu
        if not available_domains:
            logger.warning("Všechny dostupné domény již byly vyzkoušeny, resetuji seznam")
            self.tried_domains = set()
            available_domains = all_domains
        
        # Vybereme náhodně z dostupných domén pro lepší rozložení
        next_domain = random.choice(available_domains)
        self.tried_domains.add(next_domain)
        
        # Aktualizujeme informaci o typu API
        self.use_futures_api = any(f_domain in next_domain for f_domain in self.futures_domains)
        
        logger.info(f"Přepínám na novou doménu: {next_domain} (futures API: {self.use_futures_api})")
        return next_domain

    def _try_next_domain(self):
        """Zkusí další doménu, pokud je aktuální blokovaná nebo nedostupná."""
        self.base_url = self._get_next_domain()
        # Přidáme malé zpoždění před použitím nové domény
        jitter = random.uniform(0.5, 2.0)
        time.sleep(jitter)

    def fetch_historical_data(self, symbol, interval, days, progress_callback=None):
        """
        Stáhne historická OHLCV data z Binance pro jeden časový rámec
        s vylepšeným ošetřením chyb a automatickou změnou koncových bodů.
        
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
        # Zmenšení velikosti chunků pro spolehlivější stahování
        chunk_size = 3 * 60 * 60 * 1000  # 3 hodiny v milisekundách místo 6 hodin
        total_chunks = (end_time - start_time) // chunk_size + 1
        
        show_progress = progress_callback is None
        pbar = tqdm(total=total_chunks, desc=f"Stahování {symbol} {interval}", unit="chunk") if show_progress else None
        
        current_start = start_time
        # Zvýšíme maximální počet chyb než se úplně vzdáme
        max_total_retries = 20
        total_retries = 0
        consecutive_errors = 0
        
        while current_start < end_time:
            chunk_end = min(current_start + chunk_size, end_time)
            
            try:
                # Zkrácení retry intervalu pro jednotlivé chunky
                klines = self._get_klines_with_retry(
                    symbol=symbol,
                    interval=interval,
                    start_time=current_start,
                    end_time=chunk_end,
                    max_retries=3  # Méně pokusů pro jednotlivé chunky
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
                    
                # Reset počtu po sobě jdoucích chyb po úspěchu
                consecutive_errors = 0
                
                # Přidání náhodného intervalu mezi požadavky pro snížení rizika rate limitů
                jitter = random.uniform(self.retry_min_wait, self.retry_min_wait * 1.5)
                time.sleep(jitter)
                
            except Exception as e:
                consecutive_errors += 1
                total_retries += 1
                error_msg = f"Chyba při stahování dat: {str(e)}"
                
                if show_progress:
                    tqdm.write(f"\n{error_msg}")
                logger.warning(error_msg)
                
                # Pokud jsme dosáhli maximálního počtu po sobě jdoucích chyb,
                # zkusíme změnit doménu a resetujeme počítadlo
                if consecutive_errors >= self.max_consecutive_errors:
                    logger.warning(f"Dosaženo {consecutive_errors} po sobě jdoucích chyb, měním API endpoint")
                    self._try_next_domain()
                    consecutive_errors = 0
                
                # Pokud jsme překročili maximální počet celkových pokusů, vzdáme to
                if total_retries >= max_total_retries:
                    if show_progress:
                        pbar.close()
                    logger.error(f"Překročen maximální počet pokusů ({max_total_retries}), ukončuji stahování")
                    break
                
                # Exponenciální backoff pro zpoždění mezi pokusy
                wait_time = min(self.retry_max_wait, self.retry_min_wait * (2 ** (consecutive_errors - 1)))
                wait_time = wait_time + random.uniform(0, 1)  # Přidání jitteru
                
                if show_progress:
                    tqdm.write(f"Čekám {wait_time:.2f}s před dalším pokusem...")
                time.sleep(wait_time)
                
                # Pokud došlo k chybě s konkrétním chunkem dat, posuneme se na další
                if consecutive_errors >= 2:
                    current_start = chunk_end + 1
                    if show_progress:
                        pbar.update(1)
                    tqdm.write(f"Přeskakuji problematický časový úsek, pokračuji dál")
                    consecutive_errors = 0
        
        if show_progress:
            pbar.close()
            
        if not all_klines:
            logger.error("Nepodařilo se stáhnout žádná data")
            raise Exception("Nepodařilo se stáhnout žádná data po opakovaných pokusech")
            
        logger.info(f"Úspěšně staženo {len(all_klines)} svíček pro {symbol} {interval}")
        return all_klines

    def _get_klines_with_retry(self, symbol, interval, start_time, end_time, limit=1000, max_retries=3):
        """
        Stáhne svíčková data s automatickým opakováním při chybě.
        
        Args:
            symbol (str): Obchodní symbol
            interval (str): Časový interval
            start_time (int): Počáteční čas v milisekundách
            end_time (int): Koncový čas v milisekundách
            limit (int, optional): Maximální počet svíček
            max_retries (int): Maximální počet pokusů
            
        Returns:
            list: Seznam svíček
        """
        retries = 0
        used_domains = set()
        last_exception = None
        
        while retries < max_retries and self.base_url not in used_domains:
            used_domains.add(self.base_url)
            
            try:
                return self._get_klines(symbol, interval, start_time, end_time, limit)
            except Exception as e:
                last_exception = e
                retries += 1
                logger.warning(f"Pokus {retries}/{max_retries} selhal: {str(e)}")
                
                # Přepneme na jinou doménu
                self._try_next_domain()
                # Přidání zpoždění před dalším pokusem
                time.sleep(random.uniform(1, 3))
        
        # Pokud jsme vyčerpali všechny pokusy, vyvoláme poslední výjimku
        if last_exception:
            raise last_exception
        else:
            raise Exception("Nepodařilo se stáhnout data po opakovaných pokusech")

    def fetch_intraday_data(self, symbol):
        """
        Stáhne OHLCV data pro intraday analýzu s vylepšenou spolehlivostí.
        
        Args:
            symbol (str): Obchodní symbol (např. 'BTCUSDT')
            
        Returns:
            dict: Slovník DataFrame s daty pro intraday timeframy
        """
        logger.info(f"Stahuji intraday data pro {symbol}...")
        
        # Definice časových rámců přesně dle zadání uživatele
        timeframes = {
            "4h": 30,     # 4-hodinová data - období 1 měsíce
            "30m": 7,     # 30-minutová data - období 1 týdne 
            "5m": 3       # 5-minutová data - období 3 dnů
        }
        
        results = {}
        
        for interval, days in timeframes.items():
            try:
                logger.info(f"Stahuji {interval} data za posledních {days} dní...")
                klines_data = self.fetch_historical_data(symbol, interval, days)
                results[interval] = klines_data
                logger.info(f"Staženo {len(klines_data)} svíček pro {interval}")
                
                # Pauza mezi požadavky s náhodnou dobou
                time.sleep(random.uniform(1.5, 3.0))
                
            except Exception as e:
                logger.error(f"Chyba při stahování {interval} dat: {str(e)}")
                # Pokračujeme s dalšími timeframy i když jeden selže
        
        if not results:
            logger.error("Nepodařilo se stáhnout žádná data pro žádný timeframe")
            raise Exception("Stahování intraday dat selhalo pro všechny timeframy")
            
        return results

    def fetch_multi_timeframe_data(self, symbol):
        """
        Stáhne OHLCV data pro timeframy používané ve swing analýze
        s vylepšenou spolehlivostí.
        
        Args:
            symbol (str): Obchodní symbol (např. 'BTCUSDT')
            
        Returns:
            dict: Slovník DataFrame s daty pro různé časové rámce
        """
        logger.info(f"Stahuji multi-timeframe data pro {symbol}...")
        
        # Definice časových rámců přesně dle požadavku
        timeframes = {
            "1w": 52,     # Weekly data - 1 rok
            "1d": 90,     # Daily data - 3 měsíce
            "4h": 30      # 4-hodinová data - 1 měsíc
        }
        
        results = {}
        
        for interval, days in timeframes.items():
            try:
                logger.info(f"Stahuji {interval} data za posledních {days} dní...")
                klines_data = self.fetch_historical_data(symbol, interval, days)
                results[interval] = klines_data
                logger.info(f"Staženo {len(klines_data)} svíček pro {interval}")
                
                # Pauza mezi požadavky s náhodnou dobou
                time.sleep(random.uniform(1.5, 3.0))
                
            except Exception as e:
                logger.error(f"Chyba při stahování {interval} dat: {str(e)}")
                # Pokračujeme s dalšími timeframy i když jeden selže
        
        if not results:
            logger.error("Nepodařilo se stáhnout žádná data pro žádný timeframe")
            raise Exception("Stahování multi-timeframe dat selhalo pro všechny timeframy")
            
        return results

    def _get_klines(self, symbol, interval, start_time, end_time, limit=1000):
        """
        Stáhne svíčková data pro daný symbol a interval s vylepšeným ošetřením chyb.
        
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
            
            # Rotace User-Agent pro snížení šance detekce automatizovaného přístupu
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
                "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0"
            ]
            
            # Přidání dalších hlaviček, které napodobují běžné prohlížeče
            headers = {
                'User-Agent': random.choice(user_agents),
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Origin': 'https://www.binance.com',
                'Referer': 'https://www.binance.com/'
            }

            # Explicitně nastavíme timeouty
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                verify=True,
                timeout=(self.connect_timeout, self.read_timeout)  # (connect timeout, read timeout)
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectTimeout as e:
            logger.error(f"Timeout při připojování k {self.base_url}: {str(e)}")
            raise Exception(f"Timeout při připojování k serveru: {str(e)}")
            
        except requests.exceptions.ReadTimeout as e:
            logger.error(f"Timeout při čtení dat z {self.base_url}: {str(e)}")
            raise Exception(f"Timeout při čtení dat ze serveru: {str(e)}")
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') and e.response is not None else "neznámý"
            logger.error(f"HTTP chyba {status_code} z {self.base_url}: {str(e)}")
            
            # Speciální zpracování chyb podle status kódu
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 429:
                    # Rate limit překročen
                    retry_after = e.response.headers.get('Retry-After', 60)
                    logger.warning(f"Rate limit překročen, čekání {retry_after}s před dalším pokusem")
                    time.sleep(int(retry_after))
                elif e.response.status_code in [403, 451]:
                    # Přístup zakázán nebo regionální blokování - určitě zkusit jinou doménu
                    logger.warning(f"Přístup blokován (kód {e.response.status_code}), zkusím jinou doménu")
                    self._try_next_domain()
            
            raise Exception(f"HTTP chyba {status_code}: {str(e)}")
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Problém s připojením k {self.base_url}: {str(e)}")
            raise Exception(f"Problém s připojením: {str(e)}")
            
        except socket.error as e:
            logger.error(f"Socket chyba pro {self.base_url}: {str(e)}")
            raise Exception(f"Síťová chyba: {str(e)}")
            
        except (ValueError, KeyError) as e:
            logger.error(f"Chyba při zpracování odpovědi z {self.base_url}: {str(e)}")
            raise Exception(f"Chyba při zpracování odpovědi: {str(e)}")
            
        except Exception as e:
            logger.error(f"Neočekávaná chyba při komunikaci s {self.base_url}: {str(e)}")
            raise Exception(f"Neočekávaná chyba: {str(e)}")
