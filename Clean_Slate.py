# -*- coding: utf-8 -*-
"""
Created on Tue Nov 11 11:34:53 2025

@author: nilsw
"""

def clear_all():
    """Clears all the variables from the workspace of the spyder application."""
    gl = globals().copy()
    for var in gl:
        if var[0] == '_': continue
        if 'func' in str(globals()[var]): continue
        if 'module' in str(globals()[var]): continue

        del globals()[var]
    from IPython import get_ipython
    get_ipython().run_line_magic('reset', '-f')