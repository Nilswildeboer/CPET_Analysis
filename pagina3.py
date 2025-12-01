# -*- coding: utf-8 -*-
"""
Pagina 3 – CPET-grafiek en toelichting
Modulaire versie die werkt met de CPET_Analyse workflow.
Bevat exact dezelfde functionaliteit en visualiteit als het originele script.
"""

import os
from datetime import date
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from xml.sax.saxutils import escape

# ---- Layout constants ----
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 20
BLOCK_INSET = 40
BLOCK_GAP = 18

LOGO_PATH = "Mens_en_Techniek_Logo.png"


#-----------------------------------------------------------
# HEADER
#-----------------------------------------------------------
def draw_header(c, testDatum, printDate):
    try:
        logo = ImageReader(LOGO_PATH)
        c.drawImage(logo, MARGIN, PAGE_HEIGHT - MARGIN - 50,
                    width=80, height=50, preserveAspectRatio=True)
    except:
        pass

    x, y = MARGIN + 90, PAGE_HEIGHT - MARGIN - 5
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x, y, "Zuyd Hogeschool, Locatie HPC")

    c.setFont("Helvetica", 10)
    c.drawString(x, y - 16, "Eggerweg 4, 6135 LG Sittard")
    c.drawString(x, y - 30, "www.zuyd.nl/opleidingen/mens-en-techniek-biometrie")

    # zwarte datum box
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

    # scheidingslijn
    c.setFillColor(colors.black)
    c.line(MARGIN, by, PAGE_WIDTH - MARGIN, by)

    return by


#-----------------------------------------------------------
# KORTE GEGEVENSRIJ (net zoals pagina 2)
#-----------------------------------------------------------
def _col_widths(total_w):
    ratios = [1.5, 1, 1, 1.2, 1.2]
    s = sum(ratios)
    return [r/s * total_w for r in ratios]


def draw_kv_table_short(c, x, y, total_w, persoon):
    fields = ["Voornaam", "Geslacht", "Leeftijd", "Gewicht (kg)", "Lengte (cm)"]
    values = [
        persoon["voornaam"],
        persoon["geslacht"],
        persoon["leeftijd"],
        persoon["gewicht"],
        persoon["lengte"]
    ]

    col_w = _col_widths(total_w)
    row_h = 28
    tw = sum(col_w)
    th = row_h

    # rechthoek
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

    # onderlijntjes
    bot = y - th
    pad = 5
    ax = x
    for w in col_w:
        c.line(ax + pad, bot, ax + w - pad, bot)
        ax += w

    # inhoud
    cy = y
    ax = x
    for lab, val, w in zip(fields, values, col_w):
        c.setFont("Helvetica", 7)
        c.drawString(ax + 4, cy - 6, str(lab))
        c.setFont("Helvetica-Bold", 8)
        c.drawRightString(ax + w - 4, cy - th + 6, str(val))
        ax += w

    return th


#-----------------------------------------------------------
# FOOTER
#-----------------------------------------------------------
def draw_footer(c, page=3, total=4):
    y_line = 28
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.8)
    c.line(MARGIN, y_line, PAGE_WIDTH - MARGIN, y_line)

    text_y = y_line - 12

    c.setFont("Helvetica", 8)
    c.drawString(MARGIN, text_y, "Geprint door Zuyd")
    c.drawCentredString(PAGE_WIDTH/2, text_y, f"{page} / {total}")
    c.drawRightString(PAGE_WIDTH - MARGIN, text_y, "omnia 2.3")


#-----------------------------------------------------------
# PDF → PNG PREVIEW
#-----------------------------------------------------------
def render_page_to_png(pdf_path, page_idx=1, dpi=150):
    """Render één pagina van een PDF naar PNG ter preview."""
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_idx)
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    out_png = "__preview_page.png"
    pix.save(out_png)
    doc.close()
    return out_png, pix.width, pix.height


#-----------------------------------------------------------
# INTERACTIEVE CROPPER
#-----------------------------------------------------------
def choose_crop_rect(image_path):
    """Laat gebruiker met de muis rechthoek trekken."""
    root = tk.Tk()
    root.title("Selecteer de CPET-grafiek")

    img = Image.open(image_path)
    W, H = img.size

    scale = min(1, 1200 / W)
    disp_w, disp_h = int(W*scale), int(H*scale)
    disp_img = img.resize((disp_w, disp_h), Image.LANCZOS)

    tkimg = ImageTk.PhotoImage(disp_img, master=root)
    canvas = tk.Canvas(root, width=disp_w, height=disp_h)
    canvas.pack()
    canvas._img = tkimg
    canvas.create_image(0, 0, anchor="nw", image=tkimg)

    rect = None
    start = [0, 0]
    end = [0, 0]

    def on_press(e):
        nonlocal rect
        start[:] = e.x, e.y
        if rect:
            canvas.delete(rect)
            rect = None

    def on_drag(e):
        nonlocal rect
        end[:] = e.x, e.y
        if rect:
            canvas.delete(rect)
        rect = canvas.create_rectangle(start[0], start[1], end[0], end[1],
                                       outline="red", width=2)

    def on_release(e):
        end[:] = e.x, e.y
        root.quit()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    root.mainloop()
    root.destroy()

    x0 = min(start[0], end[0]) / scale
    y0 = min(start[1], end[1]) / scale
    x1 = max(start[0], end[0]) / scale
    y1 = max(start[1], end[1]) / scale

    return (x0 / W, y0 / H, x1 / W, y1 / H)


#-----------------------------------------------------------
# CROPPEN VAN DE GRAFIEK
#-----------------------------------------------------------
def extract_chart_image(src_pdf_path, page_idx, clip_fracs, dpi=300):
    doc = fitz.open(src_pdf_path)
    page = doc.load_page(page_idx)

    W = page.rect.width
    H = page.rect.height

    x0f, y0f, x1f, y1f = clip_fracs
    clip = fitz.Rect(W*x0f, H*y0f, W*x1f, H*y1f)

    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat, clip=clip)

    out_png = "chart_extracted.png"
    pix.save(out_png)
    doc.close()

    return out_png


#-----------------------------------------------------------
# VRAAG OM PDF + KNIPPEN
#-----------------------------------------------------------
def ask_and_crop_pdf():
    """Vraag PDF → preview → crop → PNG."""
    root = tk.Tk()
    root.withdraw()
    src_pdf = filedialog.askopenfilename(title="Kies PDF met CPET-grafiek")
    root.destroy()

    if not src_pdf:
        return None

    # preview
    preview_png, _, _ = render_page_to_png(src_pdf, page_idx=1)

    # cropselectie
    fracs = choose_crop_rect(preview_png)

    # high-res uitsnede
    return extract_chart_image(src_pdf, page_idx=1, clip_fracs=fracs)



#-----------------------------------------------------------
#  PAGINA 3 BOUWER
#-----------------------------------------------------------
def build_pagina3(data, output_path):
    """
    Bouwt pagina 3 van het CPET-rapport.
    Gebruikt:
      - data["persoon"]
      - data["sport"]
    """
    persoon = data["persoon"]
    sport = data["sport"]
    testDatum = persoon["testDatum"]
    printDate = date.today().strftime("%d-%m-%Y")

    c = canvas.Canvas(output_path, pagesize=A4)

    # Header + korte gegevensrij
    header_bottom = draw_header(c, testDatum, printDate)
    total_w = PAGE_WIDTH - 2*MARGIN
    kv_h = draw_kv_table_short(c, MARGIN, header_bottom, total_w, persoon)
    y = header_bottom - kv_h - 8

    # Breedte voor het grafiekvak
    block_width = total_w - 2*BLOCK_INSET
    x_block = MARGIN + BLOCK_INSET
    chart_h = 420

    # Laat gebruiker PDF selecteren & croppen
    chart_png = ask_and_crop_pdf()

    y_img_bottom = y - chart_h

    # Tekenen van grafiek
    if chart_png and os.path.exists(chart_png):
        img = ImageReader(chart_png)
        iw, ih = img.getSize()
        pad = 8
        img_w = block_width - 2*pad
        img_h = chart_h - 2*pad
        scale = min(img_w/iw, img_h/ih)
        dw, dh = iw*scale, ih*scale
        dx = x_block + (block_width - dw)/2
        dy = y_img_bottom + (chart_h - dh)/2
        c.drawImage(img, dx, dy, width=dw, height=dh, preserveAspectRatio=True)
    else:
        # fallback box
        c.setFillColor(colors.lightgrey)
        c.roundRect(x_block, y_img_bottom, block_width, chart_h, 8, fill=1, stroke=0)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Oblique", 9)
        c.drawCentredString(x_block + block_width/2,
                            y_img_bottom + chart_h/2,
                            "Geen grafiek geselecteerd")

    y = y_img_bottom - BLOCK_GAP

    # ---- Tekst (zoals origineel) ----
    if sport == "Hardlopen":
        lines = [
            "In de bovenstaande figuur is de inspanning grafisch in drie blokken weergeven. Het oranje deel staat"
            " voor de <b>rustfase</b>. Het blauwe blok betreft de <b>warming-up</b>, Het groene deel toont de "
            " <b>Intensieve Inspanning</b>, die eindigt wanneer deze niet meer vol te houden is.",
            "",
            " Vier parameters zijn zichtbaar in de figuur. De groene lijn laat de oplopende snelheid in <b>kilometer per uur</b> "
            " zien, die met constante tijdsintervallen toeneemt. De paarse lijn laat de <b>hartfrequentie</b> zien"
            " in slagen per minuut. De figuur toont verder de <b>VO<sub rise='-6' size='6'>2</sub> (volume ingeademd zuurstof)</b> en <b>VCO<sub rise='-6' size='6'>2</sub> (volume uitgeademd koolstofdioxide)</b>"
            " in <b>mL/min</b>. De <b>VO<sub rise='-6' size='6'>2</sub>max</b> is hierbij een weergave van de maximale zuurstofopname aan het eind"
            " van de test. Dit geeft de <b>maximale aërobe capaciteit</b> van de sporter weer. Om personen onderling"
            " te kunnen vergelijken wordt deze weergegeven per kg lichaamsgewicht (dus ml/min/kg)."
            " De <b>ABG-markers</b> in de grafiek laten de tijdstippen zien waarop lactaat is gemeten."
        ]
    else:
        lines = [
            "In de bovenstaande figuur is de inspanning grafisch in drie blokken weergeven. Het oranje deel staat"
            "voor de <b>rustfase</b>. Het blauwe blok betreft de <b>warming-up</b>, Het groene deel toont de "
            "<b>Intensieve Inspanning</b>, die eindigt wanneer deze niet meer vol te houden is.",
            "",
            "Vier parameters zijn zichtbaar in de figuur. De groene lijn laat de oplopende weerstand in <b>wattage</b> "
            "zien, dat met constante tijdsintervallen toeneemt, doorgaans tussen drie en vijf minuten, zodat "
            "het lactaatgehalte kan stabiliseren. Daarnaast wordt ook de <b>hartslag</b> weergegeven die theoretisch "
            "maximaal 220 minus uw leeftijd is. Het figuur toont verder de <b>VO2</b> (volume ingeademd zuurstof) en "
            "<b>VCO2</b> (volume uitgeademd koolstofdioxide) in mL/min tegenover de tijd waarbij ook uw <b>VO2max</b> is "
            "bepaald. De <b>VO2max</b> is de maximale hoeveelheid zuurstof per tijdseenheid per kilogram "
            "lichaamsgewicht kunnen opnemen en gebruiken voor de productie van energie. Opvallend is dat "
            "beide grafieken blijven stijgen en op een bepaald punt ze elkaar snijden waarna de <b>VCO2</b> een hogere "
            "waarde heeft dan de <b>VO2</b>. Verder is een groene verticale balk zichtbaar die aangeeft waarop uw "
            "<b>VO2max</b> is gebaseerd. Deze is veelal kenbaar wanneer de <b>VO2</b> tijdens een inspanning niet meer "
            "toeneemt. Als laatste bevatten de lijnen aan het einde van ieder tijdsinterval een <b>ABG-marker</b>, "
            "die het moment van <b>lactaatafname</b> uit de oorlel aangeeft."] 
    y = draw_text_block(c, "Toelichting", lines, x_block, y, block_width)

    draw_footer(c, page=3, total=4)

    c.showPage()
    c.save()

    print(f"✅ Pagina 3 aangemaakt: {output_path}")
    print("DEBUG: pagina3 pad =", os.path.abspath(output_path))



#-----------------------------------------------------------
# TEKSTBLOK (zoals in originele script)
#-----------------------------------------------------------
def draw_text_block(c, title, lines, x, y_top, width, gap=18):
    pad_x = 10
    pad_top = 6
    pad_bottom = 10
    title_font = "Helvetica-Bold"
    title_size = 10
    body_font = "Helvetica"
    body_size = 9
    leading = 11

    import re

    def safe(line):
        if line is None:
            return ""
        line = str(line)

        # tags die we wél willen laten werken (ook met attributen)
        allowed_pattern = r"</?(?:b|sub|sup|super)(?:\s+[^>]*)?>"
        placeholders = []

        def _store_tag(m):
            placeholders.append(m.group(0))
            return f"§§TAG{len(placeholders)-1}§§"

        # 1) haal toegestane tags tijdelijk uit de tekst
        line = re.sub(allowed_pattern, _store_tag, line)

        # 2) escape de rest
        line = escape(line)

        # 3) plaats tags terug
        for i, tag in enumerate(placeholders):
            line = line.replace(f"§§TAG{i}§§", tag)

        return line

    html = "<br/>".join(safe(l) for l in lines)

    style = ParagraphStyle("txt", fontName=body_font, fontSize=body_size, leading=leading)
    para = Paragraph(html, style)

    text_w = width - 2*pad_x
    _, para_h = para.wrap(text_w, 10000)

    title_h = title_size + 3
    box_h = title_h + pad_top + para_h + pad_bottom

    y0 = y_top - box_h
    c.setFillColor(colors.lightgrey)
    c.roundRect(x, y0, width, box_h, 6, fill=1, stroke=0)

    c.setFillColor(colors.black)
    c.setFont(title_font, title_size)
    c.drawString(x + pad_x, y0 + box_h - title_h, title)

    para.drawOn(c, x + pad_x, y0 + box_h - title_h - pad_top - para_h)

    return y0 - gap