# ====================================================
# /audio/sonido.py
# Lógica de generación de audio
# ====================================================

import numpy as np

def columna_a_sonido(columna, modo_duracion_var, entry_bpm, entry_total, samplerate=44100):
    datos = columna.dropna().astype(float).values
    if len(datos) == 0:
        return None

    if np.max(datos) == np.min(datos):
        freqs = np.array([440] * len(datos))
    else:
        datos_norm = (datos - np.min(datos)) / (np.max(datos) - np.min(datos))
        freqs = 300 + datos_norm * 1000

    if modo_duracion_var.get() == "bpm":
        try:
            bpm = float(entry_bpm.get())
        except:
            bpm = 120
        duracion_nota = 60.0 / bpm
    else:
        try:
            duracion_total = float(entry_total.get())
        except:
            duracion_total = 10.0
        duracion_nota = duracion_total / len(freqs)

    tono_final = np.array([], dtype=np.float32)
    for freq in freqs:
        t = np.linspace(0, duracion_nota, int(samplerate * duracion_nota), endpoint=False)
        onda = 0.6 * np.sign(np.sin(2 * np.pi * freq * t))
        if len(tono_final) > 0:
            transicion = int(0.01 * samplerate)
            mezcla = tono_final[-transicion:] * np.linspace(1, 0, transicion) + \
                     onda[:transicion] * np.linspace(0, 1, transicion)
            tono_final = np.concatenate((tono_final[:-transicion], mezcla, onda[transicion:]))
        else:
            tono_final = np.concatenate((tono_final, onda))
    return tono_final


def columnas_a_sonido(df, columnas, modo_duracion_var, entry_bpm, entry_total):
    columnas_validas = [col for col in columnas if col in df.columns]
    if not columnas_validas:
        return None
    datos_combinados = df[columnas_validas].sum(axis=1, skipna=True)
    return columna_a_sonido(datos_combinados, modo_duracion_var, entry_bpm, entry_total)