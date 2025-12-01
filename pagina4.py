# -*- coding: utf-8 -*-
"""
Pagina 4 – Trainingszones
Modulaire versie die werkt met CPET_Analyse.

Input:
    data  : dict van lees_excel_data(...)
    zones : dict van bepaal_trainingszones(...)  -> wordt nu alleen gebruikt
            als "garantie" dat de PNG's bestaan (inhoud wordt hier niet gelezen)

Uitvoer:
    PDF met:
        - header
        - korte persoonsinfo
        - titelbalk "Trainingszones"
        - figuur (high_definition_plot.png)
        - tabel (high_definition_table.png)
        - tekstblokken over de trainingszones
"""

from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

# -------------------------------------------------
# Layout & constants
# -------------------------------------------------
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 20

BLOCK_INSET = 40
BLOCK_GAP   = 10
TEXT_GAP    = 5

LOGO_PATH = "Mens_en_Techniek_Logo.png"


# -------------------------------------------------
# HEADER
# -------------------------------------------------
def draw_header(c, testDatum, printDate):
    """Zelfde stijl als de andere pagina's, maar met eigen functie."""
    try:
        logo = ImageReader(LOGO_PATH)
        c.drawImage(
            logo,
            MARGIN,
            PAGE_HEIGHT - MARGIN - 50,
            width=80,
            height=50,
            preserveAspectRatio=True,
        )
    except Exception:
        pass

    x, y = MARGIN + 90, PAGE_HEIGHT - MARGIN - 5
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "Zuyd Hogeschool, Locatie HPC")

    c.setFont("Helvetica", 10)
    c.drawString(x, y - 16, "Eggerweg 4, 6135 LG Sittard")
    c.drawString(
        x, y - 30, "www.zuyd.nl/opleidingen/mens-en-techniek-biometrie"
    )

    # Zwarte datum-box rechts
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
    c.drawString(bx + 65, by + bh - 44, str(printDate))

    # horizontale lijn onder header
    c.setFillColor(colors.black)
    c.line(MARGIN, by, PAGE_WIDTH - MARGIN, by)

    return by


# -------------------------------------------------
# KORTE GEGEVENSRIJ (uitgebreide versie zoals Pagina 4 origineel)
# -------------------------------------------------
def draw_kv_table_short(c, x, y, total_w, persoon):
    """
    Eén rij met 9 kolommen:
      Voornaam | Tweede naam | Achternaam | ID | Geboortedatum |
      Geslacht | Leeftijd | Gewicht (kg) | Lengte (cm)
    """
    fields = [
        "Voornaam",
        "Tweede naam",
        "Achternaam",
        "ID",
        "Geboortedatum",
        "Geslacht",
        "Leeftijd",
        "Gewicht (kg)",
        "Lengte (cm)",
    ]

    # persoon-dict uit lees_excel_data
    voornaam      = persoon.get("voornaam", "")
    achternaam    = persoon.get("achternaam", "")
    geslacht      = persoon.get("geslacht", "")
    leeftijd      = persoon.get("leeftijd", "")
    gewicht       = persoon.get("gewicht", "")
    lengte        = persoon.get("lengte", "")
    geboortedatum = persoon.get("geboortedatum", "")
    proefpersoon_id = persoon.get("id", "–")  # als je later een ID toevoegt

    values = [
        f"{voornaam}",
        "–",  # Tweede naam niet bekend
        f"{achternaam}",
        f"{proefpersoon_id}",
        f"{geboortedatum}",
        f"{geslacht}",
        f"{leeftijd}",
        f"{gewicht}",
        f"{lengte}",
    ]

    # zelfde kolombreedte-verhouding als origineel
    ratios = [1.2, 1.2, 1.2, 0.8, 1.2, 0.9, 0.9, 1.1, 1.1]
    s = float(sum(ratios))
    col_w = [r / s * total_w for r in ratios]

    row_h = 28
    tw = sum(col_w)
    th = row_h

    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(0.5)
    c.rect(x, y - th, tw, th, stroke=1, fill=0)

    ax = x
    for w in col_w:
        c.line(ax, y, ax, y - th)
        ax += w
    bot = y - th
    c.line(x, bot, x + tw, bot)

    # labels + waarden
    ax = x
    for label, val, w in zip(fields, values, col_w):
        c.setFont("Helvetica", 7)
        c.drawString(ax + 4, y - 6, str(label))
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(ax + w / 2.0, y - th + 6, str(val))
        ax += w

    return th


# -------------------------------------------------
# FOOTER
# -------------------------------------------------
def draw_footer(
    c,
    left_text="Geprint door Zuyd",
    page=None,
    total=None,
    right_text="omnia 2.3",
):
    """
    Simpele footer met horizontale lijn en pagina-nummering.
    FOOTER_LINE_Y wordt ook globaal gezet zodat de tekstblokken
    weten waar de “veilige” onderrand is.
    """
    global FOOTER_LINE_Y
    FOOTER_LINE_Y = 28

    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.line(MARGIN, FOOTER_LINE_Y, PAGE_WIDTH - MARGIN, FOOTER_LINE_Y)

    text_y = FOOTER_LINE_Y - 12
    c.setFont("Helvetica", 8)

    c.drawString(MARGIN, text_y, left_text)

    current = page if page is not None else c.getPageNumber()
    mid = f"{current} / {total}" if total is not None else f"{current}"
    c.drawCentredString(PAGE_WIDTH / 2.0, text_y, mid)

    c.drawRightString(PAGE_WIDTH - MARGIN, text_y, right_text)


# -------------------------------------------------
# HULPFUNCTIES VOOR TITELBALK & TEKST
# -------------------------------------------------
def title_bar(c, text, x, y, width, h=18):
    c.setFillColor(colors.lightgrey)
    c.rect(x, y - h, width, h, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x + width / 2.0, y - h + (h - 11) / 2.0 + 1, text)
    return y - h - 8


def draw_zone_paragraphs(c, x, y_top, w, gap=TEXT_GAP):
    """
    Tekstblokken onderaan de pagina met uitleg per trainingszone.
    """
    body = ParagraphStyle(
        "body", fontName="Helvetica", fontSize=8, leading=10
    )

    def para_height(text):
        p = Paragraph(text, body)
        return p, p.wrap(w, 10000)[1]

    blocks = [
        (
            "ERG LICHT",
            "Trainen met deze intensiteit helpt om te herstellen na een zware trainingssessie "
            "of om op te warmen voor de volgende sessie. De activiteit voelt gemakkelijk aan "
            "en is langdurig vol te houden. De metabole route is voornamelijk aerobe en de "
            "primaire energieleverancier is vetoxidatie.",
        ),
        (
            "LICHT",
            "Deze intensiteit verbetert het basisuithoudingsvermogen en het algehele "
            "cardiovasculaire systeem. De activiteit is comfortabel en goed vol te houden "
            "voor langere tijd. De metabole route is aerobe en vetten zijn de belangrijkste "
            "energieleverancier.",
        ),
        (
            "MATIG",
            "Bij matige intensiteit verbetert vooral het uithoudingsvermogen en de aerobe "
            "capaciteit. De activiteit voelt oncomfortabel maar nog wel beheersbaar. "
            "Het bloedlactaat begint langzaam boven de basislijn te stijgen.",
        ),
        (
            "ZWAAR",
            "Deze intensiteit verbetert het uithoudingsvermogen, het anaerobe vermogen en "
            "de lactaattolerantie. De activiteit voelt intens en de ervaren inspanning is "
            "hoog. Het bloedlactaat stijgt duidelijk. Koolhydraten zijn de belangrijkste "
            "energieleverancier, vetoxidatie neemt af.",
        ),
        (
            "MAXIMAAL",
            "Maximale intensiteit verbetert de VO<sub rise='-6' size='6'>2</sub>max en de lactaatdrempels. De activiteit "
            "is zeer intens, slechts kort vol te houden en voelt extreem zwaar aan. "
            "Alleen (goed) getrainde atleten zouden in deze zone moeten trainen.",
        ),
    ]

    bar_colors = [
        HexColor("#2ab34b"),
        HexColor("#f2cf24"),
        HexColor("#f36f44"),
        HexColor("#007ac2"),
        HexColor("#b432b0"),
    ]

    safe_bottom = (FOOTER_LINE_Y if "FOOTER_LINE_Y" in globals() else 28) + 18
    y = y_top
    BAR_H = 4
    BAR_W = 90

    for (title, text), col in zip(blocks, bar_colors):
        p, h_text = para_height(text)
        needed = 14 + BAR_H + 3 + h_text + gap
        if y - needed < safe_bottom:
            break  # geen ruimte meer

        # titel
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.black)
        c.drawString(x, y - 10, title)

        # gekleurde balk
        c.setFillColor(col)
        c.rect(x, y - 14 - BAR_H, BAR_W, BAR_H, stroke=0, fill=1)

        # tekst
        y_text = y - 14 - BAR_H - 3
        p.drawOn(c, x, y_text - h_text)
        y = y_text - h_text - gap

    return y


def draw_image_fullwidth(c, img_path, x, y_top, width, max_height=None):
    """
    Teken een PNG op volle breedte binnen 'width', met behoud van aspectratio.
    max_height: optionele beperking van de hoogte.
    Retourneert nieuwe y (onderkant van de afbeelding).
    """
    img = ImageReader(img_path)
    iw, ih = img.getSize()

    # schaal op breedte:
    scale_w = width / float(iw)
    dw = width
    dh = ih * scale_w

    # eventueel begrenzen op max hoogte
    if max_height is not None and dh > max_height:
        scale_h = max_height / float(ih)
        dw = iw * scale_h
        dh = max_height

    y0 = y_top - dh
    pad = 0
    dx = x + (width - dw) / 2.0
    dy = y0

    c.drawImage(
        img,
        dx,
        dy,
        width=dw,
        height=dh,
        preserveAspectRatio=True,
        mask="auto",
    )

    return y0


# -------------------------------------------------
# HOOFDFUNCTIE: PAGINA 4 BOUWEN
# -------------------------------------------------
def build_pagina4(data, zones, output_path):
    """
    Bouwt pagina 4 van het CPET-rapport.

    Verwacht:
        data["persoon"]["testDatum"]
        high_definition_plot.png
        high_definition_table.png
    """
    persoon = data["persoon"]
    testDatum = persoon["testDatum"]
    printDate = date.today().strftime("%d-%m-%Y")
    plot_path = zones["plot_path"]
    table_path = zones["table_path"]

    c = canvas.Canvas(output_path, pagesize=A4)

    # Header + korte persoonsgegevens
    header_bottom = draw_header(c, testDatum, printDate)
    total_w = PAGE_WIDTH - 2 * MARGIN

    kv_h = draw_kv_table_short(c, MARGIN, header_bottom, total_w, persoon)
    y = header_bottom - kv_h - 8

    # Titelbalk
    y = title_bar(c, "Trainingszones", MARGIN, y, total_w)

    # Blokbreedte
    x_block = MARGIN + BLOCK_INSET
    w_block = total_w - 2 * BLOCK_INSET

    # Grafiek – gebruik PNG die door trainingszones-script is gemaakt
    image_width = total_w * 0.8
    x_centered = MARGIN + (total_w - image_width) / 2.0
    y = draw_image_fullwidth(
        c,
        plot_path,
        x_centered,
        y,
        image_width,
        max_height=300,
    ) - 10

    # Tabel – ook op (bijna) volle breedte
    y = draw_image_fullwidth(
        c,
        table_path,
        x_block,
        y,
        w_block,
        max_height=None,
    ) - 12

    # Footer (zet FOOTER_LINE_Y)
    draw_footer(c, page=4, total=4)

    # Zone-teksten eronder
    draw_zone_paragraphs(c, x_block, y, w_block, gap=TEXT_GAP)

    c.showPage()
    c.save()
    print(f"✅ Pagina 4 aangemaakt: {output_path}")