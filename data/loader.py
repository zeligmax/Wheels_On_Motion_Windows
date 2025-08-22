# ====================================================
# /data/loader.py
# Lógica para cargar datos desde CSV o TXT
# ====================================================

import pandas as pd

def cargar_csv(ruta):
    return pd.read_csv(ruta)
