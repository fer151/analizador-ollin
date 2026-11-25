"""Ventana del analizador léxico OLLIN."""
import tkinter as tk
from tkinter import filedialog, scrolledtext
import analizador


def abrir():
    raiz = tk.Tk()
    raiz.title("Analizador léxico OLLIN")
    raiz.geometry("1100x650")

    marco_botones = tk.Frame(raiz)
    marco_botones.pack(fill="x", padx=8, pady=6)

    txt_prog = scrolledtext.ScrolledText(raiz, width=50, height=20, font=("Consolas", 11))
    txt_salida = scrolledtext.ScrolledText(raiz, width=60, height=20, font=("Consolas", 11))
    txt_prog.pack(side="left", fill="both", expand=True, padx=8, pady=4)
    txt_salida.pack(side="right", fill="both", expand=True, padx=8, pady=4)

    def cargar():
        ruta = filedialog.askopenfilename(filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if ruta:
            txt_prog.delete("1.0", "end")
            with open(ruta, encoding="utf-8") as f:
                txt_prog.insert("1.0", f.read())

    def guardar_programa():
        ruta = filedialog.asksaveasfilename(defaultextension=".txt")
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(txt_prog.get("1.0", "end-1c"))

    def analizar():
        texto = txt_prog.get("1.0", "end-1c")
        txt_salida.delete("1.0", "end")
        txt_salida.insert("1.0", analizador.reporte(texto))

    def guardar_salida():
        ruta = filedialog.asksaveasfilename(defaultextension=".txt")
        if ruta:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(txt_salida.get("1.0", "end-1c"))

    for texto, cmd in [("Cargar programa", cargar), ("Guardar programa", guardar_programa),
                       ("Analizar", analizar), ("Guardar resultado", guardar_salida)]:
        tk.Button(marco_botones, text=texto, command=cmd, padx=10, pady=4).pack(side="left", padx=4)

    raiz.mainloop()


if __name__ == "__main__":
    analizador.inicializar()   # conecta a SQL Server y carga la matriz
    abrir()