# -*- coding: utf-8 -*-
"""
Created on Thu Nov 13 18:29:09 2025

@author: nilsw
"""

# Functies/pagina2.py
# Pagina 2: Evaluatie (VT1/LT1, VT2/LT2, Max, Let op!)
# Gebaseerd op Pagina_Twee_uitwerking.py, maar zónder tkinter / Excel inlezen.
# Aangeroepen vanuit CPET_Analyse met data uit data_uitlezen.py

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from xml.sax.saxutils import escape

import pandas as pd
import numpy as np
from datetime import time, timedelta, date

from scipy.interpolate import interp1d
from scipy.optimize import fsolve


# ---- Layout-constanten ----
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 20

BLOCK_INSET = 40   # binnenmarge links/rechts -> maakt de blokken smaller
BLOCK_GAP   = 18   # verticale ruimte tussen de grijze blokken

# Globals die we in de helpers vullen in build_pagina2()
LOGO_PATH = "Mens_en_Techniek_Logo.png"
testDatum = None
vandaag = None
fields_eval = None
values_eval = None
sport = None


# ---------------- Header ----------------
def draw_header(c):
    """Header met logo, adres en datum-kader (zelfde stijl als Pagina_Twee_uitwerking)."""
    try:
        logo = ImageReader(LOGO_PATH)
        c.drawImage(logo, MARGIN, PAGE_HEIGHT - MARGIN - 50,
                    width=80, height=50, preserveAspectRatio=True)
    except Exception:
        pass  # als logo ontbreekt, gewoon overslaan

    x, y = MARGIN + 90, PAGE_HEIGHT - MARGIN - 5
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "Zuyd Hogeschool, Locatie HPC")
    c.setFont("Helvetica", 10)
    c.drawString(x, y - 16, "Eggerweg 4, 6135 LG Sittard")
    c.drawString(x, y - 30, "www.zuyd.nl/opleidingen/mens-en-techniek-biometrie")

    # zwarte datum-box rechts
    bw, bh = 120, 60
    bx = PAGE_WIDTH - MARGIN - bw
    by = PAGE_HEIGHT - MARGIN - bh
    c.setFillColor(colors.black)
    c.rect(bx, by, bw, bh, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(bx + 5, by + bh - 12, "Bezoekdatum")
    c.setFont("Helvetica", 9)
    c.drawString(bx + 5, by + bh - 26, str(testDatum))
    c.line(bx + 3, by + bh - 30, bx + bw - 3, by + bh - 30)
    c.drawString(bx + 5, by + bh - 44, "Geprint op")
    c.drawString(bx + 65, by + bh - 44, str(vandaag))
    c.setFillColor(colors.black)
    c.line(MARGIN, by, PAGE_WIDTH - MARGIN, by)
    return by  # onderrand van header


# ---------------- Korte gegevensrij ----------------

def _eval_col_widths(total_w):
    ratios = [1.5, 1, 1, 1.2, 1.2]
    s = float(sum(ratios))
    return [r / s * total_w for r in ratios]


def draw_kv_table_short(c, x, y, total_w):
    """Korte rij met Voornaam, Geslacht, Leeftijd, Gewicht, Lengte (zoals in originele script)."""
    col_w = _eval_col_widths(total_w)
    row_h = 28
    tw = sum(col_w)
    th = row_h

    c.setLineWidth(0.5)
    c.setStrokeColor(colors.lightgrey)
    c.rect(x, y - th, tw, th, stroke=1, fill=0)

    # verticale lijnen
    ax = x
    for w in col_w:
        c.line(ax, y, ax, y - th)
        ax += w
    c.line(x + tw, y, x + tw, y - th)

    # horizontale lijnen
    c.line(x, y, x + tw, y)
    c.line(x, y - th, x + tw, y - th)

    # onderlijntje in elke cel
    bot = y - th
    pad = 5
    ax = x
    for w in col_w:
        c.line(ax + pad, bot, ax + w - pad, bot)
        ax += w

    # inhoud
    cy = y
    ax = x
    for lab, val, w in zip(fields_eval, values_eval, col_w):
        c.setFont("Helvetica", 7)
        c.drawString(ax + 4, cy - 6, str(lab))
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(ax + w - 4, cy - th + 6, str(val))
        ax += w

    return th  # gebruikte hoogte


# ---------------- EVALUATIE-balk ----------------

def draw_eval_bar(c, x, y, width, height=18):
    c.setFillColor(colors.lightgrey)
    c.rect(x, y - height, width, height, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x + width / 2, y - height + (height - 11) / 2 + 1, "EVALUATIE")
    return y - height - 10


# ---------------- Evaluatie-sectie ----------------

def draw_eval_section(c, title, note_lines, table_pairs,
                      x, y_top, width, gap=14):
    """
    Tekent één evaluatie-grijs blok.
    - note_lines: lijst met tekstregels
    - table_pairs: lijst met (label, waarde) of None
    """
    corner = 6
    pad_x = 10
    pad_top = 6
    pad_bottom = 10
    title_font = "Helvetica-Bold"
    title_size = 11
    body_font = "Helvetica"
    body_size = 9
    body_leading = 11

    has_table = bool(table_pairs)
    table_col_w = [95, 85] if has_table else []
    table_w = sum(table_col_w) if has_table else 0
    gap_text_tbl = 12 if has_table else 0

    text_w = width - 2 * pad_x - table_w - gap_text_tbl

    safe_lines = [(l or "").replace("CO₂", "CO2") for l in note_lines]
    html = "<br/>".join(escape(line) if line.strip() != "" else "&nbsp;"
                        for line in safe_lines)
    p_style = ParagraphStyle(
        "eval_body",
        fontName=body_font,
        fontSize=body_size,
        leading=body_leading,
    )
    para = Paragraph(html, p_style)
    _, para_h = para.wrap(text_w, 10000)

    table_h = 0
    if has_table:
        data = [[k, v] for k, v in table_pairs]
        tbl = Table(data, colWidths=table_col_w)
        tbl.setStyle(
            TableStyle(
                [
                    ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("FONT", (1, 0), (1, -1), "Helvetica", 9),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]
            )
        )
        _, table_h = tbl.wrap(0, 0)
    else:
        tbl = None

    title_h = title_size + 3
    content_h = max(para_h, table_h)
    box_h = title_h + pad_top + content_h + pad_bottom

    y0 = y_top - box_h
    c.setFillColor(colors.lightgrey)
    c.roundRect(x, y0, width, box_h, corner, fill=1, stroke=0)

    c.setFillColor(colors.black)
    c.setFont(title_font, title_size)
    c.drawString(x + pad_x, y0 + box_h - title_h, title)

    text_top_y = y0 + box_h - title_h - pad_top
    para.drawOn(c, x + pad_x, text_top_y - para_h)

    if has_table:
        tx = x + width - pad_x - table_w
        ty = y0 + (box_h - table_h) / 2.0
        tbl.drawOn(c, tx, ty)

    return y0 - gap


# ---------------- Footer-sectie ----------------

def draw_footer(c, left_text="Geprint door Zuyd",
                page=None, total=None, right_text="omnia 2.3"):
    y_line = 28
    x_left = MARGIN
    x_right = PAGE_WIDTH - MARGIN

    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.line(x_left, y_line, x_right, y_line)

    text_y = y_line - 12
    c.setFont("Helvetica", 8)
    c.drawString(x_left, text_y, left_text)

    current = page if page is not None else c.getPageNumber()
    mid = f"{current} / {total}" if total is not None else f"{current}"
    c.drawCentredString(PAGE_WIDTH / 2.0, text_y, mid)

    c.drawRightString(x_right, text_y, right_text)


# ---------------- Hulpfunctie: tijd converteren ----------------

def to_td(x):
    """Accepteert 'MM:SS', 'HH:MM:SS', datetime.time, Timedelta, ook met spaties/komma."""
    if isinstance(x, pd.Timedelta):
        return x
    if isinstance(x, time):
        return timedelta(hours=x.hour, minutes=x.minute, seconds=x.second)
    s = str(x).strip()
    if not s:
        return pd.NaT
    s = s.replace(",", ".")
    parts = s.split(":")
    try:
        if len(parts) == 2:  # MM:SS(.fff)
            m, sec = parts
            return timedelta(minutes=int(m), seconds=float(sec))
        elif len(parts) == 3:  # HH:MM:SS(.fff)
            h, m, sec = parts
            return timedelta(hours=int(h), minutes=int(m), seconds=float(sec))
        else:
            return pd.to_timedelta(s)
    except Exception:
        return pd.NaT


# ---------------- Hoofdfunctie: Pagina 2 bouwen ----------------

def build_pagina2(data, zones, output_path,
                  logo_path="Mens_en_Techniek_Logo.png"):
    """
    Bouwt pagina 2 van het rapport (evaluatiepagina).

    Parameters
    ----------
    data : dict
        Output van lees_excel_data(file_path, sport)
    zones : dict
        Output van bepaal_trainingszones(data, lactaat)
        (nu nog niet intensief gebruikt, maar kan later handig zijn)
    output_path : str
        Pad naar het PDF-bestand voor pagina 2
    logo_path : str
        Pad naar het logo (PNG)
    """

    global LOGO_PATH, testDatum, vandaag, fields_eval, values_eval, sport

    LOGO_PATH = logo_path

    # ---- Data uit structuren halen ----
    df_1 = data["df_1"]
    df_2 = data["df_2"]
    df_3 = data["df_3"]
    sport = data["sport"]  # 'wielrennen' of 'hardlopen'

    # Persoonsinfo (zoals in het origineel)
    voornaam = df_1.iloc[2, 1]
    geslacht = df_1.iloc[3, 1]
    leeftijd = round(df_1.iloc[4, 1], 1)
    lengte = df_1.iloc[5, 1]
    gewicht = df_1.iloc[6, 1]
    testDatum = df_1.iloc[0, 4]
    vandaag = date.today().strftime("%d-%m-%Y")

    # Resultaten
    tijdvt1 = df_2.iloc[4, 5].strftime("%M:%S")
    tijdvt2 = df_2.iloc[4, 6].strftime("%M:%S")
    tijdmax = df_2.iloc[4, 7].strftime("%M:%S")

    # Hartslag (zie script)
    hrrust = df_2.iloc[20, 3]
    hrwarmup = df_2.iloc[20, 4]
    hrvt1 = df_2.iloc[20, 5]
    hrvt2 = df_2.iloc[20, 6]
    hrmax = df_2.iloc[20, 7]
    hrr = hrmax - hrrust

    if sport == "Hardlopen":
        snelheidvt1 = df_2.iloc[5, 5]
        snelheidvt2 = df_2.iloc[5, 6]
        snelheidmax = df_2.iloc[5, 7]

        tempovt1 = df_2.iloc[6, 5].strftime("%M:%S")
        tempovt2 = df_2.iloc[6, 6].strftime("%M:%S")
        tempomax = df_2.iloc[6, 7].strftime("%M:%S")

        percvt1max = round((snelheidvt1 / snelheidmax * 100), 1)
        percvt2max = round((snelheidvt2 / snelheidmax * 100), 1)

        # bij lopen: hartslag-drempels op rij 22
        hrrust = df_2.iloc[22, 3]
        hrwarmup = df_2.iloc[22, 4]
        hrvt1 = df_2.iloc[22, 5]
        hrvt2 = df_2.iloc[22, 6]
        hrmax = df_2.iloc[22, 7]
        hrr = hrmax - hrrust
    else:
        powervt1 = df_2.iloc[6, 5]
        powervt2 = df_2.iloc[6, 5]

    # Steady State sheet
    # (wordt gebruikt voor lactaat-waarden etc.)
    # df_3 = data["df_3"] is al boven gedefinieerd

    # --------- Trainingszone snippet (zoals origineel) ---------

    column_time = df_1.iloc[2:, 9].astype(str).str.strip()
    column_ventilation = df_1.iloc[2:, 12].astype(float)
    column_heartrate = df_1.iloc[2:, 23].astype(float)
    column_vo2 = df_1.iloc[2:, 14].astype(float)
    column_vco2 = df_1.iloc[2:, 15].astype(float)    # niet gebruikt verder
    column_prestation = df_1.iloc[2:, 36].astype(float)
    column_power = df_1.iloc[2:, 35].astype(float)

    df_1["Time"] = column_time
    df_1["VE"] = column_ventilation
    df_1["VO2"] = column_vo2

    start_times = df_3.iloc[1, 2:].astype(str).str.strip()
    end_times = df_3.iloc[2, 2:].astype(str).str.strip()

    mean_values_VE = []
    mean_values_VO2 = []

    for start, end in zip(start_times, end_times):
        mask = (df_1["Time"] >= start) & (df_1["Time"] <= end)
        filtered = df_1.loc[mask, ["VE", "VO2"]]
        mean_values_VE.append(filtered["VE"].mean())
        mean_values_VO2.append(filtered["VO2"].mean())

    row_8 = df_3.iloc[8]
    row_9 = df_3.iloc[9]
    row_10 = df_3.iloc[10]
    row_5 = df_3.iloc[4]

    row_8_numeric = row_8[2:].astype(float)
    row_9_numeric = row_9[2:].astype(float)
    row_10_numeric = row_10[2:].astype(float)
    row_5_numeric = row_5[2:].astype(float)

    differences_lactate = row_9_numeric.diff()

    if (differences_lactate >= 0.4).any():
        first_increase_label = differences_lactate[differences_lactate >= 0.4].index[0]
        position = differences_lactate.index.get_loc(first_increase_label)
        index_increase = position - 1
        first_la_datapoint = row_9_numeric.iloc[index_increase]
        power_first_La_increase = row_10_numeric.iloc[index_increase]
    else:
        first_la_datapoint = row_9_numeric.iloc[0]
        power_first_La_increase = row_10_numeric.iloc[0]

    if sport in ["wielrennen", "Hardlopen"]:
        x_power = row_10_numeric
        y_lactate = row_9_numeric
        y_hr = row_8_numeric

    x_power_excluded = x_power[1:]
    y_lactate_excl = y_lactate[1:]

    x_line = np.array([power_first_La_increase, x_power.iloc[-1]])
    y_line = np.array([first_la_datapoint, y_lactate.iloc[-1]])

    coefficients = np.polyfit(x_power_excluded, y_lactate_excl, 3)
    polynomial = np.poly1d(coefficients)

    x_fit = np.linspace(float(x_power_excluded.min()),
                        float(x_power_excluded.max()), 100)
    y_fit = polynomial(x_fit)

    slope_line = (y_line[1] - y_line[0]) / (x_line[1] - x_line[0])
    poly_deriv = np.polyder(polynomial)

    def find_intersection(x_val):
        return poly_deriv(x_val) - slope_line

    initial_guess = power_first_La_increase
    x_intersection = fsolve(find_intersection, initial_guess)[0]
    y_intersection = polynomial(x_intersection)

    dx = np.diff(x_fit)
    dy = np.diff(y_fit)
    slopes = dy / dx
    max_slope_index = np.argmax(np.abs(slopes))
    x_max_slope = x_fit[max_slope_index]
    y_max_slope = y_fit[max_slope_index]

    # handmatige LT2 op 4.0 mmol/L
    y_intersection = 4.0

    def find_x_intersection(x_val):
        return polynomial(x_val) - y_intersection

    x_intersection = fsolve(find_x_intersection, x_max_slope)[0]

    # LT1
    y_LT1 = ((y_lactate.iloc[0] + y_lactate.iloc[0]) / 2) + 1.0

    def find_x_LT1(x_val):
        return polynomial(x_val) - y_LT1

    initial_guess_LT1 = power_first_La_increase
    x_LT1 = fsolve(find_x_LT1, x_max_slope)[0]

    lt1_power = x_LT1
    lt1 = y_LT1
    lt2_power = x_intersection
    lt2_lact = y_intersection

    lt1_wattage_values = x_power[x_power <= lt1_power]
    split_50_50_wattage = lt1_power * 0.6

    above_lt2_wattage_values = x_power[x_power >= lt2_power]
    split_75_25_wattage = above_lt2_wattage_values.quantile(0.6)

    # Interpolaties
    hr_interpolation = interp1d(
        x_power, y_hr, kind="linear", fill_value="extrapolate"
    )
    VE_interpolation = interp1d(
        x_power, mean_values_VE, kind="linear", fill_value="extrapolate"
    )
    VO2_interpolation = interp1d(
        x_power, mean_values_VO2, kind="linear", fill_value="extrapolate"
    )
    row_5_interpolation = interp1d(
        x_power, row_5_numeric, kind="linear", fill_value="extrapolate"
    )

    power_rest = round(float(x_power.min()), 1)
    power_split_50_50 = round(float(split_50_50_wattage), 1)
    power_LT1 = round(float(lt1_power), 1)
    power_LT2 = round(float(lt2_power), 1)
    power_split_75_25 = round(float(split_75_25_wattage), 1)
    power_max = round(float(x_power.max()), 1)

    # ---- Steady state voor lactaat_VT1 / VT2 (zoals in script) ----

    weight = df_1.iloc[6, 1]

    vo2 = df_3.iloc[4, 2:]
    hartslag = df_3.iloc[8, 2:]
    lactaat = df_3.iloc[9, 2:]
    if sport == "Hardlopen":
        snelheid = df_3.iloc[10, 2:]
        tempo = snelheid.apply(
            lambda s: f"{int(60/s)}:{int(round(((60/s) % 1) * 60)):02d}"
            if s > 0
            else None
        )
    else:
        power = df_3.iloc[10, 2:]
        prestatie = df_3.iloc[10, 2:]
        powermax = power.iloc[-1]
        percvt1max = round((powervt1 / powermax * 100), 1)
        percvt2max = round((powervt2 / powermax * 100), 1)

    tijdstart = df_3.iloc[1, 2:]

    # lactaat rond VT1
    target = to_td(tijdvt1)
    s_td = tijdstart.map(to_td)
    diff_s = (s_td - target).abs().dt.total_seconds().fillna(np.inf)
    posities0 = np.sort(np.argsort(diff_s.to_numpy())[:2])
    lactaat_vt1 = lactaat[posities0]

    # lactaat rond VT2
    target = to_td(tijdvt2)
    s_td = tijdstart.map(to_td)
    diff_s = (s_td - target).abs().dt.total_seconds().fillna(np.inf)
    posities0 = np.sort(np.argsort(diff_s.to_numpy())[:2])
    lactaat_vt2 = lactaat[posities0]

    # ---- Evaluatie-gegevens voor korte KV-rij ----
    fields_eval = ["Voornaam", "Geslacht", "Leeftijd", "Gewicht (kg)", "Lengte (cm)"]
    values_eval = [f"{voornaam}", f"{geslacht}", f"{leeftijd}", f"{gewicht}", f"{lengte}"]

    # ---------------- Pagina 2 tekenen ----------------
    c = canvas.Canvas(output_path, pagesize=A4)

    # Header
    header_bottom = draw_header(c)

    total_w = PAGE_WIDTH - 2 * MARGIN

    # Korte gegevensrij
    kv_h = draw_kv_table_short(c, MARGIN, header_bottom, total_w)
    y = header_bottom - kv_h - 8

    # EVALUATIE-balk
    y = draw_eval_bar(c, MARGIN, y, total_w)

    # Grijze blokken (iets smaller dan de balk)
    block_width = total_w - 2 * BLOCK_INSET
    x_block = MARGIN + BLOCK_INSET

    if sport == "Hardlopen":
        # VT1/LT1
        vt1_text = [
            "VT1 en LT1 (respectievelijk Ventilatoire Threshold 1 en Lactate Threshold 1) zijn veelgebruikte drempelwaarden, die de overgang markeren van lichte naar matige inspanningsintensiteit. Boven de VT1 neemt de ademhaling (in l/min) sterker toe dan de opname van zuurstof. LT1 markeert het punt waarop lactaatwaarden voor het eerst beginnen toe te nemen. Beide drempels hebben te maken met anaëroob metabolisme (energieproductie zonder zuurstof) dat vanaf dit punt een grotere rol gaat spelen in de energielevering. De productie en de buffering van zuur (H+-ionen) neemt hierbij toe."
        ]
        vt1_table = [
            ("Snelheid", f"{snelheidvt1} km/u"),
            ("%Max (km/u)", f"{percvt1max} %"),
            ("Tempo", f"{tempovt1} mm:ss/k"),
            ("Hartslag", f"{hrvt1} bpm"),
            ("Lactaat", f"{lactaat_vt1.iloc[0]} - {lactaat_vt1.iloc[1]} mmol/L"),
        ]
        y = draw_eval_section(
            c, "VT1 en LT1", vt1_text, vt1_table,
            x_block, y, block_width, gap=BLOCK_GAP
        )

        # VT2/LT2
        vt2_text = [
            "VT2 en LT2 (respectievelijk Ventilatoire Threshold 2 en Lactate Threshold 2) zijn veelgebruikte drempelwaarden, die de overgang markeren van matige naar zware inspanningsintensiteit. De aërobe energielevering (met zuurstof) komt boven deze drempel in de buurt van zijn limiet en de anaërobe energielevering wordt sterk geactiveerd in dit gebied. Inspanning boven deze drempel veroorzaakt pH-daling en een snelle ophoping van lactaat. Inspanningen boven deze drempel zullen snel leiden tot uitputting. "
            "Inspanningen boven de VT2, ook wel respiratoir compensatiepunt genoemd, worden gekenmerkt door een sterke CO2-productie en een disproportionele stimulatie van de ademhaling (hyperventileren). De LT2 is het punt waarboven lactaatwaarden in het bloed heel toenemen.",
        ]
        vt2_table = [
            ("Snelheid", f"{snelheidvt2} km/u"),
            ("%Max (km/u)", f"{percvt2max} %"),
            ("Tempo", f"{tempovt2} mm:ss/k"),
            ("Hartslag", f"{hrvt2} bpm"),
            ("Lactaat", f"{lactaat_vt2.iloc[0]} - {lactaat_vt2.iloc[1]} mmol/L"),
        ]
        y = draw_eval_section(
            c, "VT2 en LT2", vt2_text, vt2_table,
            x_block, y, block_width, gap=BLOCK_GAP
        )

        # Max prestatie
        max_text = [
            "De maximale prestatie wordt aan het einde van de test vastgesteld. Indien de laatste stap niet volledig is uitgevoerd, wordt de maximale prestatie bepaald op basis van de feitelijke duur van die laatste stap.",
            "",
            "De prestatie boven VT2 en LT2 wordt bepaald door het vermogen om weerstand te bieden tegen de vermoeidheid en daling van de pH. De aërobe energielevering bereikt hier zijn maximum. Hiernaast wordt de anaërobe energielevering hier ook sterk geactiveerd, leidend tot een verdere ophoping van lactaat in spieren en bloed.",
        ]
        max_table = [
            ("Snelheid", f"{snelheidmax} km/u"),
            ("%Max (km/u)", "100 %"),
            ("Tempo", f"{tempomax} mm:ss/k"),
            ("Hartslag", f"{hrmax} bpm"),
            ("Lactaat", f"{lactaat.iloc[-1]} mmol/L"),
        ]
        y = draw_eval_section(
            c, "Maximale Prestatie", max_text, max_table,
            x_block, y, block_width, gap=BLOCK_GAP
        )

        warning_lines = [
            "Het protocol van deze test is vanwege de langer durende stappen met name geschikt voor lactaatbepalingen. Daarom wordt de indeling in trainingszones ook gebaseerd op lactaatwaarden en niet op ventilatoire drempels. Een ramp-protocol is meer geschikt om deze nauwkeurig te bepalen. Voor de volledigheid worden deze drempels wel getoond.",
        ]
    else:
        # wielrennen
        vt1_text = [
            "VT1 en LT1 (respectievelijk Ventilatoire Threshold 1 en Lactate Threshold 1) worden aangeduid als de aerobe drempel.",
            "Bij VT1 neemt de ademhaling toe zonder sterke versnelling en markeert dit de grens tussen lichte en matige inspanning. LT1 is de eerste significante stijging in lactaat boven de basislijn.",
        ]
        vt1_table = [
            ("Vermogen", f"{power_LT1} Watt"),
            ("%Max (Watt)", f"{round((power_LT1 / power_max * 100), 1)} %"),
            ("Prestatie", f"{round((power_LT1 / weight), 1)} W/kg"),
            ("Hartslag", f"{hrvt1} bpm"),
            ("Lactaat", "2,0 - 3,1 mmol/L"),
        ]
        y = draw_eval_section(
            c, "VT1 en LT1", vt1_text, vt1_table,
            x_block, y, block_width, gap=BLOCK_GAP
        )

        vt2_text = [
            "VT2 en LT2 (respectievelijk Ventilatoire Threshold 2 en Lactate Threshold 2) worden basaal gedefinieerd als de anaerobe drempel.",
            "VT2 is het respiratoire compensatie punt waarop het lichaam aanzienlijk meer CO2 produceert en de ademhaling disproportioneel toeneemt, omdat het aerobe systeem niet meer voldoende energie levert en het lichaam overgaat op anaerobe energievoorziening. LT2 komt overeen met het tweede afbuigpunt op de bloedlactaatcurve en initieert het begin van lactaataccumulatie.",
        ]
        vt2_table = [
            ("Vermogen", f"{power_LT2} Watt"),
            ("%Max (Watt)", f"{round((power_LT2 / power_max * 100), 1)} %"),
            ("Prestatie", f"{round((power_LT2 / weight), 1)} W/kg"),
            ("Hartslag", f"{hrvt2} bpm"),
            ("Lactaat", "4,6 - 6,5 mmol/L"),
        ]
        y = draw_eval_section(
            c, "VT2 en LT2", vt2_text, vt2_table,
            x_block, y, block_width, gap=BLOCK_GAP
        )

        max_text = [
            "De maximale prestatie wordt aan het einde van de test vastgesteld. Indien de laatste stap niet volledig is uitgevoerd, wordt de maximale prestatie bepaald op basis van de feitelijke duur van die laatste stap.",
            "",
            "De prestatie boven VT2 en LT2 wordt bepaald door het vermogen om weerstand te bieden tegen de ophoping van lactaat in de spieren. Tussen VT2/LT2 en de maximale prestatie vindt er een accumulatie van lactaat plaats in de spieren.",
        ]
        max_table = [
            ("Vermogen", f"{power_max} Watt"),
            ("%Max (Watt)", "100 %"),
            ("Prestatie", f"{round((power_max / weight), 1)} W/kg"),
            ("Hartslag", f"{hrmax} bpm"),
            ("Lactaat", f"{lactaat.iloc[-1]} mmol/L"),
        ]
        y = draw_eval_section(
            c, "Maximale Prestatie", max_text, max_table,
            x_block, y, block_width, gap=BLOCK_GAP
        )

        warning_lines = [
            "De ventilatoire drempels zijn slechts een bepaling die door de onderzoekers van het High Performance Centre te Sittard worden gedaan.",
            "Deze bepalingen zijn lastig uitvoerbaar en uit de literatuur wordt zelfs geconstateerd dat het niet altijd mogelijk is deze te bepalen.",
            "Om deze reden zal voor het opstellen van de trainingszones de lactaatwaarden worden gebruikt.",
        ]

    # Let op!-blok
    y = draw_eval_section(
        c, "Let op!", warning_lines,
        table_pairs=None,
        x=x_block, y_top=y, width=block_width,
        gap=BLOCK_GAP
    )

    draw_footer(c, page=2, total=4)

    c.showPage()
    c.save()
    print(f"✅ Pagina 2 aangemaakt: {output_path}")
