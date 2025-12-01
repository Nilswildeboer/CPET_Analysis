# -*- coding: utf-8 -*-
"""
Trainingszones – functionele versie voor CPET_Analyse

Deze module is een directe vertaling van het originele
'Trainingszones_bepaling.py' script naar een functie:

    bepaal_trainingszones(data, lactaat)

Belangrijk:
- Zelfde berekeningen en OPMAAK van de figuren als het origineel
- Geen Tkinter, geen Excel-inlezen meer
- Data komt uit `data` (output van jouw Excel-leesfunctie)
- PNG's worden opgeslagen in de map 'Plots' binnen base_dir:

    <base_dir>/Plots/high_definition_plot.png
    <base_dir>/Plots/high_definition_table.png
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
from scipy.interpolate import interp1d, PchipInterpolator
from matplotlib.transforms import Bbox


def bepaal_trainingszones(data, lactaat=True):
    """
    Bepaal LT1/LT2, zones en genereer de twee PNG's
    met exact dezelfde opmaak als het originele script.

    Parameters
    ----------
    data : dict
        Structure uit jouw CPET_Analyse (zie screenshot):
            - df_1 : DataFrame (hoofdsheet)
            - df_3 : DataFrame ('Steady State')
            - sport : "Wielrennen" of "Hardlopen"
            - base_dir : (optioneel) projectmap; anders huidige werkmap
    lactaat : bool
        Alleen voor compatibiliteit met jouw bestaande call-signature.
        Wordt verder niet gebruikt (originele script gebruikt het ook niet).

    Returns
    -------
    dict :
        {
            "LT1_power": ...,
            "LT1_lactaat": ...,
            "LT2_power": ...,
            "LT2_lactaat": ...,
            "HR_LT1": ...,
            "HR_LT2": ...,
            "plot_path":  <abs pad naar Plots/high_definition_plot.png>,
            "table_path": <abs pad naar Plots/high_definition_table.png>,
        }
    """

    # ======================================================================
    # 0. Data uit CPET_Analyse
    # ======================================================================
    df_1 = data["df_1"].copy()
    df_3 = data["df_3"].copy()
    sport = data["sport"]
    base_dir = data.get("base_dir", os.getcwd())

    # Zorg dat de plots-mappen bestaat
    plots_dir = os.path.join(base_dir, "Plots")
    os.makedirs(plots_dir, exist_ok=True)

    # ======================================================================
    # 4) Basisvariabelen uit Excel halen (identiek aan origineel)
    # ======================================================================
    weight = float(data["persoon"]["gewicht"])

    column_time        = df_1.iloc[2:, 9].astype(str).str.strip()
    column_ventilation = df_1.iloc[2:,12].astype(float)
    column_heartrate   = df_1.iloc[2:,23].astype(float)
    column_vo2         = df_1.iloc[2:,14].astype(float)
    column_vco2        = df_1.iloc[2:,15].astype(float)   # niet verder gebruikt
    column_prestation  = df_1.iloc[2:,36].astype(float)   # niet verder gebruikt
    column_power       = df_1.iloc[2:,35].astype(float)

    df_1["Time"] = column_time
    df_1["VE"]   = column_ventilation
    df_1["VO2"]  = column_vo2

    # ======================================================================
    # 5) Rijen uit 'Steady State' pakken
    # ======================================================================
    row_8  = df_3.iloc[8]
    row_9  = df_3.iloc[9]
    row_10 = df_3.iloc[10]
    row_5  = df_3.iloc[4]

    row_8_numeric  = row_8[2:].astype(float)
    row_9_numeric  = row_9[2:].astype(float)
    row_10_numeric = row_10[2:].astype(float)
    row_5_numeric  = row_5[2:].astype(float)

    # ======================================================================
    # 6) Intervalbepaling voor gemiddelde VE/VO2
    # ======================================================================
    start_times = df_3.iloc[1, 2:].astype(str).str.strip()
    end_times   = df_3.iloc[2, 2:].astype(str).str.strip()

    mean_values_VE  = []
    mean_values_VO2 = []

    for start, end in zip(start_times, end_times):
        mask = (df_1["Time"] >= start) & (df_1["Time"] <= end)
        filtered = df_1.loc[mask, ["VE", "VO2"]]
        mean_values_VE.append(filtered["VE"].mean())
        mean_values_VO2.append(filtered["VO2"].mean())

    mean_values_VE  = np.array(mean_values_VE)
    mean_values_VO2 = np.array(mean_values_VO2)

    # ======================================================================
    # 7) Eerste duidelijke lactaatstijging (>= 0.4 mmol/L)
    # ======================================================================
    differences_lactate = row_9_numeric.diff()

    if (differences_lactate >= 0.4).any():
        first_increase_label = differences_lactate[differences_lactate >= 0.4].index[0]
        position = differences_lactate.index.get_loc(first_increase_label)
        index_increase = position - 1
        first_la_datapoint = row_9_numeric.iloc[index_increase]
        power_first_La_increase = row_10_numeric.iloc[index_increase]
    else:
        # fallback: als er geen sprong is, pak eerste punt
        first_la_datapoint = row_9_numeric.iloc[0]
        power_first_La_increase = row_10_numeric.iloc[0]

    # ======================================================================
    # 8) Voorbereiding voor curve-fit en DMax-Modified
    # ======================================================================
    if sport in ("Wielrennen", "Hardlopen"):
        x_power   = row_10_numeric
        y_lactate = row_9_numeric
        y_hr      = row_8_numeric
    else:
        # fallback – zou eigenlijk nooit moeten voorkomen
        x_power   = row_10_numeric
        y_lactate = row_9_numeric
        y_hr      = row_8_numeric

    x_power_excluded = x_power[1:]
    y_lactate_excl   = y_lactate[1:]

    x_line = np.array([power_first_La_increase, x_power[-1]])
    y_line = np.array([first_la_datapoint,      y_lactate[-1]])

    coefficients = np.polyfit(x_power_excluded, y_lactate_excl, 3)
    polynomial   = np.poly1d(coefficients)

    x_fit = np.linspace(float(x_power_excluded.min()),
                        float(x_power_excluded.max()), 100)
    y_fit = polynomial(x_fit)

    slope_line = (y_line[1] - y_line[0]) / (x_line[1] - x_line[0])
    poly_deriv = np.polyder(polynomial)

    def find_intersection(x_value):
        return poly_deriv(x_value) - slope_line

    initial_guess = power_first_La_increase
    x_intersection = fsolve(find_intersection, initial_guess)[0]
    y_intersection = polynomial(x_intersection)

    # === HANDMATIGE LT2 override: y_intersection = 4.0 mmol/L (zoals origineel) ===
    y_intersection = 4.0

    def find_x_intersection(x_value):
        return polynomial(x_value) - y_intersection

    x_intersection = fsolve(find_x_intersection, x_intersection)[0]

    # ======================================================================
    # 9) LT1 bepalen
    # ======================================================================
    y_LT1 = ((y_lactate.iloc[0] + y_lactate.iloc[0]) / 2) + 1.0

    def find_x_LT1(x_value):
        return polynomial(x_value) - y_LT1

    x_LT1 = fsolve(find_x_LT1, x_intersection)[0]

    lt1_power = x_LT1
    lt1       = y_LT1
    lt2_power = x_intersection
    lt2_lact  = y_intersection

    # ======================================================================
    # 10) Zone-splits
    # ======================================================================
    split_50_50_wattage = lt1_power * 0.6

    above_lt2_wattage_values = x_power[x_power >= lt2_power]
    split_75_25_wattage = above_lt2_wattage_values.quantile(0.6)

    # ======================================================================
    # 11) Interpolaties voor HR/VE/VO2 vs 'power'
    # ======================================================================
    hr_interpolation    = interp1d(x_power, y_hr,           kind="linear", fill_value="extrapolate")
    VE_interpolation    = interp1d(x_power, mean_values_VE, kind="linear", fill_value="extrapolate")
    VO2_interpolation   = interp1d(x_power, mean_values_VO2,kind="linear", fill_value="extrapolate")
    row_5_interpolation = interp1d(x_power, row_5_numeric,  kind="linear", fill_value="extrapolate")

    power_rest        = round(float(x_power.min()), 1)
    power_split_50_50 = round(float(split_50_50_wattage), 1)
    power_LT1         = round(float(lt1_power), 1)
    power_LT2         = round(float(lt2_power), 1)
    power_split_75_25 = round(float(split_75_25_wattage), 1)
    power_max         = round(float(x_power.max()), 1)

    # ======================================================================
    # 12) Helper: km/u -> tempo
    # ======================================================================
    def speed_to_pace(speed):
        if speed == 0:
            return "N/A"
        pace_min = 60.0 / float(speed)
        minutes  = int(pace_min)
        seconds  = round((pace_min - minutes) * 60)
        return f"{minutes:02}:{seconds:02}"

    # PRESTATIE / TEMPO
    if sport == "Wielrennen":
        pace_rest        = round(power_rest        / weight, 2)
        pace_split_50_50 = round(power_split_50_50 / weight, 2)
        pace_LT1         = round(power_LT1         / weight, 2)
        pace_LT2         = round(power_LT2         / weight, 2)
        pace_split_75_25 = round(power_split_75_25 / weight, 2)
        pace_max         = round(power_max         / weight, 2)
    else:  # Hardlopen
        pace_rest        = speed_to_pace(power_rest)
        pace_split_50_50 = speed_to_pace(power_split_50_50)
        pace_LT1         = speed_to_pace(power_LT1)
        pace_LT2         = speed_to_pace(power_LT2)
        pace_split_75_25 = speed_to_pace(power_split_75_25)
        pace_max         = speed_to_pace(power_max)

    # ======================================================================
    # 13) HR/VE/VO2 bij sleutelpunt-snelheden
    # ======================================================================
    hr_rest        = round(float(y_hr.min()))
    hr_split_50_50 = round(float(hr_interpolation(split_50_50_wattage)))
    hr_LT1         = round(float(hr_interpolation(lt1_power)))
    hr_LT2         = round(float(hr_interpolation(lt2_power)))
    hr_split_75_25 = round(float(hr_interpolation(split_75_25_wattage)))
    hr_max         = round(float(y_hr.max()))

    VE_rest        = round(float(np.min(mean_values_VE)), 1)
    VE_split_50_50 = round(float(VE_interpolation(split_50_50_wattage)), 1)
    VE_LT1         = round(float(VE_interpolation(lt1_power)), 1)
    VE_LT2         = round(float(VE_interpolation(lt2_power)), 1)
    VE_split_75_25 = round(float(VE_interpolation(split_75_25_wattage)), 1)
    VE_max         = round(float(np.max(mean_values_VE)), 1)

    VO2_rest        = round(float(np.min(row_5_numeric)))
    VO2_split_50_50 = round(float(row_5_interpolation(split_50_50_wattage)))
    VO2_LT1         = round(float(row_5_interpolation(lt1_power)))
    VO2_LT2         = round(float(row_5_interpolation(lt2_power)))
    VO2_split_75_25 = round(float(row_5_interpolation(split_75_25_wattage)))
    VO2_max         = round(float(np.max(row_5_numeric)))

    VO2max_rest        = round(VO2_rest        / weight, 1)
    VO2max_split_50_50 = round(VO2_split_50_50 / weight, 1)
    VO2max_LT1         = round(VO2_LT1         / weight, 1)
    VO2max_LT2         = round(VO2_LT2         / weight, 1)
    VO2max_split_75_25 = round(VO2_split_75_25 / weight, 1)
    VO2max_max         = round(VO2_max         / weight, 1)

    # ======================================================================
    # 14) Gladde HR-lijn (PCHIP)
    # ======================================================================
    pchip       = PchipInterpolator(x_power, y_hr)
    x_smooth    = np.linspace(float(x_power.min()), float(x_power.max()), 500)
    y_hr_smooth = pchip(x_smooth)

    # ======================================================================
    # 15) Plot (lactaat + hartslag + zones + annotaties)
    # ======================================================================
    color_lactate   = "#9496f7"
    color_heartrate = "#ff7d73"
    color_DMax_mod  = "#f7a35c"
    color_LT1       = "#90ed7d"

    fig, ax1 = plt.subplots(figsize=(10, 6), constrained_layout=True)
    ax2 = ax1.twinx()

    ax2.scatter(x_power, y_hr, color=color_heartrate, marker="o", s=50)
    ax2.plot(x_smooth, y_hr_smooth, color=color_heartrate, linestyle="-", linewidth=1.5)
    ax2.set_ylabel("Hartslag (bpm)", fontsize=10)
    ax2.tick_params(axis="y")

    ax1.scatter(x_power, y_lactate, color=color_lactate, s=50, zorder=2)
    ax1.plot(x_fit, y_fit, color=color_lactate, linewidth=1.5)

    ax1.plot(lt1_power, lt1,       "o", color=color_LT1,      markersize=9, zorder=3)
    ax1.plot(lt2_power, lt2_lact,  "o", color=color_DMax_mod, markersize=8)

    if sport == "Wielrennen":
        ax1.set_xlabel("Vermogen (Watt)", fontsize=10)
        ax1.set_ylabel("Lactaat (mmol/L)", fontsize=10)
    else:
        ax1.set_xlabel("Snelheid (km/u)", fontsize=10)
        ax1.set_ylabel("Lactaat (mmol/L)", fontsize=10)
    ax1.tick_params(axis="y")

    ax1.axvspan(0,                   split_50_50_wattage, facecolor="#2ab34b", alpha=0.3, label="Zone 1")
    ax1.axvspan(split_50_50_wattage, lt1_power,           facecolor="#f2cf24", alpha=0.3, label="Zone 2")
    ax1.axvspan(lt1_power,           lt2_power,           facecolor="#f36f44", alpha=0.3, label="Zone 3")
    ax1.axvspan(lt2_power,           split_75_25_wattage, facecolor="#007ac2", alpha=0.3, label="Zone 4")
    ax1.axvspan(split_75_25_wattage, x_power.max(),       facecolor="#b432b0", alpha=0.3, label="Zone 5")

    for i, (xv, yv) in enumerate(zip(x_power, y_lactate)):
        dy = -20 if i in [10] else 10
        ax1.annotate(
            f"{yv:.1f}", (xv, yv),
            textcoords="offset points", xytext=(0, dy),
            ha="center", color="white", fontsize=8,
            bbox=dict(
                facecolor=color_lactate,
                edgecolor="none",
                alpha=0.8,
                boxstyle="round,pad=0.3,rounding_size=0.2",
            ),
        )

    for i, (xv, yv) in enumerate(zip(x_power, y_hr)):
        dy = -15 if i in [40] else 10
        ax2.annotate(
            f"{yv:.0f}", (xv, yv),
            textcoords="offset points", xytext=(0, dy),
            ha="center", color="white", fontsize=8,
            bbox=dict(
                facecolor=color_heartrate,
                edgecolor="none",
                alpha=0.8,
                boxstyle="round,pad=0.3,rounding_size=0.2",
            ),
        )

    if sport == "Wielrennen":
        ax1.annotate(
            f"Lactate Threshold 1\n{round(lt1,1)} mmol/L    {round(lt1_power,1)} Watt",
            xy=(lt1_power, lt1), xytext=(0, 50), textcoords="offset points",
            ha="center", va="bottom", fontsize=9, color="white", fontfamily="Arial",
            bbox=dict(facecolor=color_LT1, edgecolor="none", boxstyle="round,pad=0.8"),
            arrowprops=dict(arrowstyle="-", color=color_LT1, linewidth=3),
        )
        ax1.annotate(
            f"Lactate Threshold 2\n{round(lt2_lact,1)} mmol/L    {round(lt2_power,1)} Watt",
            xy=(lt2_power, lt2_lact), xytext=(0, 55), textcoords="offset points",
            ha="center", va="bottom", fontsize=9, color="white", fontfamily="Arial",
            bbox=dict(facecolor=color_DMax_mod, edgecolor="none", boxstyle="round,pad=0.8"),
            arrowprops=dict(arrowstyle="-", color=color_DMax_mod, linewidth=3),
        )
    else:  # Hardlopen
        ax1.annotate(
            f"Lactate Threshold 1\n{round(lt1,1)} mmol/L    {round(lt1_power,1)} km/u",
            xy=(lt1_power, lt1), xytext=(0, 50), textcoords="offset points",
            ha="center", va="bottom", fontsize=9, color="white", fontfamily="Arial",
            bbox=dict(facecolor=color_LT1, edgecolor="none", boxstyle="round,pad=0.8"),
            arrowprops=dict(arrowstyle="-", color=color_LT1, linewidth=3),
        )
        ax1.annotate(
            f"Lactate Threshold 2\n{round(lt2_lact,1)} mmol/L    {round(lt2_power,1)} km/u",
            xy=(lt2_power, lt2_lact), xytext=(0, 55), textcoords="offset points",
            ha="center", va="bottom", fontsize=9, color="white", fontfamily="Arial",
            bbox=dict(facecolor=color_DMax_mod, edgecolor="none", boxstyle="round,pad=0.8"),
            arrowprops=dict(arrowstyle="-", color=color_DMax_mod, linewidth=3),
        )

    ax1.yaxis.grid(True, linestyle="-", alpha=0.7, color="white")
    ax1.spines["top"].set_visible(False)
    ax2.spines["top"].set_visible(False)
    ax1.set_ylim(0, float(y_lactate.max()) + 1)

    plot_path = os.path.join(plots_dir, "high_definition_plot.png")
    fig.savefig(plot_path, dpi=300, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    
    # ✅ HARD CHECK
    if not os.path.exists(plot_path):
        raise RuntimeError(
            f"Plot PNG is niet opgeslagen. Verwacht op: {plot_path}\n"
            f"plots_dir={plots_dir} bestaat={os.path.exists(plots_dir)}"
        )

    # ======================================================================
    # 16) Tabel (exacte opmaak) → high_definition_table.png
    # ======================================================================
    data_table = {
        "Rest"  : [hr_rest, VO2_rest, VO2max_rest, power_rest,        pace_rest,        VE_rest],
        "Zone 2": [hr_split_50_50, VO2_split_50_50, VO2max_split_50_50, power_split_50_50, pace_split_50_50, VE_split_50_50],
        "Zone 3": [hr_LT1, VO2_LT1, VO2max_LT1, power_LT1,            pace_LT1,         VE_LT1],
        "Zone 4": [hr_LT2, VO2_LT2, VO2max_LT2, power_LT2,            pace_LT2,         VE_LT2],
        "Zone 5": [hr_split_75_25, VO2_split_75_25, VO2max_split_75_25, power_split_75_25, pace_split_75_25, VE_split_75_25],
        "Max"   : [hr_max, VO2_max, VO2max_max, power_max,            pace_max,         VE_max],
    }

    if sport == "Wielrennen":
        row_labels = [
            "Hartslag (bpm)",
            "VO2 (mL/min)",
            "VO2/kg (mL/kg/min)",
            "Geschat Vermogen (Watt)",
            "Prestatie (Watt/kg)",
            "Ventilatie (L/min)",
        ]
    else:
        row_labels = [
            "Hartslag (bpm)",
            "VO2 (mL/min)",
            "VO2/kg (mL/kg/min)",
            "Geschatte snelheid (km/u)",
            "Tempo (mm:ss/km)",
            "Ventilatie (L/min)",
        ]

    formatted_data = {
        "ERG LICHT": [f"{data_table['Rest'][i]}   -   {data_table['Zone 2'][i]}"  for i in range(len(row_labels))],
        "LICHT"    : [f"{data_table['Zone 2'][i]} -   {data_table['Zone 3'][i]}" for i in range(len(row_labels))],
        "MATIG"    : [f"{data_table['Zone 3'][i]} -   {data_table['Zone 4'][i]}" for i in range(len(row_labels))],
        "ZWAAR"    : [f"{data_table['Zone 4'][i]} -   {data_table['Zone 5'][i]}" for i in range(len(row_labels))],
        "MAXIMAAL" : [f"{data_table['Zone 5'][i]} -   {data_table['Max'][i]}"    for i in range(len(row_labels))],
    }

    df_table = pd.DataFrame(formatted_data, index=row_labels)

    colors = ["#2ab34b", "#f2cf24", "#f36f44", "#007ac2", "#b432b0"]

    fig2, ax = plt.subplots(figsize=(28, 5))
    ax.axis("off")
    ax.set_position([0, 0, 1, 1])

    table = ax.table(
        cellText=df_table.values,
        colLabels=df_table.columns,
        rowLabels=df_table.index,
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(20)

    for (row, col), cell in table._cells.items():
        cell.set_edgecolor("white")
        cell.set_text_props(fontsize=24, fontfamily="Arial")
        cell.set_width(0.16)
        if row == 0:
            cell.set_text_props(weight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#dfe0e1")
        else:
            cell.set_facecolor("white")
        cell.set_height(0.1)

    fig2.canvas.draw()
    renderer = fig2.canvas.get_renderer()

    bars = []
    bar_height = 0.02
    for col_idx, color in enumerate(colors):
        key = (0, col_idx)
        if key in table._cells:
            cell = table._cells[key]
            bbox = cell.get_window_extent(renderer)
            x0_fig, y0_fig = fig2.transFigure.inverted().transform((bbox.x0, bbox.y0))
            x1_fig, _      = fig2.transFigure.inverted().transform((bbox.x1, bbox.y1))
            width_fig = x1_fig - x0_fig

            bar = plt.Rectangle(
                (x0_fig, y0_fig + 0.09),
                width_fig,
                bar_height,
                transform=fig2.transFigure,
                color=color,
                clip_on=False,
            )
            fig2.patches.append(bar)
            bars.append(bar)

    bboxes_px = [table.get_window_extent(renderer)] + [b.get_window_extent(renderer) for b in bars]
    full_bbox_px = Bbox.union(bboxes_px).expanded(1.01, 1.04)
    full_bbox_in = full_bbox_px.transformed(fig2.dpi_scale_trans.inverted())

    table_path = os.path.join(plots_dir, "high_definition_table.png")
    fig2.savefig(table_path, dpi=300, bbox_inches=full_bbox_in, pad_inches=0.02)
    plt.close(fig2)
    
    # ✅ HARD CHECK
    if not os.path.exists(table_path):
        raise RuntimeError(
            f"Tabel PNG is niet opgeslagen. Verwacht op: {table_path}\n"
            f"plots_dir={plots_dir} bestaat={os.path.exists(plots_dir)}"
        )

    # ======================================================================
    # 17) Resultaat teruggeven
    # ======================================================================
    return {
        "LT1_power": float(lt1_power),
        "LT1_lactaat": float(lt1),
        "LT2_power": float(lt2_power),
        "LT2_lactaat": float(lt2_lact),
        "HR_LT1": float(hr_LT1),
        "HR_LT2": float(hr_LT2),
        "plot_path": plot_path,
        "table_path": table_path,
    }
