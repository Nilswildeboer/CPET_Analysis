# -*- coding: utf-8 -*-
"""
CPET-analyse
-------------------------------------------------------------
Auteur  : Nils Wildeboer
Doel    : Het maken van een compleet rapport op basis van een Excel en PDF bestand van een CPET meting met het [NAAM SYSTEEM]
    Uitlezen van CPET/step-test resultaten uit Excel, bepalen van LT1 en LT2
          (DMax-Modified), hartslag/ventilatie/VO2 bij sleutelpunt-wattages schatten,
          trainingszones opstellen en twee figuren exporteren (curve + tabel).
Datum start script: 11-11-2025
Datum script compleet: 

Benodigde packages (pip):
    pip install pandas numpy matplotlib scipy openpyxl
"""
from Functies.Clean_Slate import clear_all
print("\x1b[2J\033[H")
clear_all()
from Functies.dependencies import *

#%%
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
pagina1_path = os.path.join(BASE_DIR, "Pagina1.pdf")
pagina2_path = os.path.join(BASE_DIR, "Pagina2.pdf")
pagina3_path = os.path.join(BASE_DIR, "Pagina3.pdf")
pagina4_path = os.path.join(BASE_DIR, "Pagina4.pdf")
#%%
file_path = kies_bestand()
sport, lactaat = select_sport()
print("Geselecteerde sport:", sport)
print("Met lactaat?", lactaat)
#%%
data = lees_excel_data(file_path, sport)
data["base_dir"] = BASE_DIR
zones = bepaal_trainingszones(data, lactaat)
#%%

build_pagina1(data, zones, pagina1_path)
build_pagina2(data, zones, pagina2_path)
build_pagina3(data, pagina3_path)
build_pagina4(data, zones, pagina4_path)
#%%

# 1. Haal naam + datum op
persoon = data["persoon"]
voornaam = persoon["voornaam"]
achternaam = persoon["achternaam"]
datum = persoon["testDatum"]

# 2. Bestandsnaam maken
rapport_naam = f"Rapport_{voornaam}{achternaam}_{datum}.pdf".replace(" ", "")
rapport_pad = os.path.join(BASE_DIR, rapport_naam)

# 3. Samenvoegen in juiste volgorde
combineer_paginas(
    rapport_pad,
    pagina1_path,
    pagina2_path,
    pagina3_path,
    pagina4_path
)