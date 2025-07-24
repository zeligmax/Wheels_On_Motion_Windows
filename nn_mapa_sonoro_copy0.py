import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import simpleaudio as sa
import os

# --- Funciones para sonido ---

def generar_tono(frecuencia, duracion=0.3, fs=44100):
    t = np.linspace(0, duracion, int(fs * duracion), False)
    # Sonido tipo "8-bit"/"r2d2" con onda cuadrada y modulación
    onda = 0.5 * np.sign(np.sin(2 * np.pi * frecuencia * t))
    # Añadimos modulación rápida para efecto "chip"
    mod_freq = 30
    mod = 0.5 * (1 + np.sign(np.sin(2 * np.pi * mod_freq * t)))
    onda *= mod
    return onda.astype(np.float32)

def aplicar_fade(onda, duracion_fade_ms=20, fs=44100):
    muestras_fade = int(fs * duracion_fade_ms / 1000)
    fade_in = np.linspace(0, 1, muestras_fade)
    fade_out = np.linspace(1, 0, muestras_fade)
    onda[:muestras_fade] *= fade_in
    onda[-muestras_fade:] *= fade_out
    return onda

def columna_a_sonido(columna):
    duracion_nota = 0.3  # segundos por nota
    fs = 44100
    duracion_fade_ms = 20
    muestras_fade = int(fs * duracion_fade_ms / 1000)

    tonos = []
    for valor in columna:
        try:
            frecuencia = 300 + (float(valor) * 8)
            tono = generar_tono(frecuencia, duracion=duracion_nota, fs=fs)
            tono = aplicar_fade(tono, duracion_fade_ms=duracion_fade_ms, fs=fs)
            tonos.append(tono)
        except ValueError:
            continue

    if not tonos:
        return np.array([])

    sonido = tonos[0]
    for siguiente_tono in tonos[1:]:
        sonido_final = sonido[:-muestras_fade]
        mezcla_crossfade = sonido[-muestras_fade:] + siguiente_tono[:muestras_fade]
        sonido = np.concatenate([sonido_final, mezcla_crossfade, siguiente_tono[muestras_fade:]])

    # Normalizar para evitar saturación
    sonido /= np.max(np.abs(sonido)) + 1e-6
    return sonido

def reproducir_sonido(sonido, fs=44100):
    if sonido.size == 0:
        messagebox.showwarning("Atención", "No hay sonido para reproducir.")
        return
    audio = (sonido * 32767).astype(np.int16)
    play_obj = sa.play_buffer(audio, 1, 2, fs)
    play_obj.wait_done()

def guardar_wav(sonido, ruta, fs=44100):
    from scipy.io.wavfile import write
    if sonido.size == 0:
        messagebox.showwarning("Atención", "No hay sonido para guardar.")
        return
    audio = (sonido * 32767).astype(np.int16)
    write(ruta, fs, audio)

# --- Funciones UI ---

def cargar_archivo():
    ruta = filedialog.askopenfilename(filetypes=[("CSV/TXT", "*.csv *.txt"), ("Todos los archivos", "*.*")])
    if not ruta:
        return
    global df
    try:
        if ruta.endswith('.csv'):
            df = pd.read_csv(ruta)
        else:
            df = pd.read_csv(ruta, delimiter='\t')
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")
        return
    mostrar_columnas()
    mostrar_tabla()

def mostrar_columnas():
    columnas = df.select_dtypes(include=[np.number]).columns.tolist()
    texto = "Columnas numéricas disponibles:\n" + ", ".join(columnas)
    lbl_columnas.config(text=texto)

def mostrar_tabla():
    for i in tabla.get_children():
        tabla.delete(i)
    tabla["columns"] = list(df.columns)
    tabla["show"] = "headings"
    # Configurar encabezados y estilo
    for col in df.columns:
        tabla.heading(col, text=col)
        tabla.column(col, width=100, anchor='center')

    # Limitar filas a 100 para rendimiento
    to_show = df.head(100)
    for _, row in to_show.iterrows():
        tabla.insert("", "end", values=list(row))

def reproducir_columna():
    col = combo_columnas.get()
    if not col or col not in df.columns:
        messagebox.showwarning("Atención", "Selecciona una columna válida.")
        return
    columna = df[col].dropna().values
    sonido = columna_a_sonido(columna)
    reproducir_sonido(sonido)

def reproducir_todas_columnas():
    columnas = df.select_dtypes(include=[np.number]).columns.tolist()
    if not columnas:
        messagebox.showwarning("Atención", "No hay columnas numéricas para reproducir.")
        return
    sonidos = []
    for col in columnas:
        col_data = df[col].dropna().values
        sonido = columna_a_sonido(col_data)
        if sonido.size > 0:
            sonidos.append(sonido)
    if not sonidos:
        messagebox.showwarning("Atención", "No hay sonido generado.")
        return
    # Ajustar longitudes
    max_len = max(len(s) for s in sonidos)
    mezcla = np.zeros(max_len)
    for s in sonidos:
        mezcla[:len(s)] += s
    mezcla /= np.max(np.abs(mezcla)) + 1e-6
    reproducir_sonido(mezcla)

def guardar_columna():
    col = combo_columnas.get()
    if not col or col not in df.columns:
        messagebox.showwarning("Atención", "Selecciona una columna válida.")
        return
    columna = df[col].dropna().values
    sonido = columna_a_sonido(columna)
    if sonido.size == 0:
        messagebox.showwarning("Atención", "No hay sonido para guardar.")
        return
    ruta = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
    if ruta:
        guardar_wav(sonido, ruta)
        messagebox.showinfo("Guardado", f"Archivo guardado en:\n{ruta}")

def guardar_todas():
    columnas = df.select_dtypes(include=[np.number]).columns.tolist()
    if not columnas:
        messagebox.showwarning("Atención", "No hay columnas numéricas para guardar.")
        return
    sonidos = []
    for col in columnas:
        col_data = df[col].dropna().values
        sonido = columna_a_sonido(col_data)
        if sonido.size > 0:
            sonidos.append(sonido)
    if not sonidos:
        messagebox.showwarning("Atención", "No hay sonido para guardar.")
        return
    max_len = max(len(s) for s in sonidos)
    mezcla = np.zeros(max_len)
    for s in sonidos:
        mezcla[:len(s)] += s
    mezcla /= np.max(np.abs(mezcla)) + 1e-6

    ruta = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
    if ruta:
        guardar_wav(mezcla, ruta)
        messagebox.showinfo("Guardado", f"Archivo guardado en:\n{ruta}")

# --- UI principal ---

root = tk.Tk()
root.title("Mapa Sonoro - Max")
root.geometry("900x600")
root.configure(bg="#2b2b2b")

# Fuente Bahnschrift (puede no estar en todos los sistemas, se adapta)
fuente = ("Bahnschrift", 11)

# Estilo ttk para Treeview (tabla)
style = ttk.Style(root)
style.theme_use('clam')
style.configure("Treeview",
                background="#2b2b2b",
                foreground="white",
                fieldbackground="#2b2b2b",
                font=fuente)
style.map('Treeview', background=[('selected', '#555555')], foreground=[('selected', 'white')])
style.configure("Treeview.Heading", background="#3c3f41", foreground="white", font=(fuente[0], 12, "bold"))

# Widgets UI

btn_cargar = tk.Button(root, text="📂 Cargar archivo CSV/TXT", command=cargar_archivo, font=fuente, bg="#3c3f41", fg="white")
btn_cargar.pack(pady=5)

lbl_columnas = tk.Label(root, text="No hay archivo cargado.", font=fuente, bg="#2b2b2b", fg="white")
lbl_columnas.pack(pady=5)

combo_columnas = ttk.Combobox(root, state="readonly", font=fuente, width=40)
combo_columnas.pack(pady=5)

btn_reproducir = tk.Button(root, text="▶️ Reproducir columna seleccionada", command=reproducir_columna, font=fuente, bg="#3c3f41", fg="white")
btn_reproducir.pack(pady=5)

btn_reproducir_todas = tk.Button(root, text="▶️ Reproducir todas columnas numéricas", command=reproducir_todas_columnas, font=fuente, bg="#3c3f41", fg="white")
btn_reproducir_todas.pack(pady=5)

btn_guardar = tk.Button(root, text="💾 Guardar columna seleccionada como WAV", command=guardar_columna, font=fuente, bg="#3c3f41", fg="white")
btn_guardar.pack(pady=5)

btn_guardar_todas = tk.Button(root, text="💾 Guardar todas las columnas numéricas como WAV", command=guardar_todas, font=fuente, bg="#3c3f41", fg="white")
btn_guardar_todas.pack(pady=5)

# Frame para tabla con borde y scrollbars
frame_tabla = tk.Frame(root, bg="#2b2b2b", highlightbackground="#4a4a4a", highlightcolor="#4a4a4a", highlightthickness=1)
frame_tabla.pack(fill="both", expand=True, padx=10, pady=10)

scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical")
scroll_y.pack(side="right", fill="y")

scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal")
scroll_x.pack(side="bottom", fill="x")

tabla = ttk.Treeview(frame_tabla,
                     yscrollcommand=scroll_y.set,
                     xscrollcommand=scroll_x.set,
                     selectmode="browse",
                     style="Treeview")
tabla.pack(fill="both", expand=True)

scroll_y.config(command=tabla.yview)
scroll_x.config(command=tabla.xview)

df = pd.DataFrame()  # Variable global vacía para el dataframe

# Actualizar combo_columnas cuando se cargue un archivo
def actualizar_combo_columnas():
    cols = df.select_dtypes(include=[np.number]).columns.tolist()
    combo_columnas['values'] = cols
    if cols:
        combo_columnas.current(0)
    else:
        combo_columnas.set('')

# Modificar mostrar_columnas para actualizar combo
def mostrar_columnas():
    columnas = df.select_dtypes(include=[np.number]).columns.tolist()
    texto = "Columnas numéricas disponibles:\n" + ", ".join(columnas)
    lbl_columnas.config(text=texto)
    actualizar_combo_columnas()

root.mainloop()
