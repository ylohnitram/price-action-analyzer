#!/usr/bin/env python3

import logging
import argparse
import sys
import os
from datetime import datetime

from src.clients.binance_client import BinanceClient
from src.analysis.price_action import PriceActionAnalyzer
from src.notification.telegram_bot import TelegramBot
from src.utils.helpers import (
    setup_logging, 
    validate_interval, 
    validate_days,
    save_data_to_csv,
    get_required_env_vars
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """Zpracuje a vrátí argumenty příkazové řádky."""
    parser = argparse.ArgumentParser(description='Price Action Analyzer')
    parser.add_argument('-s', '--symbol', type=str, default='BTCUSDT',
                        help='Trading pár (např. BTCUSDT)')
    parser.add_argument('-i', '--interval', type=str, default='30m',
                        choices=['1m','3m','5m','15m','30m','1h','2h','4h','6h','8h','12h','1d','1w'],
                        help='Časový interval (pouze pro single-timeframe analýzu)')
    parser.add_argument('-d', '--days', type=int, default=3,
                        help='Počet dní historie (pouze pro single-timeframe analýzu)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--multi', action='store_true',
                        help='Použít kompletní multi-timeframe analýzu (všechny timeframy)')
    group.add_argument('--intraday', action='store_true',
                        help='Použít intraday analýzu (pouze 5m, 15m, 1h, 4h)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Podrobnější výpisy')
    
    return parser.parse_args()

def run_intraday_analysis(symbol):
    """
    Spustí intraday analýzu zaměřenou na kratší časové rámce.
    
    Args:
        symbol (str): Obchodní symbol
        
    Returns:
        bool: True pokud byla analýza úspěšně dokončena
    """
    # Kontrola proměnných prostředí
    env_vars = get_required_env_vars()
    
    logger.info(f"Spouštím intraday analýzu pro {symbol}")
    
    # Inicializace klientů
    binance_client = BinanceClient()
    analyzer = PriceActionAnalyzer(api_key=env_vars['OPENAI_API_KEY'])
    telegram_bot = TelegramBot(
        token=env_vars['TELEGRAM_TOKEN'],
        chat_id=env_vars['TELEGRAM_CHAT_ID']
    )
    
    try:
        # Stažení dat pouze pro intraday timeframy
        logger.info("Stahuji intraday data z Binance")
        intraday_data = binance_client.fetch_intraday_data(symbol)
        
        if not intraday_data:
            logger.error("Nepodařilo se stáhnout žádná data")
            return False
            
        timeframes_with_data = list(intraday_data.keys())
        logger.info(f"Stažena data pro timeframy: {timeframes_with_data}")
        
        # Zpracování dat
        logger.info("Zpracovávám data")
        dataframes = analyzer.process_multi_timeframe_data(intraday_data)
        
        # Generování analýzy
        logger.info("Generuji intraday AI analýzu")
        analysis = analyzer.generate_intraday_analysis(symbol, dataframes)
        
        # Odeslání výsledků
        message = f"**Intraday Price Action Analýza {symbol}**\n\n{analysis}"
        logger.info("Odesílám analýzu na Telegram")
        telegram_bot.send_message(message)
        
        # Uložení dat
        for tf, df in dataframes.items():
            filename = save_data_to_csv(df, symbol, tf)
            logger.info(f"Data {tf} uložena do: {filename}")
        
        logger.info("Intraday analýza úspěšně dokončena")
        return True
        
    except Exception as e:
        logger.error(f"Chyba během intraday analýzy: {str(e)}")
        return False

def main():
    """Hlavní funkce programu."""
    # Parsování argumentů
    args = parse_arguments()
    
    # Nastavení loggeru
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(level=log_level)
    
    # Spuštění analýzy
    try:
        if args.multi:
            logger.info("Spouštím kompletní multi-timeframe analýzu")
            success = run_multi_timeframe_analysis(args.symbol)
        elif args.intraday:
            logger.info("Spouštím intraday analýzu")
            success = run_intraday_analysis(args.symbol)
        else:
            logger.info("Spouštím single-timeframe analýzu")
            success = run_analysis(args.symbol, args.interval, args.days)
            
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Operace přerušena uživatelem")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Neočekávaná chyba: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
