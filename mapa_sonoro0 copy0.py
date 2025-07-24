import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import numpy as np
import sounddevice as sd
import os
from scipy.io.wavfile import write

# ---------------------- FUNCIONES DE SONIDO ----------------------
def generar_tono(frecuencia, duracion=0.3, volumen=0.5, fs=44100):
    t = np.linspace(0, duracion, int(fs * duracion), endpoint=False)
    onda_base = np.sign(np.sin(2 * np.pi * frecuencia * t))
    mod_glitch = np.random.uniform(-20, 20, size=t.shape)
    glitch_onda = np.sign(np.sin(2 * np.pi * (frecuencia + mod_glitch) * t))
    mezcla = 0.7 * onda_base + 0.3 * glitch_onda
    onda = volumen * mezcla
    onda = np.clip(onda, -1, 1)
    return onda

def columna_a_sonido(columna):
    tono = []
    for valor in columna:
        try:
            frecuencia = 300 + (float(valor) * 8)
            tono.extend(generar_tono(frecuencia))
        except ValueError:
            continue
    return np.array(tono)

def columnas_a_sonido(columnas):
    ondas = []
    longitudes = []
    for nombre_col in columnas:
        if nombre_col not in df.columns:
            continue
        tono = columna_a_sonido(df[nombre_col])
        ondas.append(tono)
        longitudes.append(len(tono))
    if not ondas:
        return None
    min_len = min(longitudes)
    ondas = [onda[:min_len] for onda in ondas]
    suma = np.sum(ondas, axis=0)
    suma = suma / np.max(np.abs(suma))
    return suma

# ---------------------- FUNCIONES DE INTERFAZ ----------------------
def cargar_archivo():
    ruta = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt")])
    if not ruta:
        return
    global df
    try:
        df = pd.read_csv(ruta)
        columnas_var.set("\n".join(df.columns))
        messagebox.showinfo("Éxito", "Archivo cargado correctamente.")
        mostrar_tabla(df)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

def mostrar_tabla(dataframe):
    # Limpiar tabla previa
    tabla.delete(*tabla.get_children())
    tabla["columns"] = list(dataframe.columns)
    tabla["show"] = "headings"

    for col in dataframe.columns:
        tabla.heading(col, text=col)
        tabla.column(col, width=120, anchor='center')

    # Añadir filas (máximo 100 para no ralentizar)
    filas = dataframe.values.tolist()
    for i, fila in enumerate(filas[:100]):
        tabla.insert("", "end", values=fila)

def reproducir_columna():
    nombre_columna = entrada_columna.get().strip()
    if nombre_columna not in df.columns:
        messagebox.showerror("Error", "Columna no encontrada.")
        return
    tono = columna_a_sonido(df[nombre_columna])
    sd.play(tono, samplerate=44100)
    sd.wait()

def guardar_columna():
    nombre_columna = entrada_columna.get().strip()
    if nombre_columna not in df.columns:
        messagebox.showerror("Error", "Columna no encontrada.")
        return
    tono = columna_a_sonido(df[nombre_columna])
    carpeta = filedialog.askdirectory()
    if carpeta:
        ruta_salida = os.path.join(carpeta, f"{nombre_columna}.wav")
        write(ruta_salida, 44100, tono.astype(np.float32))
        messagebox.showinfo("Guardado", f"Archivo guardado en:\n{ruta_salida}")

def reproducir_variass():
    entrada = entrada_multi.get().strip()
    columnas = [col.strip() for col in entrada.split(",") if col.strip() in df.columns]
    if not columnas:
        messagebox.showerror("Error", "No se encontraron columnas válidas.")
        return
    mezcla = columnas_a_sonido(columnas)
    if mezcla is None:
        messagebox.showerror("Error", "No se pudo generar sonido.")
        return
    sd.play(mezcla, samplerate=44100)
    sd.wait()

def guardar_variass():
    entrada = entrada_multi.get().strip()
    columnas = [col.strip() for col in entrada.split(",") if col.strip() in df.columns]
    if not columnas:
        messagebox.showerror("Error", "No se encontraron columnas válidas.")
        return
    mezcla = columnas_a_sonido(columnas)
    if mezcla is None:
        messagebox.showerror("Error", "No se pudo generar sonido.")
        return
    carpeta = filedialog.askdirectory()
    if carpeta:
        ruta_salida = os.path.join(carpeta, "mezcla_columnas.wav")
        write(ruta_salida, 44100, mezcla.astype(np.float32))
        messagebox.showinfo("Guardado", f"Archivo guardado en:\n{ruta_salida}")

def reproducir_todas():
    columnas = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    if not columnas:
        messagebox.showerror("Error", "No hay columnas numéricas disponibles.")
        return
    mezcla = columnas_a_sonido(columnas)
    if mezcla is None:
        messagebox.showerror("Error", "No se pudo generar sonido.")
        return
    sd.play(mezcla, samplerate=44100)
    sd.wait()

def guardar_todas():
    columnas = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    if not columnas:
        messagebox.showerror("Error", "No hay columnas numéricas disponibles.")
        return
    mezcla = columnas_a_sonido(columnas)
    if mezcla is None:
        messagebox.showerror("Error", "No se pudo generar sonido.")
        return
    carpeta = filedialog.askdirectory()
    if carpeta:
        ruta_salida = os.path.join(carpeta, "todas_columnas.wav")
        write(ruta_salida, 44100, mezcla.astype(np.float32))
        messagebox.showinfo("Guardado", f"Archivo guardado en:\n{ruta_salida}")

# ---------------------- INTERFAZ ----------------------
root = tk.Tk()
root.title("Mapa Sonoro de Gráfico")
root.geometry("720x720")
root.configure(bg="#2b2b2b")

fuente = ("Bahnschrift", 10)

# Estilo ttk para modo oscuro
style = ttk.Style(root)
style.theme_use('clam')

style.configure("Treeview",
                background="#2b2b2b",
                foreground="white",
                fieldbackground="#2b2b2b",
                font=fuente,
                bordercolor="#4a4a4a",
                borderwidth=1,
                relief="solid")

style.map("Treeview",
          background=[("selected", "#575757")],
          foreground=[("selected", "white")])

style.configure("Treeview.Heading",
                background="#3c3f41",
                foreground="white",
                font=("Bahnschrift", 11, "bold"),
                relief="raised",
                borderwidth=1)

style.configure("Vertical.TScrollbar", troughcolor="#2b2b2b", background="#4a4a4a", arrowcolor="white")
style.configure("Horizontal.TScrollbar", troughcolor="#2b2b2b", background="#4a4a4a", arrowcolor="white")

frame = tk.Frame(root, bg="#2b2b2b")
frame.pack(pady=10)

btn_cargar = tk.Button(frame, text="📂 Cargar archivo CSV/TXT", command=cargar_archivo, font=fuente, bg="#3c3f41", fg="white")
btn_cargar.pack()

columnas_var = tk.StringVar()
lbl_columnas = tk.Label(root, textvariable=columnas_var, justify="left", bg="#2b2b2b", fg="white", font=fuente)
lbl_columnas.pack(pady=5)

entrada_columna = tk.Entry(root, font=fuente, bg="#3c3f41", fg="white", insertbackground="white")
entrada_columna.pack(pady=5)
entrada_columna.insert(0, "Tendencia_1")

btn_reproducir = tk.Button(root, text="▶ Reproducir columna", command=reproducir_columna, font=fuente, bg="#3c3f41", fg="white")
btn_reproducir.pack(pady=5)

btn_guardar = tk.Button(root, text="💾 Guardar columna como WAV", command=guardar_columna, font=fuente, bg="#3c3f41", fg="white")
btn_guardar.pack(pady=5)

lbl_multi = tk.Label(root, text="🎛 Reproducir múltiples columnas (coma):", bg="#2b2b2b", fg="white", font=fuente)
lbl_multi.pack(pady=5)

entrada_multi = tk.Entry(root, font=fuente, bg="#3c3f41", fg="white", insertbackground="white")
entrada_multi.pack(pady=5)
entrada_multi.insert(0, "Tendencia_1,Tendencia_2")

btn_multi = tk.Button(root, text="▶ Reproducir mezcla", command=reproducir_variass, font=fuente, bg="#3c3f41", fg="white")
btn_multi.pack(pady=5)

btn_guardar_multi = tk.Button(root, text="💾 Guardar mezcla como WAV", command=guardar_variass, font=fuente, bg="#3c3f41", fg="white")
btn_guardar_multi.pack(pady=5)

btn_todas = tk.Button(root, text="▶ Reproducir todas las columnas numéricas", command=reproducir_todas, font=fuente, bg="#3c3f41", fg="white")
btn_todas.pack(pady=10)

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

root.mainloop()
