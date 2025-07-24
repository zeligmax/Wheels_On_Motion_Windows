import tkinter as tk
from tkinter import filedialog, messagebox, StringVar
from tkinter.ttk import Combobox, Treeview, Scrollbar, Style
import pandas as pd
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import threading
import os

# Configuración principal de la ventana
root = tk.Tk()
root.title("Mapa Sonoro")
root.geometry("800x700")
root.configure(bg="#2b2b2b")
fuente = ("Bahnschrift", 10)

# Estilo global oscuro
style = Style()
style.theme_use("clam")

# Estilo para Treeview (tabla)
style.configure("Treeview",
    background="#1e1e1e",
    foreground="white",
    fieldbackground="#1e1e1e",
    font=("Bahnschrift", 9)
)
style.configure("Treeview.Heading",
    background="#3c3f41",
    foreground="white",
    font=("Bahnschrift", 10, "bold")
)
style.map('Treeview', background=[('selected', '#5a5a5a')])

# Estilo para Combobox
style.configure("TCombobox",
    fieldbackground="#3c3f41",
    background="#3c3f41",
    foreground="white",
    arrowcolor="white"
)

# Variables globales
df = None
columna_unica_var = StringVar()
columnas_var = StringVar()

# Función para convertir una columna en una onda sonora estilo 8-bit
def columna_a_sonido(columna, duracion_total=3.0, samplerate=44100):
    datos = columna.dropna().astype(float).values
    if len(datos) < 2 or np.max(datos) == np.min(datos):
        return None
    datos_norm = (datos - np.min(datos)) / (np.max(datos) - np.min(datos))
    freqs = 300 + datos_norm * 1000
    duracion_nota = duracion_total / len(freqs)
    tono_final = np.array([], dtype=np.float32)
    for freq in freqs:
        t = np.linspace(0, duracion_nota, int(samplerate * duracion_nota), endpoint=False)
        onda = 0.6 * np.sign(np.sin(2 * np.pi * freq * t))
        if len(tono_final) > 0:
            transicion = int(0.01 * samplerate)
            mezcla = tono_final[-transicion:] * np.linspace(1, 0, transicion) + onda[:transicion] * np.linspace(0, 1, transicion)
            tono_final = np.concatenate((tono_final[:-transicion], mezcla, onda[transicion:]))
        else:
            tono_final = np.concatenate((tono_final, onda))
    return tono_final

# Mezcla de varias columnas
def columnas_a_sonido(columnas):
    tonos = [columna_a_sonido(df[col]) for col in columnas if col in df.columns]
    tonos = [t for t in tonos if t is not None]
    if not tonos:
        return None
    longitud = min(len(t) for t in tonos)
    mezcla = sum(t[:longitud] for t in tonos)
    mezcla = mezcla / max(abs(mezcla))
    return mezcla

# Mostrar tabla con estilo
def mostrar_tabla(df):
    tabla.delete(*tabla.get_children())
    tabla["columns"] = list(df.columns)
    for col in df.columns:
        tabla.heading(col, text=col)
        tabla.column(col, anchor=tk.CENTER, width=100)
    for _, row in df.iterrows():
        tabla.insert("", tk.END, values=list(row))

# Cargar archivo
def cargar_archivo():
    ruta = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt")])
    if not ruta:
        return
    global df
    try:
        df = pd.read_csv(ruta)
        columnas_numericas = df.select_dtypes(include=[np.number]).columns
        columnas_var.set("\n".join(columnas_numericas))
        combo_columna['values'] = list(columnas_numericas)
        if columnas_numericas.any():
            combo_columna.current(0)
        combo_multi.delete(0, tk.END)
        for col in columnas_numericas:
            combo_multi.insert(tk.END, col)
        messagebox.showinfo("Éxito", "Archivo cargado correctamente.")
        mostrar_tabla(df)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

# Reproducción columna
def reproducir_columna():
    if df is None:
        return
    nombre_columna = columna_unica_var.get().strip()
    if nombre_columna not in df.columns:
        messagebox.showerror("Error", "Columna no encontrada.")
        return
    tono = columna_a_sonido(df[nombre_columna])
    if tono is not None:
        threading.Thread(target=lambda: (sd.play(tono, samplerate=44100), sd.wait()), daemon=True).start()

# Guardar columna
def guardar_columna():
    if df is None:
        return
    nombre_columna = columna_unica_var.get().strip()
    if nombre_columna not in df.columns:
        messagebox.showerror("Error", "Columna no encontrada.")
        return
    tono = columna_a_sonido(df[nombre_columna])
    if tono is None:
        return
    carpeta = filedialog.askdirectory()
    if carpeta:
        ruta_salida = os.path.join(carpeta, f"{nombre_columna}.wav")
        write(ruta_salida, 44100, tono.astype(np.float32))
        messagebox.showinfo("Guardado", f"Archivo guardado en:\n{ruta_salida}")

# Reproducir varias
def reproducir_variass():
    if df is None:
        return
    seleccionadas = [combo_multi.get(i) for i in combo_multi.curselection()]
    columnas = [col for col in seleccionadas if col in df.columns]
    if not columnas:
        messagebox.showerror("Error", "No se encontraron columnas válidas.")
        return
    mezcla = columnas_a_sonido(columnas)
    if mezcla is not None:
        threading.Thread(target=lambda: (sd.play(mezcla, samplerate=44100), sd.wait()), daemon=True).start()

# Guardar mezcla
def guardar_variass():
    if df is None:
        return
    seleccionadas = [combo_multi.get(i) for i in combo_multi.curselection()]
    columnas = [col for col in seleccionadas if col in df.columns]
    if not columnas:
        messagebox.showerror("Error", "No se encontraron columnas válidas.")
        return
    mezcla = columnas_a_sonido(columnas)
    if mezcla is None:
        return
    carpeta = filedialog.askdirectory()
    if carpeta:
        ruta_salida = os.path.join(carpeta, "mezcla_columnas.wav")
        write(ruta_salida, 44100, mezcla.astype(np.float32))
        messagebox.showinfo("Guardado", f"Archivo guardado en:\n{ruta_salida}")

# UI
btn_cargar = tk.Button(root, text="📂 Cargar archivo", command=cargar_archivo, font=fuente, bg="#3c3f41", fg="white")
btn_cargar.pack(pady=10)

combo_columna = Combobox(root, textvariable=columna_unica_var, font=fuente)
combo_columna.pack(pady=5)

btn_reproducir = tk.Button(root, text="▶ Reproducir columna", command=reproducir_columna, font=fuente, bg="#3c3f41", fg="white")
btn_reproducir.pack(pady=5)

btn_guardar = tk.Button(root, text="💾 Guardar columna como WAV", command=guardar_columna, font=fuente, bg="#3c3f41", fg="white")
btn_guardar.pack(pady=5)

lbl_multi = tk.Label(root, text="🎛 Selecciona múltiples columnas (Ctrl + click):", bg="#2b2b2b", fg="white", font=fuente)
lbl_multi.pack(pady=5)

combo_multi = tk.Listbox(root, selectmode="multiple", exportselection=0, bg="#3c3f41", fg="white", font=fuente, height=6, selectbackground="#5a5a5a", selectforeground="white")
combo_multi.pack(pady=5, ipady=5)

btn_multi = tk.Button(root, text="▶ Reproducir mezcla", command=reproducir_variass, font=fuente, bg="#3c3f41", fg="white")
btn_multi.pack(pady=5)

btn_guardar_multi = tk.Button(root, text="💾 Guardar mezcla como WAV", command=guardar_variass, font=fuente, bg="#3c3f41", fg="white")
btn_guardar_multi.pack(pady=5)

lbl_tabla = tk.Label(root, text="📊 Vista previa de la tabla:", bg="#2b2b2b", fg="white", font=fuente)
lbl_tabla.pack(pady=5)

# Tabla con scrolls
frame_tabla = tk.Frame(root, bg="#2b2b2b")
frame_tabla.pack(pady=5, fill=tk.BOTH, expand=True)

tabla = Treeview(frame_tabla, show="headings", selectmode="browse")
tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

scroll_y = Scrollbar(frame_tabla, orient="vertical", command=tabla.yview)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
tabla.configure(yscrollcommand=scroll_y.set)

scroll_x = Scrollbar(root, orient="horizontal", command=tabla.xview)
scroll_x.pack(fill=tk.X)
tabla.configure(xscrollcommand=scroll_x.set)

root.mainloop()
