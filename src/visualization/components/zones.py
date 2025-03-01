import matplotlib
# Nastavení neinteraktivního backend před importem pyplot
matplotlib.use('Agg')

import numpy as np
import logging
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

logger = logging.getLogger(__name__)

def draw_support_zones(ax, zones, start_date, colors):
    """
    Vykreslí supportní zóny do grafu.
    
    Args:
        ax: Matplotlib osa
        zones (list): Seznam zón jako (min, max) tuples
        start_date: Počáteční datum v grafu
        colors (list): Seznam barev pro zóny
        
    Returns:
        bool: True pokud byla přidána alespoň jedna zóna
    """
    if not zones:
        return False
        
    zone_added = False
    
    # Získání limitů x-osy
    xlim = ax.get_xlim()
    xrange = xlim[1] - xlim[0]
    
    # Explicitně definované zelené barvy
    support_colors = ['#006400', '#008000', '#228B22', '#32CD32']
    
    # Seřazení zón vzestupně podle ceny
    sorted_zones = sorted(zones, key=lambda x: x[0])
    
    for i, (s_min, s_max) in enumerate(sorted_zones):
        if not (np.isnan(s_min) or np.isnan(s_max)):
            # Použití správné barvy pro zónu
            color_idx = min(i, len(support_colors) - 1)
            color = support_colors[color_idx]
            
            # Vytvoření obdélníku pro zónu přes celou šířku grafu
            rect = Rectangle(
                (xlim[0], s_min),  # (x, y) levého dolního rohu
                xrange,  # šířka = celá viditelná část grafu
                s_max - s_min,  # výška = rozsah zóny
                facecolor=color,
                alpha=0.2,  # průhlednost
                edgecolor=color,
                linestyle='--',
                linewidth=1,
                zorder=1
            )
            ax.add_patch(rect)
            
            # Přidání popisku
            mid_point = (s_min + s_max) / 2
            ax.text(
                xlim[0] + xrange * 0.02,  # 2% od levého okraje
                mid_point,
                f"S{i+1}: {mid_point:.0f}",
                color='white',
                fontweight='bold',
                fontsize=9,
                bbox=dict(
                    facecolor=color,
                    alpha=0.7,
                    boxstyle='round,pad=0.3'
                ),
                zorder=4
            )
            
            zone_added = True
            
    return zone_added

def draw_resistance_zones(ax, zones, start_date, colors):
    """
    Vykreslí resistenční zóny do grafu.
    
    Args:
        ax: Matplotlib osa
        zones (list): Seznam zón jako (min, max) tuples
        start_date: Počáteční datum v grafu
        colors (list): Seznam barev pro zóny
        
    Returns:
        bool: True pokud byla přidána alespoň jedna zóna
    """
    if not zones:
        return False
        
    zone_added = False
    
    # Získání limitů x-osy
    xlim = ax.get_xlim()
    xrange = xlim[1] - xlim[0]
    
    # Explicitně definované červené barvy - všechny v červeném odstínu
    resistance_colors = ['#FF0000', '#FF3333', '#FF6666', '#FF9999']
    
    # Seřazení zón vzestupně podle ceny
    sorted_zones = sorted(zones, key=lambda x: x[0])
    
    for i, (r_min, r_max) in enumerate(sorted_zones):
        if not (np.isnan(r_min) or np.isnan(r_max)):
            # Použití správné barvy pro zónu - vždy červená
            color_idx = min(i, len(resistance_colors) - 1)
            color = resistance_colors[color_idx]
            
            # Vytvoření obdélníku pro zónu přes celou šířku grafu
            rect = Rectangle(
                (xlim[0], r_min),  # (x, y) levého dolního rohu
                xrange,  # šířka = celá viditelná část grafu
                r_max - r_min,  # výška = rozsah zóny
                facecolor=color,
                alpha=0.2,  # průhlednost
                edgecolor=color,
                linestyle='--',
                linewidth=1,
                zorder=1
            )
            ax.add_patch(rect)
            
            # Přidání popisku
            mid_point = (r_min + r_max) / 2
            ax.text(
                xlim[0] + xrange * 0.02,  # 2% od levého okraje
                mid_point,
                f"R{i+1}: {mid_point:.0f}",
                color='white',
                fontweight='bold',
                fontsize=9,
                bbox=dict(
                    facecolor=color,
                    alpha=0.7,
                    boxstyle='round,pad=0.3'
                ),
                zorder=4
            )
            
            zone_added = True
            
    return zone_added
