import tkinter as tk
from tkinter import filedialog, messagebox, StringVar
from tkinter.ttk import Combobox, Treeview, Scrollbar, Style
import pandas as pd
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import threading
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# --- Configuración principal de la ventana ---
root = tk.Tk()
root.title("Mapa Sonoro")
root.geometry("900x750")
root.configure(bg="#2b2b2b")
fuente = ("Bahnschrift", 11)

# Estilo global oscuro
style = Style()
style.theme_use("clam")

# Estilo para Treeview (tabla)
style.configure("Treeview",
    background="#1e1e1e",
    foreground="white",
    fieldbackground="#1e1e1e",
    font=("Bahnschrift", 10)
)
style.configure("Treeview.Heading",
    background="#3c3f41",
    foreground="white",
    font=("Bahnschrift", 11, "bold")
)
style.map('Treeview', background=[('selected', '#5a5a5a')])

# Estilo para Combobox
style.configure("TCombobox",
    fieldbackground="#3c3f41",
    background="#3c3f41",
    foreground="white",
    arrowcolor="white",
    font=("Bahnschrift", 11)
)

# Variables globales
df = None
columna_unica_var = StringVar()
columnas_var = StringVar()

# --- Funciones para sonido, tabla, gráficos (sin cambios) ---
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

def columnas_a_sonido(columnas):
    tonos = [columna_a_sonido(df[col]) for col in columnas if col in df.columns]
    tonos = [t for t in tonos if t is not None]
    if not tonos:
        return None
    longitud = min(len(t) for t in tonos)
    mezcla = sum(t[:longitud] for t in tonos)
    mezcla = mezcla / max(abs(mezcla))
    return mezcla

def mostrar_tabla(df):
    tabla.delete(*tabla.get_children())
    tabla["columns"] = list(df.columns)
    for col in df.columns:
        tabla.heading(col, text=col)
        tabla.column(col, anchor=tk.CENTER, width=110)
    for _, row in df.iterrows():
        tabla.insert("", tk.END, values=list(row))

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
        if len(columnas_numericas) > 0:
            combo_columna.current(0)
        combo_multi.delete(0, tk.END)
        for col in columnas_numericas:
            combo_multi.insert(tk.END, col)
        messagebox.showinfo("Éxito", "Archivo cargado correctamente.")
        mostrar_tabla(df)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

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

def guardar_columna():
    if df is None:
        return
    nombre_columna = columna_unica_var.get().strip()
    if nombre_columna not in df.columns:
        messagebox.showerror("Error", "Columna no encontrada.")
        return
    tono = columna_a_sonido(df[nombre_columna])
    if tono is None:
        messagebox.showerror("Error", "No se puede generar sonido para esta columna.")
        return
    carpeta = filedialog.askdirectory()
    if carpeta:
        ruta_salida = os.path.join(carpeta, f"{nombre_columna}.wav")
        write(ruta_salida, 44100, tono.astype(np.float32))
        messagebox.showinfo("Guardado", f"Archivo guardado en:\n{ruta_salida}")

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
        mostrar_graficos(mezcla)

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

def mostrar_graficos(onda, samplerate=44100):
    if onda is None:
        return

    for widget in frame_graficos.winfo_children():
        widget.destroy()

    n = len(onda)
    fft_vals = np.fft.rfft(onda)
    fft_freq = np.fft.rfftfreq(n, 1/samplerate)
    magnitud = np.abs(fft_vals)

    fig, ax = plt.subplots(figsize=(7, 3), constrained_layout=True)
    fig.patch.set_facecolor('#2b2b2b')
    ax.set_facecolor('#1e1e1e')

    ax.plot(fft_freq, magnitud, color='orange')
    ax.set_title("Espectro de frecuencias (FFT)", color='white', fontsize=12, fontweight='bold')
    ax.set_xlabel("Frecuencia [Hz]", color='white', fontsize=10)
    ax.set_ylabel("Magnitud", color='white', fontsize=10)
    ax.tick_params(colors='white')
    ax.set_xlim(0, 2000)

    canvas = FigureCanvasTkAgg(fig, master=frame_graficos)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


# --- Funciones para hover y cursor mano ---
def on_enter(e):
    e.widget['background'] = '#505f70'

def on_leave(e):
    e.widget['background'] = '#3c3f41'

# --- UI con grid para mejor layout ---
# Contenedor principal con padding
padding_x = 15
padding_y = 10

btn_cargar = tk.Button(root, text="📂 Cargar archivo", command=cargar_archivo, font=fuente, bg="#3c3f41", fg="white", relief="flat", activebackground="#505f70")
btn_cargar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=padding_x, pady=padding_y)

combo_columna = Combobox(root, textvariable=columna_unica_var, font=fuente, state="readonly")
combo_columna.grid(row=1, column=0, columnspan=2, sticky="ew", padx=padding_x)

btn_reproducir = tk.Button(root, text="▶ Reproducir columna", command=reproducir_columna, font=fuente, bg="#3c3f41", fg="white", relief="flat", activebackground="#505f70")
btn_reproducir.grid(row=2, column=0, sticky="ew", padx=padding_x, pady=padding_y)

btn_guardar = tk.Button(root, text="💾 Guardar columna", command=guardar_columna, font=fuente, bg="#3c3f41", fg="white", relief="flat", activebackground="#505f70")
btn_guardar.grid(row=2, column=1, sticky="ew", padx=padding_x, pady=padding_y)

# Lista para seleccionar múltiples columnas
tk.Label(root, text="Selecciona columnas para mezclar:", bg="#2b2b2b", fg="white", font=("Bahnschrift", 12, "bold")).grid(row=3, column=0, columnspan=2, sticky="w", padx=padding_x, pady=(15,5))

combo_multi = tk.Listbox(root, selectmode=tk.MULTIPLE, font=fuente, bg="#1e1e1e", fg="white", bd=0, relief="flat", activestyle="none", height=8)
combo_multi.grid(row=4, column=0, columnspan=2, sticky="ew", padx=padding_x)
scroll_multi = Scrollbar(root, command=combo_multi.yview)
scroll_multi.grid(row=4, column=2, sticky="ns", pady=padding_y)
combo_multi.config(yscrollcommand=scroll_multi.set)

btn_reproducir_multi = tk.Button(root, text="▶ Reproducir mezcla", command=reproducir_variass, font=fuente, bg="#3c3f41", fg="white", relief="flat", activebackground="#505f70")
btn_reproducir_multi.grid(row=5, column=0, sticky="ew", padx=padding_x, pady=padding_y)

btn_guardar_multi = tk.Button(root, text="💾 Guardar mezcla", command=guardar_variass, font=fuente, bg="#3c3f41", fg="white", relief="flat", activebackground="#505f70")
btn_guardar_multi.grid(row=5, column=1, sticky="ew", padx=padding_x, pady=padding_y)

# Tabla para mostrar datos
tabla = Treeview(root, show="headings", selectmode="browse")
tabla.grid(row=6, column=0, columnspan=3, sticky="nsew", padx=padding_x, pady=padding_y)
scroll_tabla = Scrollbar(root, command=tabla.yview)
scroll_tabla.grid(row=6, column=3, sticky="ns", pady=padding_y)
tabla.config(yscrollcommand=scroll_tabla.set)

# Frame para gráficos
frame_graficos = tk.Frame(root, bg="#2b2b2b")
frame_graficos.grid(row=7, column=0, columnspan=4, sticky="nsew", padx=padding_x, pady=(0,15))

# Configurar filas y columnas para expandir tabla y gráfico al redimensionar
root.grid_rowconfigure(6, weight=3)
root.grid_rowconfigure(7, weight=2)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# Aplicar efecto hover a botones
for boton in [btn_cargar, btn_reproducir, btn_guardar, btn_reproducir_multi, btn_guardar_multi]:
    boton.bind("<Enter>", on_enter)
    boton.bind("<Leave>", on_leave)
    boton.config(cursor="hand2")

root.mainloop()
