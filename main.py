#!/usr/bin/env python3

import logging
import argparse
import sys
import os
import time
from datetime import datetime

from src.clients.binance_client import BinanceClient
from src.analysis.price_action import PriceActionAnalyzer
from src.visualization.chart_generator import ChartGenerator
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
    parser.add_argument('-d', '--days', type=int, default=5,
                        help='Počet dní historie (pouze pro single-timeframe analýzu)')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--swing', action='store_true',
                        help='Použít swing analýzu (všechny timeframy)')
    group.add_argument('--intraday', action='store_true',
                        help='Použít intraday analýzu (pouze 4h, 30m, 5m)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Podrobnější výpisy')
    parser.add_argument('--no-chart', action='store_true',
                        help='Nevytvářet grafy')
    parser.add_argument('--chart-days', type=int, default=5,
                        help='Počet dní dat k zobrazení v grafu (výchozí: 5)')
    
    return parser.parse_args()

def run_swing_analysis(symbol, no_chart=False, chart_days=5):
    """
    Spustí swing analýzu pro všechny časové rámce.
    
    Args:
        symbol (str): Obchodní symbol
        no_chart (bool): Nevytvářet grafy
        chart_days (int): Počet dní v grafu
        
    Returns:
        bool: True pokud byla analýza úspěšně dokončena
    """
    # Kontrola proměnných prostředí
    env_vars = get_required_env_vars()
    
    logger.info(f"Spouštím swing analýzu pro {symbol}")
    
    # Inicializace klientů
    binance_client = BinanceClient()
    analyzer = PriceActionAnalyzer(api_key=env_vars['OPENAI_API_KEY'])
    chart_generator = ChartGenerator()
    telegram_bot = TelegramBot(
        token=env_vars['TELEGRAM_TOKEN'],
        chat_id=env_vars['TELEGRAM_CHAT_ID']
    )
    
    try:
        # Stažení multi-timeframe dat
        logger.info("Stahuji data pro swing analýzu z Binance")
        multi_tf_data = binance_client.fetch_multi_timeframe_data(symbol)
        
        if not multi_tf_data:
            logger.error("Nepodařilo se stáhnout žádná data")
            return False
            
        timeframes_with_data = list(multi_tf_data.keys())
        logger.info(f"Stažena data pro timeframy: {timeframes_with_data}")
        
        # Zpracování dat
        logger.info("Zpracovávám data")
        dataframes = analyzer.process_multi_timeframe_data(multi_tf_data)
        
        # Výpis statistik pro lepší pochopení dat
        for tf, df in dataframes.items():
            logger.info(f"{tf} data: {len(df)} svíček od {df.index[0]} do {df.index[-1]}")
        
        # Generování analýzy
        logger.info("Generuji swing AI analýzu")
        analysis, support_zones, resistance_zones, scenarios = analyzer.generate_multi_timeframe_analysis(symbol, dataframes)
        
        # Přidáme nadpis k analýze
        analysis = f"# Swing Price Action Analýza {symbol}\n\n{analysis}"
        
        # Generování grafu - swing analýza používá daily timeframe pro graf
        chart_path = None
        chart_timeframe = '1d'
        
        # Pokud nemáme daily data, zkusíme 4h
        if chart_timeframe not in dataframes and '4h' in dataframes:
            chart_timeframe = '4h'
            logger.info(f"Daily data nejsou k dispozici, použiji {chart_timeframe} pro graf")
        
        if not no_chart and chart_timeframe in dataframes:
            logger.info(f"Generuji graf s cenovými zónami a scénáři za posledních {chart_days} dní")
            chart_data = dataframes[chart_timeframe]
            
            # Použití generátoru grafů
            chart_path = chart_generator.generate_chart(
                chart_data, 
                support_zones, 
                resistance_zones, 
                symbol,
                days_to_show=chart_days,
                timeframe=chart_timeframe,
                scenarios=scenarios,
                analysis_text=analysis,
                analysis_type="swing"  # Změna z "complete" na "swing"
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
        
        logger.info("Swing analýza úspěšně dokončena")
        return True
        
    except Exception as e:
        logger.error(f"Chyba během swing analýzy: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def run_analysis(symbol, interval, days, no_chart=False, chart_days=5):
    """
    Spustí analýzu pro jeden časový rámec.
    
    Args:
        symbol (str): Obchodní symbol
        interval (str): Časový interval
        days (int): Počet dní historie
        no_chart (bool): Nevytvářet grafy
        chart_days (int): Počet dní v grafu
        
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
    chart_generator = ChartGenerator()
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
        
        # Přidáme nadpis k analýze
        analysis = f"# Price Action Analýza {symbol} ({interval})\n\n{analysis}"
        
        # Generování grafu
        chart_path = None
        if not no_chart:
            logger.info(f"Generuji graf s cenovými zónami za posledních {chart_days} dní")
            chart_path = chart_generator.generate_chart(
                df, 
                support_zones, 
                resistance_zones, 
                symbol,
                days_to_show=chart_days,
                timeframe=interval,  # Předáváme informaci o timeframe
                analysis_text=analysis,
                analysis_type="simple"  # Přidání parametru pro typ analýzy
            )
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
        import traceback
        logger.error(traceback.format_exc())
        return False

def run_intraday_analysis(symbol, no_chart=False, chart_days=5):
    """
    Spustí intraday analýzu zaměřenou na kratší časové rámce.
    
    Args:
        symbol (str): Obchodní symbol
        no_chart (bool): Nevytvářet grafy
        chart_days (int): Počet dní v grafu (výchozí hodnota 5)
        
    Returns:
        bool: True pokud byla analýza úspěšně dokončena
    """
    # Kontrola proměnných prostředí
    env_vars = get_required_env_vars()
    
    logger.info(f"Spouštím intraday analýzu pro {symbol}")
    
    # Inicializace klientů
    binance_client = BinanceClient()
    analyzer = PriceActionAnalyzer(api_key=env_vars['OPENAI_API_KEY'])
    chart_generator = ChartGenerator()
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
        
        # Pro intraday analýzu - přidání logování pro diagnostiku dat
        for tf, df in dataframes.items():
            logger.info(f"{tf} data: {len(df)} svíček od {df.index[0]} do {df.index[-1]}")
            if len(df) > 0:
                logger.info(f"První svíčka {tf}: {df.iloc[0]['open']}, {df.iloc[0]['high']}, {df.iloc[0]['low']}, {df.iloc[0]['close']}, {df.iloc[0]['volume']}")
                logger.info(f"Poslední svíčka {tf}: {df.iloc[-1]['open']}, {df.iloc[-1]['high']}, {df.iloc[-1]['low']}, {df.iloc[-1]['close']}, {df.iloc[-1]['volume']}")
        
        # Generování analýzy
        logger.info("Generuji intraday AI analýzu")
        analysis, support_zones, resistance_zones = analyzer.generate_intraday_analysis(symbol, dataframes)
        
        # Přidáme nadpis k analýze
        analysis = f"# Intraday Price Action Analýza {symbol}\n\n{analysis}"
        
        # Generování grafu
        chart_path = None
        if not no_chart:
            # Pro intraday analýzu preferujeme 30m nebo 5m data
            if '30m' in dataframes:
                chart_tf = '30m'
            elif '5m' in dataframes:
                chart_tf = '5m'
            else:
                # Pokud nemáme intradenní data, neděláme graf
                logger.warning("Nedostatek vhodných intradenních dat pro graf")
                chart_tf = None
            
            if chart_tf:
                # Maximálně 48 hodin dat pro intraday graf
                hours_to_show = min(48, chart_days * 24)
                
                logger.info(f"Generuji graf z {chart_tf} dat za posledních {hours_to_show} hodin")
                
                # Určení počtu svíček podle timeframe s přihlédnutím k max. počtu 96 pro lepší viditelnost
                if chart_tf == '30m':
                    candles = min(int(hours_to_show * 2), 96)  # 2 svíčky za hodinu, max 96
                    logger.info(f"Počet 30m svíček k zobrazení: {candles}")
                elif chart_tf == '5m':
                    candles = min(int(hours_to_show * 12), 96)  # 12 svíček za hodinu, max 96
                    logger.info(f"Počet 5m svíček k zobrazení: {candles}")
                else:
                    candles = 96  # Výchozí max. počet svíček
                
                # Explicitní vybírání posledních candles svíček pro lepší kontrolu
                df_to_plot = dataframes[chart_tf].copy()
                if len(df_to_plot) > candles:
                    df_to_plot = df_to_plot.tail(candles)
                
                logger.info(f"Vybráno {len(df_to_plot)} svíček z celkových {len(dataframes[chart_tf])}")
                
                # Krátká pauza před generováním grafu pro jistotu
                time.sleep(1)
                
                chart_path = chart_generator.generate_chart(
                    df_to_plot,
                    support_zones, 
                    resistance_zones, 
                    symbol,
                    hours_to_show=hours_to_show,
                    timeframe=chart_tf,
                    analysis_text=analysis,
                    analysis_type="intraday"  # Přidáno pro specifikaci typu analýzy
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
        import traceback
        logger.error(traceback.format_exc())
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
        if args.swing:  # Změněno z complete/multi na swing
            logger.info("Spouštím swing analýzu")
            success = run_swing_analysis(args.symbol, args.no_chart, args.chart_days)
        elif args.intraday:
            logger.info("Spouštím intraday analýzu")
            success = run_intraday_analysis(args.symbol, args.no_chart, args.chart_days)
        else:
            logger.info("Spouštím single-timeframe analýzu")
            success = run_analysis(args.symbol, args.interval, args.days, args.no_chart, args.chart_days)
            
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Operace přerušena uživatelem")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Neočekávaná chyba: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
