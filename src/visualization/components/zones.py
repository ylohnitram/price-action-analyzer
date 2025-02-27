import numpy as np
import logging

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
    
    # Seřazení zón vzestupně podle ceny
    sorted_zones = sorted(zones, key=lambda x: x[0])
    
    for i, (s_min, s_max) in enumerate(sorted_zones):
        if not (np.isnan(s_min) or np.isnan(s_max)):
            # Použití správné barvy pro zónu
            color_idx = min(i, len(colors) - 1)
            color = colors[color_idx]
            
            # Přidání vyplněné oblasti pro supportní zónu
            ax.axhspan(s_min, s_max, facecolor=color, alpha=0.3, label=f'Support Zone' if i == 0 else "")
            
            # Přidání horizontálních čar na hranicích zóny pro lepší viditelnost
            ax.axhline(y=s_min, color=color, linestyle='-', linewidth=1.0, alpha=0.7)
            ax.axhline(y=s_max, color=color, linestyle='-', linewidth=1.0, alpha=0.7)
            
            # Přidání textového popisku pro supportní zónu
            mid_point = (s_min + s_max) / 2
            ax.text(
                start_date, 
                mid_point, 
                f"S{i+1}: {mid_point:.0f}", 
                color='white', 
                fontweight='bold', 
                fontsize=9,
                bbox=dict(
                    facecolor=color, 
                    alpha=0.9, 
                    edgecolor=color, 
                    boxstyle='round,pad=0.3'
                )
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
    
    # Seřazení zón vzestupně podle ceny
    sorted_zones = sorted(zones, key=lambda x: x[0])
    
    for i, (r_min, r_max) in enumerate(sorted_zones):
        if not (np.isnan(r_min) or np.isnan(r_max)):
            # Použití správné barvy pro zónu
            color_idx = min(i, len(colors) - 1)
            color = colors[color_idx]
            
            # Přidání vyplněné oblasti pro resistenční zónu
            ax.axhspan(r_min, r_max, facecolor=color, alpha=0.3, label=f'Resistance Zone' if i == 0 else "")
            
            # Přidání horizontálních čar na hranicích zóny pro lepší viditelnost
            ax.axhline(y=r_min, color=color, linestyle='-', linewidth=1.0, alpha=0.7)
            ax.axhline(y=r_max, color=color, linestyle='-', linewidth=1.0, alpha=0.7)
            
            # Přidání textového popisku pro resistenční zónu
            mid_point = (r_min + r_max) / 2
            ax.text(
                start_date, 
                mid_point, 
                f"R{i+1}: {mid_point:.0f}", 
                color='white', 
                fontweight='bold', 
                fontsize=9,
                bbox=dict(
                    facecolor=color, 
                    alpha=0.9, 
                    edgecolor=color, 
                    boxstyle='round,pad=0.3'
                )
            )
            
            zone_added = True
            
    return zone_added
