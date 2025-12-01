# -*- coding: utf-8 -*-
"""
Created on Thu Nov 13 16:17:01 2025

@author: nilsw
"""

import pandas as pd
import numpy as np


def lees_excel_data(file_path: str, sport: str):
    """
    Leest alle benodigde data uit de drie CPET-sheets en geeft gestructureerde variabelen terug.
    Dit is een directe bundeling van ALLE variabelen die in het CPET_Analyse scripts worden gebruikt.
    """

    # ===============================
    # 1) Sheets inlezen
    # ===============================
    df_1 = pd.read_excel(file_path, header=None)     # hoofdsheet
    df_2 = pd.read_excel(file_path, sheet_name="Resultaten")
    df_3 = pd.read_excel(file_path, sheet_name="Steady State")

    # ===============================
    # 2) Algemene info (persoon)
    # ===============================
    voornaam   = df_1.iloc[2, 1]
    achternaam = df_1.iloc[1,1]
    geslacht   = df_1.iloc[3, 1]
    leeftijd   = round(df_1.iloc[4, 1], 1)
    geboortedatum = df_1.iloc[7,1]
    lengte     = df_1.iloc[5, 1]
    gewicht    = df_1.iloc[6, 1]
    testDatum  = df_1.iloc[0, 4]

    # ===============================
    # 3) Tijden (VT1, VT2, Max)
    # ===============================
    tijd_vt1 = df_2.iloc[4, 5].strftime("%M:%S")
    tijd_vt2 = df_2.iloc[4, 6].strftime("%M:%S")
    tijd_max = df_2.iloc[4, 7].strftime("%M:%S")

    # ===============================
    # 4) Hartslagwaarden
    # ===============================
    if sport == "hardlopen":
        hrrust  = df_2.iloc[22, 3]
        hrwarm  = df_2.iloc[22, 4]
        hrvt1   = df_2.iloc[22, 5]
        hrvt2   = df_2.iloc[22, 6]
        hrmax   = df_2.iloc[22, 7]
        hrr     = hrmax - hrrust

        snelheid_vt1 = df_2.iloc[5, 5]
        snelheid_vt2 = df_2.iloc[5, 6]
        snelheid_max = df_2.iloc[5, 7]

        tempo_vt1 = df_2.iloc[6, 5].strftime("%M:%S")
        tempo_vt2 = df_2.iloc[6, 6].strftime("%M:%S")
        tempo_max = df_2.iloc[6, 7].strftime("%M:%S")

    else:
        hrrust  = df_2.iloc[20, 3]
        hrwarm  = df_2.iloc[20, 4]
        hrvt1   = df_2.iloc[20, 5]
        hrvt2   = df_2.iloc[20, 6]
        hrmax   = df_2.iloc[20, 7]
        hrr     = hrmax - hrrust

        powervt1 = df_2.iloc[6, 5]
        powervt2 = df_2.iloc[6, 6]
        powermax = df_2.iloc[6, 7]

    # ===============================
    # 5) Kolommen uit df_1 (VO2-curve)
    # ===============================
    column_time        = df_1.iloc[2:, 9].astype(str).str.strip()
    column_ventilation = df_1.iloc[2:,12].astype(float)
    column_heartrate   = df_1.iloc[2:,23].astype(float)
    column_vo2         = df_1.iloc[2:,14].astype(float)
    column_power       = df_1.iloc[2:,35].astype(float)   # snelheid/vermogen

    df_1_clean = df_1.copy()
    df_1_clean["Time"] = column_time
    df_1_clean["VE"]   = column_ventilation
    df_1_clean["HR"]   = column_heartrate
    df_1_clean["VO2"]  = column_vo2
    df_1_clean["Power"] = column_power

    # ===============================
    # 6) Steady-state intervallen
    # ===============================
    start_times = df_3.iloc[1, 2:].astype(str).str.strip()
    end_times   = df_3.iloc[2, 2:].astype(str).str.strip()

    mean_VE  = []
    mean_VO2 = []

    for start, end in zip(start_times, end_times):
        mask = (df_1_clean["Time"] >= start) & (df_1_clean["Time"] <= end)
        subset = df_1_clean.loc[mask]

        mean_VE.append(subset["VE"].mean())
        mean_VO2.append(subset["VO2"].mean())

    # ===============================
    # 7) Lactaatcurve (rij 8–10)
    # ===============================
    row_8  = df_3.iloc[8,  2:].astype(float)   # HR per stap
    row_9  = df_3.iloc[9,  2:].astype(float)   # lactaat
    row_10 = df_3.iloc[10, 2:].astype(float)   # snelheid/vermogen
    row_5  = df_3.iloc[4,  2:].astype(float)   # VO2 per stap

    # ===============================
    # 8) Lactaat-sprong vinden
    # ===============================
    diff_lact = row_9.diff()

    if (diff_lact >= 0.4).any():
        first_label = diff_lact[diff_lact >= 0.4].index[0]
        pos = diff_lact.index.get_loc(first_label)
        idx_sprong = pos - 1
        lact_1st   = row_9.iloc[idx_sprong]
        power_1st  = row_10.iloc[idx_sprong]
    else:
        lact_1st = None
        power_1st = None

    # ===============================
    # Return alles geordend
    # ===============================
    return {
        "df_1": df_1_clean,
        "df_2": df_2,
        "df_3": df_3,

        "persoon": {
            "voornaam": voornaam,
            "achternaam": achternaam,
            "geslacht": geslacht,
            "leeftijd": leeftijd,
            "lengte": lengte,
            "gewicht": gewicht,
            "testDatum": testDatum,
            "geboortedatum": geboortedatum
        },

        "tijden": {
            "VT1": tijd_vt1,
            "VT2": tijd_vt2,
            "MAX": tijd_max
        },

        "kolommen": {
            "time": column_time,
            "VE": column_ventilation,
            "HR": column_heartrate,
            "VO2": column_vo2,
            "Power": column_power,
        },

        "steady_state": {
            "start_times": start_times,
            "end_times": end_times,
            "mean_VE": mean_VE,
            "mean_VO2": mean_VO2,
        },

        "curve_data": {
            "HR_steps": row_8,
            "Lactate_steps": row_9,
            "Power_steps": row_10,
            "VO2_steps": row_5,
        },

        "lactaat_sprong": {
            "lactaat": lact_1st,
            "power": power_1st,
        },

        "sport": sport,
    }