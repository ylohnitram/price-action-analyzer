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
    group.add_argument('--complete', action='store_true',
                        help='Použít kompletní analýzu (všechny timeframy)')
    group.add_argument('--multi', action='store_true',
                        help='Alias pro --complete (zpětná kompatibilita)')
    group.add_argument('--intraday', action='store_true',
                        help='Použít intraday analýzu (pouze 4h, 30m, 5m)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Podrobnější výpisy')
    parser.add_argument('--no-chart', action='store_true',
                        help='Nevytvářet grafy')
    
    return parser.parse_args()

def run_complete_analysis(symbol, no_chart=False):
    """
    Spustí kompletní analýzu pro všechny časové rámce.
    
    Args:
        symbol (str): Obchodní symbol
        no_chart (bool): Nevytvářet grafy
        
    Returns:
        bool: True pokud byla analýza úspěšně dokončena
    """
    # Kontrola proměnných prostředí
    env_vars = get_required_env_vars()
    
    logger.info(f"Spouštím kompletní analýzu pro {symbol}")
    
    # Inicializace klientů
    binance_client = BinanceClient()
    analyzer = PriceActionAnalyzer(api_key=env_vars['OPENAI_API_KEY'])
    telegram_bot = TelegramBot(
        token=env_vars['TELEGRAM_TOKEN'],
        chat_id=env_vars['TELEGRAM_CHAT_ID']
    )
    
    try:
        # Stažení multi-timeframe dat
        logger.info("Stahuji kompletní data z Binance")
        multi_tf_data = binance_client.fetch_multi_timeframe_data(symbol)
        
        if not multi_tf_data:
            logger.error("Nepodařilo se stáhnout žádná data")
            return False
            
        timeframes_with_data = list(multi_tf_data.keys())
        logger.info(f"Stažena data pro timeframy: {timeframes_with_data}")
        
        # Zpracování dat
        logger.info("Zpracovávám data")
        dataframes = analyzer.process_multi_timeframe_data(multi_tf_data)
        
        # Generování analýzy
        logger.info("Generuji kompletní AI analýzu")
        analysis, support_zones, resistance_zones = analyzer.generate_multi_timeframe_analysis(symbol, dataframes)
        
        # Generování grafu
        chart_path = None
        if not no_chart and '1d' in dataframes:
            logger.info("Generuji graf s cenovými zónami")
            chart_path = analyzer.generate_chart(
                dataframes['1d'], 
                support_zones, 
                resistance_zones, 
                symbol
            )
            logger.info(f"Graf vygenerován: {chart_path}")
        
        # Odeslání výsledků
        logger.info("Odesílám analýzu na Telegram")
        if chart_path:
            telegram_bot.send_analysis_with_chart(analysis, chart_path)
        else:
            telegram_bot.send_message(analysis)
        
        # Uložení dat
        for tf, df in dataframes.items():
            filename = save_data_to_csv(df, symbol, tf)
            logger.info(f"Data {tf} uložena do: {filename}")
        
        logger.info("Kompletní analýza úspěšně dokončena")
        return True
        
    except Exception as e:
        logger.error(f"Chyba během kompletní analýzy: {str(e)}")
        return False

def run_intraday_analysis(symbol, no_chart=False):
    """
    Spustí intraday analýzu zaměřenou na kratší časové rámce.
    
    Args:
        symbol (str): Obchodní symbol
        no_chart (bool): Nevytvářet grafy
        
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
        analysis, support_zones, resistance_zones = analyzer.generate_intraday_analysis(symbol, dataframes)
        
        # Generování grafu
        chart_path = None
        if not no_chart and '4h' in dataframes:
            logger.info("Generuji graf s cenovými zónami")
            chart_path = analyzer.generate_chart(
                dataframes['4h'], 
                support_zones, 
                resistance_zones, 
                symbol
            )
            logger.info(f"Graf vygenerován: {chart_path}")
        
        # Odeslání výsledků
        logger.info("Odesílám analýzu na Telegram")
        if chart_path:
            telegram_bot.send_analysis_with_chart(analysis, chart_path)
        else:
            telegram_bot.send_message(analysis)
        
        # Uložení dat
        for tf, df in dataframes.items():
            filename = save_data_to_csv(df, symbol, tf)
            logger.info(f"Data {tf} uložena do: {filename}")
        
        logger.info("Intraday analýza úspěšně dokončena")
        return True
        
    except Exception as e:
        logger.error(f"Chyba během intraday analýzy: {str(e)}")
        return False

def run_analysis(symbol, interval, days, no_chart=False):
    """
    Spustí analýzu pro jeden časový rámec.
    
    Args:
        symbol (str): Obchodní symbol
        interval (str): Časový interval
        days (int): Počet dní historie
        no_chart (bool): Nevytvářet grafy
        
    Returns:
        bool: True pokud byla analýza úspěšně dokončena
    """
    # Ověření vstupních parametrů
    validate_interval(interval)
    validate_days(days)
    
    # Kontrola proměnných prostředí
    env_vars = get_required_env_vars()
    
    logger.info(f"Spouštím analýzu pro {symbol} ({interval}), historie: {days} dní")
    
    # Inicializace klientů
    binance_client = BinanceClient()
    analyzer = PriceActionAnalyzer(api_key=env_vars['OPENAI_API_KEY'])
    telegram_bot = TelegramBot(
        token=env_vars['TELEGRAM_TOKEN'],
        chat_id=env_vars['TELEGRAM_CHAT_ID']
    )
    
    try:
        # Stažení dat
        logger.info(f"Stahuji data z Binance")
        klines_data = binance_client.fetch_historical_data(symbol, interval, days)
        logger.info(f"Staženo {len(klines_data)} svíček")
        
        # Zpracování dat
        df = analyzer.process_data(klines_data)
        
        # Detekce patternů
        logger.info("Detekuji price action patterny")
        patterns = analyzer.detect_patterns(df)
        logger.info(f"Detekováno {len(patterns)} patternů")
        
        # Generování analýzy
        logger.info("Generuji AI analýzu")
        analysis, support_zones, resistance_zones = analyzer.generate_analysis(symbol, df, patterns)
        
        # Generování grafu
        chart_path = None
        if not no_chart:
            logger.info("Generuji graf s cenovými zónami")
            chart_path = analyzer.generate_chart(df, support_zones, resistance_zones, symbol)
            logger.info(f"Graf vygenerován: {chart_path}")
        
        # Odeslání výsledků
        logger.info("Odesílám analýzu na Telegram")
        if chart_path:
            telegram_bot.send_analysis_with_chart(analysis, chart_path)
        else:
            telegram_bot.send_message(analysis)
        
        # Uložení dat
        filename = save_data_to_csv(df, symbol, interval)
        logger.info(f"Data uložena do: {filename}")
        
        logger.info("Analýza úspěšně dokončena")
        return True
        
    except Exception as e:
        logger.error(f"Chyba během analýzy: {str(e)}")
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
        if args.complete or args.multi:  # Podpora obou variant
            logger.info("Spouštím kompletní analýzu")
            success = run_complete_analysis(args.symbol, args.no_chart)
        elif args.intraday:
            logger.info("Spouštím intraday analýzu")
            success = run_intraday_analysis(args.symbol, args.no_chart)
        else:
            logger.info("Spouštím single-timeframe analýzu")
            success = run_analysis(args.symbol, args.interval, args.days, args.no_chart)
            
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Operace přerušena uživatelem")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Neočekávaná chyba: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
