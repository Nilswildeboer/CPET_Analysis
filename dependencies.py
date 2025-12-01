# -*- coding: utf-8 -*-
"""
Created on Tue Nov 11 13:33:34 2025

@author: nilsw
"""
from Functies.Keuzemenu import select_sport, kies_bestand
from Functies.data_uitlezen import lees_excel_data
from Functies.trainingszones import bepaal_trainingszones
import os
from Functies.pagina1 import build_pagina1
from Functies.pagina2 import build_pagina2
from Functies.pagina3 import build_pagina3
from Functies.pagina4 import build_pagina4
from Functies.pdf_merge import combineer_paginas
import runpy