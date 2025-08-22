# ====================================================
# main.py
# Punto de entrada principal del programa
# ====================================================

import tkinter as tk
from ui.interfaz import construir_interfaz

if __name__ == "__main__":
    root = tk.Tk()
    construir_interfaz(root)
    root.mainloop()
