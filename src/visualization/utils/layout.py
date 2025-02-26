def adjust_y_limits(ax, data, padding=0.05):
    """
    Upraví limity osy y pro optimální zobrazení dat.
    
    Args:
        ax: Matplotlib osa
        data: Data k zobrazení
        padding (float): Odsazení v procentech rozsahu
    """
    y_min = data.min()
    y_max = data.max()
    y_range = y_max - y_min
    
    # Přidání odsazení
    ax.set_ylim(y_min - y_range * padding, y_max + y_range * padding)

def optimize_chart_area(fig, ax_main, ax_volume, main_height_ratio=0.8):
    """
    Optimalizuje využití prostoru v grafu.
    
    Args:
        fig: Matplotlib figura
        ax_main: Hlavní osa grafu
        ax_volume: Osa pro objem
        main_height_ratio (float): Poměr výšky hlavního grafu k celkové výšce
    """
    # Nastavení výšky hlavního grafu a volume grafu
    fig.subplots_adjust(
        left=0.1,
        right=0.9,
        bottom=0.15,
        top=0.95,
        hspace=0.05
    )
    
    # Nastavení poměru výšky
    total_height = ax_main.get_position().height + ax_volume.get_position().height
    main_height = total_height * main_height_ratio
    volume_height = total_height * (1 - main_height_ratio)
    
    # Aktualizace pozic
    main_pos = ax_main.get_position()
    volume_pos = ax_volume.get_position()
    
    ax_main.set_position([main_pos.x0, volume_pos.y0 + volume_height, 
                          main_pos.width, main_height])
    ax_volume.set_position([volume_pos.x0, volume_pos.y0, 
                            volume_pos.width, volume_height])
