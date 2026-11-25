"""Ventana del analizador léxico OLLIN, versión 2.0."""
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

import analizador as az

RETRASO_ANALISIS_MS = 600   # tiempo sin escribir antes de analizar en vivo


class Ventana:
    def __init__(self, raiz):
        self.raiz = raiz
        self.ultimo = None          # último resultado de analizar(), para la búsqueda
        self.pendiente = None       # id del análisis programado (análisis en vivo)
        self._construir()

    # ------------------------------------------------------------ construcción
    def _construir(self):
        r = self.raiz
        r.title(f"{az.NOMBRE} v{az.VERSION}")
        r.geometry("1200x700")

        # Identidad
        cab = tk.Frame(r)
        cab.pack(fill="x", padx=8, pady=(6, 0))
        tk.Label(cab, text=f"{az.NOMBRE}  v{az.VERSION}", font=("Arial", 12, "bold")).pack(side="left")
        tk.Label(cab, text=f"Autores: {az.AUTORES}", fg="#555").pack(side="left", padx=12)

        # Botones
        barra = tk.Frame(r)
        barra.pack(fill="x", padx=8, pady=6)
        botones = [("Cargar programa", self.cargar), ("Guardar programa", self.guardar_programa),
                   ("Analizar", self.analizar), ("Guardar resultado", self.guardar_resultado),
                   ("Guardar UML", self.guardar_uml)]
        for texto, cmd in botones:
            tk.Button(barra, text=texto, command=cmd, padx=10, pady=4).pack(side="left", padx=4)

        # Zona central: programa con números de línea y resultado
        centro = tk.Frame(r)
        centro.pack(fill="both", expand=True, padx=8)

        marco_prog = tk.Frame(centro)
        marco_prog.pack(side="left", fill="both", expand=True)
        tk.Label(marco_prog, text="Programa fuente").pack(anchor="w")
        cuerpo = tk.Frame(marco_prog)
        cuerpo.pack(fill="both", expand=True)
        self.numeros = tk.Text(cuerpo, width=4, padx=4, takefocus=0, border=0,
                               background="#eee", foreground="#666",
                               font=("Consolas", 11), state="disabled")
        self.numeros.pack(side="left", fill="y")
        self.programa = tk.Text(cuerpo, width=60, font=("Consolas", 11), undo=True,
                                yscrollcommand=self._sincronizar_scroll)
        sb_prog = tk.Scrollbar(cuerpo, command=self._scroll_programa)
        sb_prog.pack(side="right", fill="y")
        self.programa.config(yscrollcommand=lambda a, b: (sb_prog.set(a, b), self._sincronizar_scroll(a, b)))
        self.programa.pack(side="left", fill="both", expand=True)
        self.programa.bind("<KeyRelease>", lambda e: self._programar_analisis())
        self.programa.bind("<<Modified>>", lambda e: self._actualizar_numeros())

        marco_res = tk.Frame(centro)
        marco_res.pack(side="right", fill="both", expand=True, padx=(8, 0))
        tk.Label(marco_res, text="Resultado").pack(anchor="w")
        self.salida = scrolledtext.ScrolledText(marco_res, width=75, font=("Consolas", 10))
        self.salida.pack(fill="both", expand=True)

        # Zona inferior: búsqueda en la tabla de símbolos
        busq = tk.LabelFrame(r, text="Búsqueda en la tabla de símbolos")
        busq.pack(fill="x", padx=8, pady=6)
        self.entrada_busqueda = tk.Entry(busq, width=30, font=("Consolas", 11))
        self.entrada_busqueda.pack(side="left", padx=6, pady=6)
        self.modo = tk.StringVar(value="exacta")
        tk.Radiobutton(busq, text="Exacta", variable=self.modo, value="exacta").pack(side="left")
        tk.Radiobutton(busq, text="Por prefijo", variable=self.modo, value="prefijo").pack(side="left")
        tk.Button(busq, text="Buscar", command=self.buscar_simbolo, padx=10).pack(side="left", padx=6)
        self.resultado_busqueda = tk.Label(busq, text="", anchor="w", fg="#1f4e78")
        self.resultado_busqueda.pack(side="left", padx=8, fill="x", expand=True)

        # Barra de estado
        self.estado = tk.Label(r, text="Listo. Escriba un programa o cargue un archivo.", anchor="w", relief="sunken")
        self.estado.pack(fill="x", padx=8, pady=(0, 6))

        self.entrada_busqueda.bind("<Return>", lambda e: self.buscar_simbolo())
        self._actualizar_numeros()

    # ------------------------------------------------------------ números de línea
    def _actualizar_numeros(self):
        """Escribe 1, 2, 3... en la columna de la izquierda, una vez por línea."""
        lineas = int(self.programa.index("end-1c").split(".")[0])
        self.numeros.config(state="normal")
        self.numeros.delete("1.0", "end")
        self.numeros.insert("1.0", "\n".join(str(n) for n in range(1, lineas + 1)))
        self.numeros.config(state="disabled")
        self.programa.edit_modified(False)

    def _sincronizar_scroll(self, primero, ultimo):
        """Mantiene alineados los números con el texto al hacer scroll."""
        self.numeros.yview_moveto(primero)

    def _scroll_programa(self, *args):
        self.programa.yview(*args)

    # ------------------------------------------------------------ análisis
    def _programar_analisis(self):
        """Análisis en vivo: espera un momento sin escribir y luego analiza."""
        if self.pendiente:
            self.raiz.after_cancel(self.pendiente)
        self.pendiente = self.raiz.after(RETRASO_ANALISIS_MS, self.analizar)

    def analizar(self):
        self.pendiente = None
        texto = self.programa.get("1.0", "end-1c")
        try:
            self.ultimo = az.analizar(texto)
            self.salida.delete("1.0", "end")
            self.salida.insert("1.0", az.reporte(texto))
            r = self.ultimo
            self.estado.config(text=f"Tokens: {len(r['tokens'])}   Errores: {len(r['errores'])}   "
                                    f"Advertencias de tabulación: {len(r['tabulacion'])}")
        except Exception as ex:
            self.estado.config(text=f"No se pudo analizar: {ex}")

    def buscar_simbolo(self):
        texto = self.entrada_busqueda.get().strip()
        if not self.ultimo:
            self.analizar()
        if not self.ultimo:
            self.resultado_busqueda.config(text="Primero analice un programa.")
            return
        if not texto:
            self.resultado_busqueda.config(text="Escriba un nombre para buscar.")
            return
        hallados = az.buscar(self.ultimo["simbolos"], texto, self.modo.get())
        if not hallados:
            self.resultado_busqueda.config(text=f"No se encontró '{texto}' ({self._nombre_modo()}).")
        else:
            detalle = "; ".join(f"{s['nombre']} (tipo {s['tipo']}, línea {s['linea']})" for s in hallados)
            self.resultado_busqueda.config(text=f"{len(hallados)} encontrado(s): {detalle}")

    def _nombre_modo(self):
        return "búsqueda exacta" if self.modo.get() == "exacta" else "búsqueda por prefijo"

    # ------------------------------------------------------------ archivos
    def cargar(self):
        ruta = filedialog.askopenfilename(filetypes=[("Texto", "*.txt"), ("Todos", "*.*")])
        if ruta:
            with open(ruta, encoding="utf-8") as f:
                contenido = f.read()
            self.programa.delete("1.0", "end")
            self.programa.insert("1.0", contenido)
            self._actualizar_numeros()
            self.analizar()

    def guardar_programa(self):
        self._guardar_texto(self.programa.get("1.0", "end-1c"), "programa")

    def guardar_resultado(self):
        self._guardar_texto(self.salida.get("1.0", "end-1c"), "resultado")

    def guardar_uml(self):
        self._guardar_texto(az.diagrama_uml(), "diagrama UML", extension=".mmd")

    def _guardar_texto(self, contenido, que, extension=".txt"):
        ruta = filedialog.asksaveasfilename(defaultextension=extension)
        if not ruta:
            return
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
            self.estado.config(text=f"{que.capitalize()} guardado en {ruta}")
        except OSError as ex:
            messagebox.showerror("Error al guardar", str(ex))


def abrir():
    raiz = tk.Tk()
    Ventana(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    try:
        az.inicializar()   # conecta a SQL Server y carga la matriz
    except Exception as ex:
        messagebox.showerror("Error de conexión", f"No se pudo conectar a la base:\n{ex}")
        raise SystemExit(1)
    abrir()