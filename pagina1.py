# -*- coding: utf-8 -*-
"""
Created on Thu Nov 13 16:34:56 2025

@author: nilsw
"""

"""
Pagina 1 van het CPET-rapport
Modulair opgebouwd: alles komt uit data_uitlezen.py en trainingszones.py
Alle PDF-functies komen uit pdf_utils.py
"""

# Functies/pagina1.py
# Pagina 1 van het CPET-rapport, met originele layout (CPET-box, SAMENVATTING, VO2-zones)

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle
from datetime import date

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 20

# Spacing / sizes (zoals origineel)
GAP_AFTER_KV = 6
GAP_BETWEEN_TABLES = 10
GAP_AFTER_SUMMARY = 10

CPET_BAR_H = 18
CPET_BAR_GAP = 6

# Deze globals vullen we in build_pagina1()
LOGO_PATH = "Mens_en_Techniek_Logo.png"
testDatum = None
vandaag = None
rows = None
col_widths_kv = None
row_heights_kv = None
overview_data = None
summary_data = None
vo2max_table = None
vo2kgmax = None


# -------------------------------------------------
# Tekst & tabel helpers (zoals in origineel)
# -------------------------------------------------

def draw_header(c):
    """Header met logo, adres, datumkader."""
    logo = ImageReader(LOGO_PATH)
    c.drawImage(
        logo,
        MARGIN,
        PAGE_HEIGHT - MARGIN - 50,
        width=80,
        height=50,
        preserveAspectRatio=True,
    )
    x, y = MARGIN + 90, PAGE_HEIGHT - MARGIN - 5
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "Zuyd Hogeschool, Locatie HPC")
    c.setFont("Helvetica", 10)
    c.drawString(x, y - 16, "Eggerweg 4, 6135 LG Sittard")
    c.drawString(x, y - 30, "www.zuyd.nl/opleidingen/mens-en-techniek-biometrie")

    bw, bh = 120, 60
    bx = PAGE_WIDTH - MARGIN - bw
    by = PAGE_HEIGHT - MARGIN - bh
    c.setFillColor(colors.black)
    c.rect(bx, by, bw, bh, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(bx + 5, by + bh - 12, "Bezoekdatum")
    c.setFont("Helvetica", 9)
    c.drawString(bx + 5, by + bh - 26, f"{testDatum}")
    c.line(bx + 3, by + bh - 30, bx + bw - 3, by + bh - 30)
    c.drawString(bx + 5, by + bh - 44, "Geprint op")
    c.drawString(bx + 65, by + bh - 44, f"{vandaag}")
    c.setFillColor(colors.black)
    c.line(MARGIN, by, PAGE_WIDTH - MARGIN, by)
    return by


def draw_kv_table(c, x, y):
    """Key–value blok met persoonsgegevens, exact zoals in het originele script."""
    tw, th = sum(col_widths_kv), sum(row_heights_kv)
    c.setLineWidth(0.5)
    c.setStrokeColor(colors.lightgrey)
    c.rect(x, y - th, tw, th, stroke=1, fill=0)

    # verticale lijnen
    ax = x
    for w in col_widths_kv:
        c.line(ax, y, ax, y - th)
        ax += w
    c.line(x + tw, y, x + tw, y - th)

    # horizontale lijnen
    ay = y
    for h in row_heights_kv:
        c.line(x, ay, x + tw, ay)
        ay -= h

    # onderstrepen van waarden
    bot = y - th
    ax = x
    pad = 5
    for w in col_widths_kv:
        c.line(ax + pad, bot, ax + w - pad, bot)
        ax += w

    # labels en waarden
    cy = y
    for ri, row in enumerate(rows):
        h = row_heights_kv[ri]
        ax = x
        for ci, (lab, val) in enumerate(row):
            w = col_widths_kv[ci]
            c.setFont("Helvetica", 7)
            c.drawString(ax + 4, cy - 6, str(lab))
            c.setFont("Helvetica-Bold", 8)
            c.drawRightString(ax + w - 4, cy - h + 6, str(val))
            ax += w
        cy -= h
    return tw, th


def build_overview_table(total_width, columns):
    """Tabel voor CPET-overview (met kop OVERVIEW + CPET-zijbalk)."""
    side_bar_width = 26
    table_width = total_width - side_bar_width - 2
    colw = [table_width / columns] * columns
    tbl = Table(overview_data, colWidths=colw)
    alternating_bg = [
        ("BACKGROUND", (0, i), (-1, i),
         colors.whitesmoke if i % 2 == 0 else colors.white)
        for i in range(1, len(overview_data))
    ]
    tbl.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.white),
                ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.black),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("TOPPADDING", (0, 1), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 1),
            ]
            + alternating_bg
        )
    )
    return tbl, side_bar_width


def build_summary_table(total_width, columns):
    """Tabel voor SAMENVATTING-blok, met zijbalk."""
    side_bar_width = 26
    table_width = total_width - side_bar_width - 2
    colw = [table_width / columns] * columns
    tbl = Table(summary_data, colWidths=colw)
    alternating_bg = [
        ("BACKGROUND", (0, i), (-1, i),
         colors.whitesmoke if i % 2 == 0 else colors.white)
        for i in range(1, len(summary_data))
    ]
    tbl.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.white),
                ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.black),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("TOPPADDING", (0, 1), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 1),
            ]
            + alternating_bg
        )
    )
    return tbl, side_bar_width


def draw_table_with_header_bar(
    c,
    tbl,
    side_bar_width,
    margin_x,
    y,
    total_width,
    side_label,
    title,
    bar_h,
    table_to_bar_gap,
):
    """Tekent CPET-overview met grijze balk 'OVERVIEW' en verticale tekst 'CPET'."""
    _, h = tbl.wrap(0, 0)

    # bovenbalk
    c.setFillColor(colors.lightgrey)
    c.rect(margin_x, y + h + table_to_bar_gap,
           total_width, bar_h, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(
        margin_x + total_width / 2,
        y + h + table_to_bar_gap + bar_h / 2 - 3,
        title,
    )

    # afgeronde achtergrond voor tabel
    c.setFillColor(colors.lightgrey)
    c.roundRect(margin_x, y - 1, total_width, h + 2,
                radius=6, fill=1, stroke=1)

    # zij-label (bijv. CPET)
    c.saveState()
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 15)
    c.translate(margin_x + side_bar_width / 1.5, y + h / 2)
    c.rotate(90)
    c.drawCentredString(0, 0, side_label)
    c.restoreState()

    x_table = margin_x + side_bar_width
    tbl.drawOn(c, x_table, y)
    return h + table_to_bar_gap + bar_h


def draw_table_block(c, tbl, side_bar_width, margin_x, y, total_width, side_label):
    """SAMENVATTING-blok met verticale label."""
    _, h = tbl.wrap(0, 0)
    c.setFillColor(colors.lightgrey)
    c.roundRect(margin_x, y - 1, total_width, h + 2,
                radius=6, fill=1, stroke=1)
    c.saveState()
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 15)
    c.translate(margin_x + side_bar_width / 1.5, y + h / 2)
    c.rotate(90)
    c.drawCentredString(0, 0, side_label)
    c.restoreState()
    x_table = margin_x + side_bar_width
    tbl.drawOn(c, x_table, y)
    return h


# ================= VO2max helpers (exacte layout) =================

def _draw_vo2_text_with_subscript(
    c,
    x_center,
    y,
    base="VO",
    sub="2",
    tail="max",
    font="Helvetica-Bold",
    size=11,
):
    """Draw 'VO2max' met subscript 2, gecentreerd."""
    c.setFont(font, size)
    w_base = c.stringWidth(base, font, size)
    w_sub = c.stringWidth(sub, font, size * 0.7)
    w_tail = c.stringWidth(tail, font, size)
    total = w_base + w_sub + w_tail
    x = x_center - total / 2.0

    t = c.beginText()
    t.setTextOrigin(x, y)
    t.setFont(font, size)
    t.textOut(base)
    t.setFont(font, size * 0.7)
    t.setRise(-size * 0.30)
    t.textOut(sub)
    t.setRise(0)
    t.setFont(font, size)
    t.textOut(tail)
    c.drawText(t)


def _draw_diagonal_stripes(c, x, y, w, h, step=6):
    c.saveState()
    c.setLineWidth(1)
    c.setStrokeColor(colors.white)

    start = int((x - 2 * w) // step) * step
    end = int((x + 2 * w) // step) * step

    for i in range(start, end, step):
        c.line(i, y, i + h, y + h)
    c.restoreState()


def build_vo2_table(total_width):
    """Tabel met VO2max-gegevens (VO2max, snelheid/vermogen, tempo, HR)."""
    side_bar_width = 26
    table_width = total_width - side_bar_width - 2
    colw = [table_width / 5.0] * 5
    tbl = Table(vo2max_table, colWidths=colw)

    alternating_bg = [
        ("BACKGROUND", (0, i), (-1, i),
         colors.whitesmoke if i % 2 == 0 else colors.white)
        for i in range(1, len(vo2max_table))
    ]
    tbl.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.white),
                ("BACKGROUND", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.black),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("TOPPADDING", (0, 1), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 1),
            ]
            + alternating_bg
        )
    )

    table_h = tbl.wrap(0, 0)[1]
    VO2_TITLE_H = 20
    VO2_ZONES_H = 72
    total_h = VO2_TITLE_H + VO2_ZONES_H + table_h
    return tbl, side_bar_width, table_h, total_h, VO2_TITLE_H, VO2_ZONES_H


def draw_vo2_section(
    c,
    tbl,
    side_bar_width,
    margin_x,
    y,
    total_width,
    table_h,
    VO2_TITLE_H,
    VO2_ZONES_H,
    vo2_value,
):
    """Tekent de gehele VO2max-sectie met zones en pijl."""
    # titelbalk
    title_y = y + table_h + VO2_ZONES_H
    c.setFillColor(colors.lightgrey)
    c.rect(margin_x, title_y, total_width, VO2_TITLE_H, fill=1, stroke=0)
    _draw_vo2_text_with_subscript(
        c, margin_x + total_width / 2.0, title_y + VO2_TITLE_H / 2.0 - 5
    )

    # tabel-achtergrond
    _, table_height = tbl.wrap(0, 0)
    c.setFillColor(colors.lightgrey)
    c.roundRect(margin_x, y - 1, total_width, table_height + 2,
                radius=6, fill=1, stroke=1)
    x_table = margin_x + side_bar_width
    tbl.drawOn(c, x_table, y)

    # zonebalken
    zones = [
        ("Erg Zwak", colors.red),
        ("Zwak", colors.orangered),
        ("Matig", colors.orange),
        ("Gemiddelde", colors.yellowgreen),
        ("Goed", colors.green),
        ("Uitstekend", colors.blue),
        ("Uitmuntend", colors.purple),
    ]
    thresholds = [29, 34, 40, 45, 51, 56]

    inner_pad = 14
    zone_w = (total_width - 2 * inner_pad) / len(zones)
    zone_y = y + table_h
    bar_h = 14
    gap = 16
    shrink = 8
    left_margin_each = shrink / 2.0

    # label VO2/kg
    label_x = margin_x + 6
    label_top = title_y - 12
    c.setFillColor(colors.black)
    t = c.beginText()
    t.setTextOrigin(label_x, label_top)
    t.setFont("Helvetica-Bold", 9)
    t.textOut("VO")
    t.setFont("Helvetica-Bold", 9 * 0.7)
    t.setRise(-9 * 0.30)
    t.textOut("2")
    t.setRise(0)
    t.setFont("Helvetica-Bold", 9)
    t.textOut("/Kg")
    c.drawText(t)
    c.setFont("Helvetica", 8)
    c.drawString(label_x, label_top - 10, "mL/min/Kg")

    # gekleurde blokken
    for i, (_, col) in enumerate(zones):
        x = margin_x + inner_pad + i * zone_w
        bx = x + left_margin_each
        by = zone_y + gap + 18
        bw = zone_w - shrink
        bh = bar_h
        c.setFillColor(col)
        c.roundRect(bx, by, bw, bh, 3, fill=1, stroke=0)
        _draw_diagonal_stripes(c, bx + 1, by + 1, bw - 2, bh - 2, step=8)

    # drempelgetallen
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    num_y = zone_y + gap + 12
    for i, tnum in enumerate(thresholds):
        boundary_x = margin_x + inner_pad + (i + 1) * zone_w
        c.drawCentredString(boundary_x, num_y, str(tnum))

    # categorie-labels
    label_y = zone_y + gap + 2
    for i, (lbl, _) in enumerate(zones):
        x = margin_x + inner_pad + i * zone_w
        c.drawCentredString(x + zone_w / 2.0, label_y, lbl)

    # pijlpositie
    scale_min = thresholds[0]
    scale_max = thresholds[-1] + (thresholds[-1] - thresholds[-2])  # 56 + 5 = 61
    v = max(scale_min, min(scale_max, vo2_value))

    span_left = margin_x + inner_pad + left_margin_each
    span_right = margin_x + total_width - inner_pad - left_margin_each
    px = span_left + (v - scale_min) / float(scale_max - scale_min) * (
        span_right - span_left
    )

    # tekst boven pijl
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.black)
    c.drawCentredString(px, title_y + 4, f"{vo2_value:.1f}")

    start_x = px
    start_y = title_y + 4
    end_y = zone_y + gap + 18 + bar_h + 8

    c.saveState()
    c.setStrokeColor(colors.black)
    c.setLineWidth(1.0)
    c.line(start_x, start_y, px, end_y)

    arrow_width = 6
    arrow_height = 5
    c.setFillColor(colors.black)
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    path = c.beginPath()
    path.moveTo(px, end_y)
    path.lineTo(px - arrow_width / 2, end_y - arrow_height)
    path.lineTo(px + arrow_width / 2, end_y - arrow_height)
    path.close()
    c.drawPath(path, stroke=0, fill=1)


def draw_footer(
    c,
    left_text="Geprint door Zuyd",
    page=None,
    total=None,
    right_text="omnia 2.3",
):
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


# -------------------------------------------------
# Hoofdfunctie: bouw pagina 1 met originele layout
# -------------------------------------------------

def build_pagina1(data, zones, output_path, logo_path="Mens_en_Techniek_Logo.png"):
    """
    Bouwt pagina 1 exact zoals in het originele 'PDF rapport pagina 1.py',
    maar gebruikt:
      - data['df_1'], data['df_2'], data['df_3'], data['sport']
      - geen Tkinter of Excel-inlezen meer hier.
    """

    global LOGO_PATH, testDatum, vandaag
    global rows, col_widths_kv, row_heights_kv
    global overview_data, summary_data, vo2max_table, vo2kgmax

    LOGO_PATH = logo_path

    df_1 = data["df_1"]
    df_2 = data["df_2"]
    df_3 = data["df_3"]
    sport = data["sport"]  # verwacht 'wielrennen' of 'hardlopen'

    # ==== 4a) Algemene informatie (zoals origineel) ====
    voornaam = df_1.iloc[2, 1]
    achternaam = df_1.iloc[1, 1]
    geslacht = df_1.iloc[3, 1]
    leeftijd = round(df_1.iloc[4, 1], 1)
    lengte = df_1.iloc[5, 1]
    gewicht = df_1.iloc[6, 1]
    geboortedatum = df_1.iloc[7, 1]
    bmi = round((gewicht / (lengte / 100 * lengte / 100)), 1)
    testDatum = df_1.iloc[0, 4]
    vandaag = date.today().strftime("%d-%m-%Y")

    etniciteit = "Kaukasisch"
    analist = "N. Wildeboer"

    # ==== 4b) Resultaten (zoals origineel) ====
    tijdvt1 = df_2.iloc[4, 5]
    tijdvt1 = tijdvt1.strftime("%M:%S")
    tijdvt2 = df_2.iloc[4, 6]
    tijdvt2 = tijdvt2.strftime("%M:%S")
    tijdmax = df_2.iloc[4, 7]
    tijdmax = tijdmax.strftime("%M:%S")

    # ademhaling
    if sport == "Hardlopen":
        vo2rust = df_2.iloc[10, 3]
        vo2warmup = df_2.iloc[10, 4]
        vo2vt1 = df_2.iloc[10, 5]
        vo2vt2 = df_2.iloc[10, 6]
        vo2max = df_2.iloc[10, 7]

        vo2kgrust = df_2.iloc[11, 3]
        vo2kgwarmup = df_2.iloc[11, 4]
        vo2kgvt1 = df_2.iloc[11, 5]
        vo2kgvt2 = df_2.iloc[11, 6]
        vo2kgmax = df_2.iloc[11, 7]

        rqrust = df_2.iloc[12, 3]
        rqwarmup = df_2.iloc[12, 4]
        rqvt1 = df_2.iloc[12, 5]
        rqvt2 = df_2.iloc[12, 6]
        rqmax = df_2.iloc[12, 7]

        vtrust = df_2.iloc[17, 3]
        vtwarmup = df_2.iloc[17, 4]
        vtvt1 = df_2.iloc[17, 5]
        vtvt2 = df_2.iloc[17, 6]
        vtmax = df_2.iloc[17, 7]

        verust = df_2.iloc[16, 3]
        vewarmup = df_2.iloc[16, 4]
        vevt1 = df_2.iloc[16, 5]
        vevt2 = df_2.iloc[16, 6]
        vemax = df_2.iloc[16, 7]

        rfrust = df_2.iloc[18, 3]
        rfwarmup = df_2.iloc[18, 4]
        rfvt1 = df_2.iloc[18, 5]
        rfvt2 = df_2.iloc[18, 6]
        rfmax = df_2.iloc[18, 7]
    else:  # wielrennen
        vo2rust = df_2.iloc[8, 3]
        vo2warmup = df_2.iloc[8, 4]
        vo2vt1 = df_2.iloc[8, 5]
        vo2vt2 = df_2.iloc[8, 6]
        vo2max = df_2.iloc[8, 7]

        vo2kgrust = df_2.iloc[9, 3]
        vo2kgwarmup = df_2.iloc[9, 4]
        vo2kgvt1 = df_2.iloc[9, 5]
        vo2kgvt2 = df_2.iloc[9, 6]
        vo2kgmax = df_2.iloc[9, 7]

        rqrust = df_2.iloc[10, 3]
        rqwarmup = df_2.iloc[10, 4]
        rqvt1 = df_2.iloc[10, 5]
        rqvt2 = df_2.iloc[10, 6]
        rqmax = df_2.iloc[10, 7]

        vtrust = df_2.iloc[15, 3]
        vtwarmup = df_2.iloc[15, 4]
        vtvt1 = df_2.iloc[15, 5]
        vtvt2 = df_2.iloc[15, 6]
        vtmax = df_2.iloc[15, 7]

        verust = df_2.iloc[14, 3]
        vewarmup = df_2.iloc[14, 4]
        vevt1 = df_2.iloc[14, 5]
        vevt2 = df_2.iloc[14, 6]
        vemax = df_2.iloc[14, 7]

        rfrust = df_2.iloc[16, 3]
        rfwarmup = df_2.iloc[16, 4]
        rfvt1 = df_2.iloc[16, 5]
        rfvt2 = df_2.iloc[16, 6]
        rfmax = df_2.iloc[16, 7]

    # hart
    hrrust = df_2.iloc[22, 3]
    hrwarmup = df_2.iloc[22, 4]
    hrvt1 = df_2.iloc[22, 5]
    hrvt2 = df_2.iloc[22, 6]
    hrmax = df_2.iloc[22, 7]
    hrr = hrmax - hrrust

    if sport == "Hardlopen":
        snelheidrust = 0
        snelheidwarmup = df_2.iloc[5, 4]
        snelheidvt1 = df_2.iloc[5, 5]
        snelheidvt2 = df_2.iloc[5, 6]
        snelheidmax = df_2.iloc[5, 7]

        tempowarmup = 0
        tempovt1 = df_2.iloc[6, 5].strftime("%M:%S")
        tempovt2 = df_2.iloc[6, 6].strftime("%M:%S")
        tempomax = df_2.iloc[6, 7].strftime("%M:%S")
    else:
        powerrest = df_2.iloc[6, 5]
        powerwarmup = df_2.iloc[6, 5]
        powervt1 = df_2.iloc[6, 5]
        powervt2 = df_2.iloc[6, 5]

    # ==== 4c) Steady state (zoals origineel) ====
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
        prestatie = power / gewicht

    # ==== Data voor tabellen (exact originele layout) ====

    # Persoonsgegevens
    fields = [
        ["Volledige naam", "ID", "Geslacht", "Geboortedatum", "Leeftijd"],
        ["Analist", "Lengte (cm)", "Gewicht (kg)", "BMI (kg/m²)", "Etniciteit"],
    ]
    values = [
        [
            f"{voornaam} {achternaam}",
            "1",
            f"{geslacht}",
            f"{geboortedatum}",
            f"{leeftijd}",
        ],
        [f"{analist}", f"{lengte}", f"{gewicht}", f"{bmi}", f"{etniciteit}"],
    ]
    rows = [list(zip(f, v)) for f, v in zip(fields, values)]
    ratios = [2, 1, 1, 1.5, 1]
    total_w = PAGE_WIDTH - 2 * MARGIN
    col_widths_kv = [r / sum(ratios) * total_w for r in ratios]
    row_heights_kv = [28, 28]

    # CPET overview + summary + VO2max data
    if sport == "Hardlopen":
        overview_data = [
            ["", "Meting", "Rest", "Warm-Up", "VT1", "VT2", "Max", "%Pred"],
            ["t", "", "", "", tijdvt1, tijdvt2, tijdmax, ""],
            ["Snelheid", "Km/u", snelheidrust, snelheidwarmup,
             snelheidvt1, snelheidvt2, snelheidmax],
            ["tempo", "mm:ss/k", "", "", tempovt2, tempovt1, tempomax],
            ["VO2", "mL/min", vo2rust, vo2warmup, vo2vt1, vo2vt2, vo2max],
            ["VO2/Kg", "mL/min/Kg", vo2kgrust, vo2kgwarmup,
             vo2kgvt1, vo2kgvt2, vo2kgmax],
            ["RQ", "–", rqrust, rqwarmup, rqvt1, rqvt2, rqmax, ""],
            ["VE", "L/min", verust, vewarmup, vevt1, vevt2, vemax],
            ["VT", "L(b/tps)", vtrust, vtwarmup, vtvt1, vtvt2, vtmax],
            ["Rf", "1/min", rfrust, rfwarmup, rfvt1, rfvt2, rfmax],
            ["HR", "bpm", hrrust, hrwarmup, hrvt1, hrvt2, hrmax],
            ["HRR", "bpm", hrr, "", "", "", "", ""],
        ]
        summary_data = []
        summary_data.append(
            [
                "",
                "Snelheid (km/u)",
                "Tempo (mm:ss/k)",
                "Hartslag (bpm)",
                "Lactaat (mmol/L)",
                "VO2 (mL/min)",
                "Opmerking",
            ]
        )
        for i in range(len(snelheid)):
            if i == 0:
                opmerking = "Rust"
                tempo_val = "-"
            elif i == 1:
                opmerking = "Warming-up"
                tempo_val = tempo[i]
            elif i == len(snelheid) - 1:
                opmerking = "Maximaal"
                tempo_val = tempo[i]
            else:
                opmerking = "Inspanning"
                tempo_val = tempo[i]
            summary_data.append(
                [
                    f"Stap {i+1}",
                    snelheid[i],
                    tempo_val,
                    hartslag[i],
                    lactaat[i],
                    vo2[i],
                    opmerking,
                ]
            )
        vo2max_table = [
            ["", "Waarde", "Snelheid", "Tempo", "HR"],
            [
                "VO2max",
                f"{vo2max} mL/min",
                f"{snelheidmax} km/u",
                f"{tempomax} mm:ss/k",
                f"{hrmax} bpm",
            ],
        ]
    else:  # wielrennen
        overview_data = [
            ["", "Meting", "Rest", "Warm-Up", "VT1", "VT2", "Max", "%Pred"],
            ["t", "", "", "", tijdvt1, tijdvt2, tijdmax, ""],
            ["VO2", "mL/min", vo2rust, vo2warmup, vo2vt1, vo2vt2, vo2max],
            ["VO2/Kg", "mL/min/Kg", vo2kgrust, vo2kgwarmup,
             vo2kgvt1, vo2kgvt2, vo2kgmax],
            ["RQ", "–", rqrust, rqwarmup, rqvt1, rqvt2, rqmax, ""],
            ["VE", "L/min", verust, vewarmup, vevt1, vevt2, vemax],
            ["VT", "L(b/tps)", vtrust, vtwarmup, vtvt1, vtvt2, vtmax],
            ["Rf", "1/min", rfrust, rfwarmup, rfvt1, rfvt2, rfmax],
            ["HR", "bpm", hrrust, hrwarmup, hrvt1, hrvt2, hrmax],
            ["HRR", "bpm", hrr, "", "", "", "", ""],
        ]
        summary_data = []
        summary_data.append(
            [
                "",
                "Vermogen (Watt)",
                "Prestatie (W/kg)",
                "Hartslag (bpm)",
                "Lactaat (mmol/L)",
                "VO2 (mL/min)",
                "Opmerking",
            ]
        )
        for i in range(len(power)):
            if i == 0:
                opmerking = "Rust"
                prestatie_val = "-"
            elif i == 1:
                opmerking = "Warming-up"
                prestatie_val = round(prestatie[i], 1)
            elif i == len(power) - 1:
                opmerking = "Maximaal"
                prestatie_val = round(prestatie[i], 1)
            else:
                opmerking = "Inspanning"
                prestatie_val = round(prestatie[i], 1)
            summary_data.append(
                [
                    f"Stap {i+1}",
                    power[i],
                    prestatie_val,
                    hartslag[i],
                    lactaat[i],
                    vo2[i],
                    opmerking,
                ]
            )
        vo2max_table = [
            ["", "Waarde", "Vermogen", "Prestatie", "HR"],
            [
                "VO2max",
                f"{vo2max} mL/min",
                f"{power[-1]} Watt",
                f"{prestatie[-1]:.1f} W/kg",
                f"{hrmax} bpm",
            ],
        ]

    # ==== PDF bouwen (identiek aan originele build_pdf) ====
    c = canvas.Canvas(output_path, pagesize=A4)

    header_bottom = draw_header(c)
    kv_w, kv_h = draw_kv_table(c, MARGIN, header_bottom)
    kv_bottom = header_bottom - kv_h

    cursor_y = kv_bottom - GAP_AFTER_KV

    ov_tbl, ov_side = build_overview_table(kv_w, columns=8)
    ov_body_h = ov_tbl.wrap(0, 0)[1]
    ov_total_h = ov_body_h + CPET_BAR_GAP + CPET_BAR_H
    y_cpet = cursor_y - ov_total_h
    draw_table_with_header_bar(
        c,
        ov_tbl,
        ov_side,
        MARGIN,
        y_cpet,
        kv_w,
        "CPET",
        "OVERVIEW",
        CPET_BAR_H,
        CPET_BAR_GAP,
    )

    cursor_y = y_cpet - GAP_BETWEEN_TABLES

    sm_tbl, sm_side = build_summary_table(kv_w, columns=7)
    sm_body_h = sm_tbl.wrap(0, 0)[1]
    y_summary = cursor_y - sm_body_h
    draw_table_block(c, sm_tbl, sm_side, MARGIN, y_summary, kv_w, "SAMENVATTING")

    vo2_tbl, vo2_side, vo2_table_h, vo2_total_h, VO2_TITLE_H, VO2_ZONES_H = build_vo2_table(
        kv_w
    )
    y_vo2 = y_summary - GAP_AFTER_SUMMARY - vo2_total_h
    draw_vo2_section(
        c,
        vo2_tbl,
        vo2_side,
        MARGIN,
        y_vo2,
        kv_w,
        vo2_table_h,
        VO2_TITLE_H,
        VO2_ZONES_H,
        vo2kgmax,
    )

    draw_footer(c, page=c.getPageNumber(), total=4)

    c.showPage()
    c.save()
    print(f"✅ Pagina 1 aangemaakt: {output_path}")
