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
    Omezeno na maximálně 2 nejdůležitější zóny pro lepší přehlednost.

    Args:
        ax: Matplotlib osa
        zones (list): Seznam zón jako (min, max) tuples
        start_date: Počáteční datum v grafu
        colors (list): Seznam barev pro zóny

    Returns:
        bool: True pokud byla přidána alespoň jedna zóna
    """
    if not zones:
        logger.warning("Nebyly předány žádné supportní zóny k vykreslení")
        return False

    # Kontrola, zda zóny mají správný formát a rozumné hodnoty
    valid_zones = []
    for z_min, z_max in zones:
        try:
            # Převod na float pokud by hodnoty byly string
            if isinstance(z_min, str):
                z_min = float(z_min.replace(',', '.'))
            if isinstance(z_max, str):
                z_max = float(z_max.replace(',', '.'))

            # Kontroly platnosti zóny
            if np.isnan(z_min) or np.isnan(z_max):
                logger.warning(f"Ignoruji zónu s NaN hodnotami: {(z_min, z_max)}")
                continue
            if z_min < 0 or z_max < 0:
                logger.warning(f"Ignoruji zónu se zápornými hodnotami: {(z_min, z_max)}")
                continue
            if z_min > z_max:
                logger.warning(f"Ignoruji zónu s min > max: {(z_min, z_max)}")
                continue
            
            # Pro různé kryptoměny budou různé cenové rozsahy, proto
            # odstraníme specifickou kontrolu pro BTC a pouze zajistíme, aby byl rozsah rozumný
            if z_max > z_min * 10:
                logger.warning(f"Ignoruji zónu s příliš velkým rozsahem: {(z_min, z_max)}")
                continue
                
            valid_zones.append((z_min, z_max))
        except (ValueError, TypeError) as e:
            logger.warning(f"Chyba při zpracování zóny {(z_min, z_max)}: {str(e)}")
            continue

    # Omezíme na maximálně 2 zóny pro lepší přehlednost
    if len(valid_zones) > 2:
        logger.info(f"Omezuji počet supportních zón z {len(valid_zones)} na 2 pro lepší přehlednost")
        valid_zones = valid_zones[:2]

    if not valid_zones:
        logger.warning("Po ověření nezůstaly žádné platné supportní zóny")
        return False

    logger.info(f"Vykreslování {len(valid_zones)} supportních zón")
    zone_added = False

    # Získání limitů x-osy
    xlim = ax.get_xlim()
    xrange = xlim[1] - xlim[0]

    # Explicitně definované zelené barvy pro supports
    support_colors = ['#006400', '#008000']

    # Získání limitů y-osy pro kontrolu viditelnosti
    ylim = ax.get_ylim()
    y_min, y_max = ylim

    # Seřazení zón vzestupně podle ceny
    sorted_zones = sorted(valid_zones, key=lambda x: x[0])

    for i, (s_min, s_max) in enumerate(sorted_zones):
        # Kontrola, zda je zóna v rozsahu y-osy
        if s_max < y_min or s_min > y_max:
            logger.warning(f"Supportní zóna {(s_min, s_max)} je mimo viditelný rozsah ({y_min}, {y_max})")
            # Pokud je to první zóna, rozšíříme osu y
            if i == 0:
                logger.info(f"Rozšiřuji y-osu pro supportní zónu: {(s_min, s_max)}")
                new_y_min = min(y_min, s_min * 0.95)  # Přidáme 5% prostoru pod zónou
                new_y_max = max(y_max, s_max * 1.05)  # Přidáme 5% prostoru nad zónou
                ax.set_ylim(new_y_min, new_y_max)
            else:
                continue

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

        # Přidání popisku s kompletními informacemi o zóně
        mid_point = (s_min + s_max) / 2

        # Zaokrouhlení hodnot na celá čísla nebo na 1 desetinné místo pro menší hodnoty
        if s_min >= 100:
            s_min_formatted = int(round(s_min))
            s_max_formatted = int(round(s_max))
        else:
            s_min_formatted = round(s_min, 1)
            s_max_formatted = round(s_max, 1)

        # Vytvoření popisku s kompletními informacemi o zóně - jednodušší označení
        label_text = f"S{i+1}: {s_min_formatted}-{s_max_formatted}"

        # Přidání popisku v pravé části grafu (daleko od legendy)
        ax.text(
            xlim[0] + xrange * 0.85,  # 85% od levého okraje (blízko pravého okraje)
            mid_point,
            label_text,
            color='white',
            fontweight='bold',
            fontsize=9,
            bbox=dict(
                facecolor=color,
                alpha=0.7,
                boxstyle='round,pad=0.3'
            ),
            zorder=4,
            horizontalalignment='right'  # Zarovnání doprava
        )

        zone_added = True
        logger.info(f"Přidána supportní zóna {i+1}: {s_min}-{s_max}")

    return zone_added

def draw_resistance_zones(ax, zones, start_date, colors):
    """
    Vykreslí resistenční zóny do grafu.
    Omezeno na maximálně 2 nejdůležitější zóny pro lepší přehlednost.

    Args:
        ax: Matplotlib osa
        zones (list): Seznam zón jako (min, max) tuples
        start_date: Počáteční datum v grafu
        colors (list): Seznam barev pro zóny

    Returns:
        bool: True pokud byla přidána alespoň jedna zóna
    """
    if not zones:
        logger.warning("Nebyly předány žádné resistenční zóny k vykreslení")
        return False

    # Kontrola, zda zóny mají správný formát a rozumné hodnoty
    valid_zones = []
    for z_min, z_max in zones:
        try:
            # Převod na float pokud by hodnoty byly string
            if isinstance(z_min, str):
                z_min = float(z_min.replace(',', '.'))
            if isinstance(z_max, str):
                z_max = float(z_max.replace(',', '.'))
                
            # Kontroly platnosti zóny
            if np.isnan(z_min) or np.isnan(z_max):
                logger.warning(f"Ignoruji zónu s NaN hodnotami: {(z_min, z_max)}")
                continue
            if z_min < 0 or z_max < 0:
                logger.warning(f"Ignoruji zónu se zápornými hodnotami: {(z_min, z_max)}")
                continue
            if z_min > z_max:
                logger.warning(f"Ignoruji zónu s min > max: {(z_min, z_max)}")
                continue
            
            # Pro různé kryptoměny budou různé cenové rozsahy, proto
            # odstraníme specifickou kontrolu pro BTC a pouze zajistíme, aby byl rozsah rozumný
            if z_max > z_min * 10:
                logger.warning(f"Ignoruji zónu s příliš velkým rozsahem: {(z_min, z_max)}")
                continue
                
            valid_zones.append((z_min, z_max))
        except (ValueError, TypeError) as e:
            logger.warning(f"Chyba při zpracování zóny {(z_min, z_max)}: {str(e)}")
            continue

    # Omezíme na maximálně 2 zóny
    if len(valid_zones) > 2:
        logger.info(f"Omezuji počet resistenčních zón z {len(valid_zones)} na 2 pro lepší přehlednost")
        valid_zones = valid_zones[:2]

    if not valid_zones:
        logger.warning("Po ověření nezůstaly žádné platné resistenční zóny")
        return False

    logger.info(f"Vykreslování {len(valid_zones)} resistenčních zón")
    zone_added = False

    # Získání limitů x-osy
    xlim = ax.get_xlim()
    xrange = xlim[1] - xlim[0]

    # Explicitně definované červené barvy - všechny v červeném odstínu
    resistance_colors = ['#FF0000', '#FF3333']

    # Získání limitů y-osy pro kontrolu viditelnosti
    ylim = ax.get_ylim()
    y_min, y_max = ylim

    # Seřazení zón vzestupně podle ceny
    sorted_zones = sorted(valid_zones, key=lambda x: x[0])

    for i, (r_min, r_max) in enumerate(sorted_zones):
        # Kontrola, zda je zóna v rozsahu y-osy
        if r_max < y_min or r_min > y_max:
            logger.warning(f"Resistenční zóna {(r_min, r_max)} je mimo viditelný rozsah ({y_min}, {y_max})")
            # Pokud je to první zóna, rozšíříme osu y
            if i == 0:
                logger.info(f"Rozšiřuji y-osu pro resistenční zónu: {(r_min, r_max)}")
                new_y_min = min(y_min, r_min * 0.95)  # Přidáme 5% prostoru pod zónou
                new_y_max = max(y_max, r_max * 1.05)  # Přidáme 5% prostoru nad zónou
                ax.set_ylim(new_y_min, new_y_max)
            else:
                continue

        # Použití správné barvy pro zónu
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

        # Přidání popisku s kompletními informacemi o zóně
        mid_point = (r_min + r_max) / 2

        # Zaokrouhlení hodnot na celá čísla nebo na 1 desetinné místo pro menší hodnoty
        if r_min >= 100:
            r_min_formatted = int(round(r_min))
            r_max_formatted = int(round(r_max))
        else:
            r_min_formatted = round(r_min, 1)
            r_max_formatted = round(r_max, 1)

        # Vytvoření popisku s kompletními informacemi o zóně - jednodušší označení
        label_text = f"R{i+1}: {r_min_formatted}-{r_max_formatted}"

        # Přidání popisku v pravé části grafu (daleko od legendy)
        ax.text(
            xlim[0] + xrange * 0.85,  # 85% od levého okraje (blízko pravého okraje)
            mid_point,
            label_text,
            color='white',
            fontweight='bold',
            fontsize=9,
            bbox=dict(
                facecolor=color,
                alpha=0.7,
                boxstyle='round,pad=0.3'
            ),
            zorder=4,
            horizontalalignment='right'  # Zarovnání doprava
        )

        zone_added = True
        logger.info(f"Přidána resistenční zóna {i+1}: {r_min}-{r_max}")

    return zone_added
