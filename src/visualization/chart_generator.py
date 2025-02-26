import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

from src.visualization.base_chart import BaseChart
from src.visualization.candlestick_chart import CandlestickChart
from src.visualization.config.timeframes import get_timeframe_config

logger = logging.getLogger(__name__)

class ChartGenerator:
    """
    Hlavní třída pro generování různých typů grafů.
    Funguje jako fasáda pro přístup k různým implementacím grafů.
    """
    
    def __init__(self):
        """Inicializace generátoru grafů."""
        pass
        
    def generate_chart(self, df, support_zones, resistance_zones, symbol, 
                       filename=None, days_to_show=2, hours_to_show=None, 
                       timeframe=None, scenarios=None):
        """
        Generuje graf podle zadaných parametrů.
        
        Args:
            df (pandas.DataFrame): DataFrame s OHLCV daty
            support_zones (list): Seznam supportních zón jako (min, max) tuple
            resistance_zones (list): Seznam resistenčních zón jako (min, max) tuple
            symbol (str): Obchodní symbol
            filename (str, optional): Výstupní soubor
            days_to_show (int, optional): Počet dní dat k zobrazení
            hours_to_show (int, optional): Počet hodin dat k zobrazení
            timeframe (str, optional): Časový rámec dat
            scenarios (list, optional): Seznam scénářů k vizualizaci
            
        Returns:
            str: Cesta k vygenerovanému souboru nebo None v případě chyby
        """
        logger.info(f"Generating chart for {symbol} ({timeframe})")
        
        # Vytvoření instance konkrétního typu grafu podle timeframe
        chart = CandlestickChart(
            df=df,
            symbol=symbol,
            timeframe=timeframe,
            days_to_show=days_to_show,
            hours_to_show=hours_to_show
        )
        
        # Přidání zón a scénářů
        chart.add_support_zones(support_zones)
        chart.add_resistance_zones(resistance_zones)
        
        if scenarios:
            chart.add_scenarios(scenarios)
            
        # Vykreslení grafu
        chart_path = chart.render(filename)
        
        if chart_path:
            logger.info(f"Chart saved: {chart_path}")
        
        return chart_path
