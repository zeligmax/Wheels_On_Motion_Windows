import tkinter as tk
from tkinter import filedialog, messagebox, StringVar
from tkinter.ttk import Combobox, Treeview, Scrollbar, Style
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from audio.sonido import columna_a_sonido, columnas_a_sonido
from data.loader import cargar_csv

import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np

# Variables globales
df = None
columna_unica_var = None
columnas_var = None
modo_duracion_var = None

entry_bpm = None
entry_total = None
combo_columna = None
combo_multi = None
tabla = None
frame_graficos = None


# --- Funciones auxiliares ---
def mostrar_tabla(df):
    tabla.delete(*tabla.get_children())
    tabla["columns"] = list(df.columns)
    for col in df.columns:
        tabla.heading(col, text=col)
        tabla.column(col, anchor=tk.CENTER, width=110)
    for _, row in df.iterrows():
        tabla.insert("", tk.END, values=list(row))


def cargar_archivo():
    global df
    ruta = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt")])
    if not ruta:
        return
    try:
        df = cargar_csv(ruta)
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
    tono = columna_a_sonido(df[nombre_columna], modo_duracion_var, entry_bpm, entry_total)
    if tono is not None:
        tono = tono / np.max(np.abs(tono)) if np.max(np.abs(tono)) > 0 else tono
        threading.Thread(target=lambda: (sd.play(tono, samplerate=44100), sd.wait()), daemon=True).start()
        mostrar_graficos(tono)


def guardar_columna():
    if df is None:
        return
    nombre_columna = columna_unica_var.get().strip()
    if nombre_columna not in df.columns:
        messagebox.showerror("Error", "Columna no encontrada.")
        return
    tono = columna_a_sonido(df[nombre_columna], modo_duracion_var, entry_bpm, entry_total)
    if tono is None:
        messagebox.showerror("Error", "No se puede generar sonido para esta columna.")
        return
    ruta_salida = filedialog.asksaveasfilename(
        defaultextension=".wav",
        filetypes=[("WAV files", "*.wav")],
        initialfile=f"{nombre_columna}.wav"
    )
    if ruta_salida:
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
    mezcla = columnas_a_sonido(df, columnas, modo_duracion_var, entry_bpm, entry_total)
    if mezcla is not None:
        mezcla = mezcla / np.max(np.abs(mezcla)) if np.max(np.abs(mezcla)) > 0 else mezcla
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
    mezcla = columnas_a_sonido(df, columnas, modo_duracion_var, entry_bpm, entry_total)
    if mezcla is None:
        return
    ruta_salida = filedialog.asksaveasfilename(
        defaultextension=".wav",
        filetypes=[("WAV files", "*.wav")],
        initialfile="mezcla_columnas.wav"
    )
    if ruta_salida:
        write(ruta_salida, 44100, mezcla.astype(np.float32))
        messagebox.showinfo("Guardado", f"Archivo guardado en:\n{ruta_salida}")


# --- Gráfico ---
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


# --- Interfaz ---
def construir_interfaz(root):
    global columna_unica_var, columnas_var, modo_duracion_var
    global entry_bpm, entry_total, combo_columna, combo_multi, tabla, frame_graficos

    columna_unica_var = StringVar()
    columnas_var = StringVar()
    modo_duracion_var = StringVar(value="bpm")

    root.title("Mapa Sonoro - Dashboard")
    root.geometry("1200x750")
    root.configure(bg="#2b2b2b")

    # Estilo moderno
    fuente = ("Segoe UI", 10)
    style = Style()
    style.theme_use("clam")
    style.configure("Treeview", background="#1e1e1e", foreground="white",
                    fieldbackground="#1e1e1e", font=fuente)
    style.configure("Treeview.Heading", background="#3c3f41", foreground="white",
                    font=("Segoe UI", 10, "bold"))
    style.map('Treeview', background=[('selected', '#5a5a5a')])

    # --- Panel lateral ---
    sidebar = tk.Frame(root, bg="#1e1e1e", width=200)
    sidebar.pack(side="left", fill="y")

    btns = [
        ("📂 Cargar archivo", cargar_archivo),
        ("🎵 Reproducir columna", reproducir_columna),
        ("💾 Guardar columna", guardar_columna),
        ("🎶 Reproducir mezcla", reproducir_variass),
        ("💾 Guardar mezcla", guardar_variass)
    ]
    for txt, cmd in btns:
        tk.Button(sidebar, text=txt, command=cmd,
                  font=fuente, bg="#3c3f41", fg="white",
                  relief="flat", pady=5).pack(fill="x", padx=15, pady=8)

    # --- Zona principal ---
    main_area = tk.Frame(root, bg="#2b2b2b")
    main_area.pack(side="right", expand=True, fill="both")

    # Controles duración
    frame_duracion = tk.Frame(main_area, bg="#2b2b2b")
    frame_duracion.pack(side="top", fill="x", padx=15, pady=10)
    tk.Label(frame_duracion, text="Duración:", bg="#2b2b2b", fg="white",
             font=("Segoe UI", 10, "bold")).pack(anchor="w")
    entry_bpm = tk.Entry(frame_duracion, font=fuente, width=10, bg="#1e1e1e", fg="white")
    entry_bpm.insert(0, "120")
    entry_bpm.pack(anchor="w", pady=3)
    entry_total = tk.Entry(frame_duracion, font=fuente, width=10, bg="#1e1e1e", fg="white")
    entry_total.insert(0, "10")
    entry_total.pack(anchor="w")

    # Combo columnas
    combo_columna = Combobox(frame_duracion, textvariable=columna_unica_var,
                             font=fuente, state="readonly")
    combo_columna.pack(fill="x", pady=5)

    # Selección múltiple
    tk.Label(frame_duracion, text="Columnas para mezclar:", bg="#2b2b2b", fg="white",
             font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
    combo_multi = tk.Listbox(frame_duracion, selectmode=tk.MULTIPLE, font=fuente,
                             bg="#1e1e1e", fg="white", bd=0, relief="flat",
                             activestyle="none", height=8)
    combo_multi.pack(fill="both", expand=True)

    # Tabla de datos
    tabla = Treeview(main_area, show="headings", selectmode="browse")
    tabla.pack(fill="both", expand=True, padx=15, pady=10)

    # Scroll tabla
    scrollbar_tabla = Scrollbar(tabla, command=tabla.yview)
    tabla.configure(yscroll=scrollbar_tabla.set)
    scrollbar_tabla.pack(side="right", fill="y")

    # Frame gráficos
    frame_graficos = tk.Frame(main_area, bg="#2b2b2b", height=250)
    frame_graficos.pack(fill="both", expand=True, padx=15, pady=10)
