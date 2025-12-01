# -*- coding: utf-8 -*-
"""
Created on Thu Nov 20 11:19:31 2025

@author: nilsw
"""

from PyPDF2 import PdfMerger
import os

def combineer_paginas(output_path, *pdf_paths):
    """
    Combineert een reeks PDF-bestanden in volgorde.

    Parameters:
        output_path: het pad voor de samengestelde PDF
        *pdf_paths: lijst van individuele PDF-bestanden
    """
    merger = PdfMerger()

    for pdf in pdf_paths:
        if os.path.exists(pdf):
            merger.append(pdf)
        else:
            print(f"⚠ Waarschuwing: {pdf} niet gevonden en wordt overgeslagen.")

    merger.write(output_path)
    merger.close()

    print(f"✅ Samengesteld rapport gemaakt: {output_path}")