# -*- coding: utf-8 -*-
"""
Created on Thu Nov 13 16:33:01 2025

@author: nilsw
"""

# Functies/pdf_utils.py

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle

# ---------------------------------------
#  Algemene layout instellingen
# ---------------------------------------

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 20

# ---------------------------------------
#  HEADER
# ---------------------------------------
def draw_header(c,logo_path, test_datum, print_datum=""):
    logo = ImageReader(logo_path)
    c.drawImage(logo, MARGIN, PAGE_HEIGHT - MARGIN - 50, width=80, height=50, preserveAspectRatio=True)
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
    c.drawString(bx + 5, by + bh - 26, f"{test_datum}")
    c.line(bx + 3, by + bh - 30, bx + bw - 3, by + bh - 30)
    c.drawString(bx + 5, by + bh - 44, "Geprint op")
    c.drawString(bx + 65, by + bh - 44, f"{print_datum}")
    c.setFillColor(colors.black)
    c.line(MARGIN, by, PAGE_WIDTH - MARGIN, by)
    return by
# ---------------------------------------
#  FOOTER
# ---------------------------------------

def draw_footer(c, page=None, total=None,
                left_text="Geprint door Zuyd",
                right_text="omnia 2.3"):

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
    middle = f"{current} / {total}" if total else f"{current}"
    c.drawCentredString(PAGE_WIDTH / 2.0, text_y, middle)

    c.drawRightString(x_right, text_y, right_text)


# ---------------------------------------
#  tabellen pagina 1 tabel helpers
# ---------------------------------------

def build_table(data, col_widths, header=True, fontsize=8):
    tbl = Table(data, colWidths=col_widths)
    rows = len(data)

    alternating_bg = [
        ("BACKGROUND", (0, i), (-1, i),
         colors.whitesmoke if i % 2 == 0 else colors.white)
        for i in range(1 if header else 0, rows)
    ]

    tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), fontsize),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 1), (0, -1), "LEFT"),
    ] + alternating_bg))

    return tbl


# ---------------------------------------
#  VO2max utilities
# ---------------------------------------

def draw_subscript_text(c, x, y, base="VO", sub="2", tail="", size=12):
    """
    Tekent VO2 of VO2max netjes met subscript.
    """
    c.setFont("Helvetica-Bold", size)
    w_base = c.stringWidth(base, "Helvetica-Bold", size)
    w_sub  = c.stringWidth(sub,  "Helvetica-Bold", size * 0.7)
    w_tail = c.stringWidth(tail, "Helvetica-Bold", size)

    total = w_base + w_sub + w_tail
    x0 = x - total / 2

    t = c.beginText()
    t.setTextOrigin(x0, y)

    t.setFont("Helvetica-Bold", size)
    t.textOut(base)

    t.setFont("Helvetica-Bold", size * 0.7)
    t.setRise(-size * 0.3)
    t.textOut(sub)

    t.setRise(0)
    t.setFont("Helvetica-Bold", size)
    t.textOut(tail)

    c.drawText(t)