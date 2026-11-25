"""Analizador léxico OLLIN.

Lee la matriz de transición desde SQL Server (base OLLIN_v2) y separa un programa en tokens.
Sirve para el análisis léxico: decide qué pieza de texto es cada token (palabra reservada,
identificador, número, operador, símbolo o cadena) y marca los errores.
"""
import pyodbc

# ---- Conexión: ajusta solo estas tres líneas si cambian tu servidor o tu base ----
SERVIDOR = r"DESKTOP-P4N2L0S"      # o el nombre que usas en SSMS
BASE = "OLLIN"
DRIVER = "ODBC Driver 17 for SQL Server"  # si falla, prueba "ODBC Driver 18 for SQL Server"

INICIAL, ERROR = "q0", "qERR"


def conectar(servidor=SERVIDOR, base=BASE, driver=DRIVER):
    return pyodbc.connect(
        f"DRIVER={{{driver}}};SERVER={servidor};DATABASE={base};Trusted_Connection=yes;"
    )


def cargar_desde_bd(con):
    """Devuelve (transiciones, categorias, simbolos):
    transiciones[estado][columna] = destino ; categorias[estado] = CAT ; simbolos[caracter] = id."""
    cur = con.cursor()
    categorias = {}
    for id_estado, categoria in cur.execute("SELECT id_estado, categoria FROM dbo.estados"):
        categorias[id_estado] = categoria

    nombre_de = {}
    for id_simbolo, simbolo in cur.execute("SELECT id_simbolo, simbolo FROM dbo.simbolos"):
        nombre_de[id_simbolo] = simbolo

    transiciones = {}
    for id_estado, id_simbolo, destino in cur.execute(
            "SELECT id_estado, id_simbolo, destino FROM dbo.transiciones"):
        transiciones.setdefault(id_estado, {})[nombre_de[id_simbolo]] = destino
    return transiciones, categorias, nombre_de


TRANS, CAT, NOMBRE = None, None, None


def inicializar(con=None):
    """Carga la matriz desde la base. Se llama una vez al iniciar."""
    global TRANS, CAT, NOMBRE
    propia = con is None
    con = con or conectar()
    TRANS, CAT, NOMBRE = cargar_desde_bd(con)
    if propia:
        con.close()
    return len(TRANS)


def columna(c):
    """Nombre de la columna de la matriz para un carácter. Minúsculas y caracteres fuera del alfabeto no existen."""
    return "ESP" if c == " " else c


def paso(estado, c):
    destino = TRANS[estado].get(columna(c))
    return destino if destino else ERROR


def mayor_lexema(linea, i):
    """Lexema más largo desde i que termine en un estado con categoría (maximal munch)."""
    estado, mejor = INICIAL, None
    for pos in range(i, len(linea)):
        estado = paso(estado, linea[pos])
        if estado == ERROR:
            break
        if CAT.get(estado):
            mejor = (pos + 1, CAT[estado])
    return mejor


def analizar(texto):
    tokens, errores, simbolos = [], [], []
    for num, linea in enumerate(texto.splitlines() or [""], 1):
        i = 0
        while i < len(linea):
            if linea[i] in (" ", "\t"):
                i += 1
                continue
            m = mayor_lexema(linea, i)
            if m is None:
                errores.append((num, i + 1, linea[i]))
                i += 1
                continue
            fin, categoria = m
            lexema = linea[i:fin]
            if categoria != "COMENTARIO":
                tokens.append((num, lexema, categoria))
                if categoria == "IDENTIFICADOR" and lexema not in [s[1] for s in simbolos]:
                    simbolos.append((len(simbolos) + 1, lexema))
            i = fin
    return tokens, errores, simbolos


def reporte(texto):
    if TRANS is None:
        inicializar()
    tokens, errores, simbolos = analizar(texto)
    out = ["ARCHIVO DE TOKENS"]
    out += [f"  línea {n:>3}: {cat:<26} {lex}" for n, lex, cat in tokens]
    out.append("\nERRORES LÉXICOS")
    out += [f"  línea {n:>3}: carácter no válido '{c}' (col {col})" for n, col, c in errores]
    out.append(f"  TOTAL DE ERRORES: {len(errores)}")
    out.append("\nTABLA DE SÍMBOLOS")
    out += [f"  {n:>3}  {nombre}" for n, nombre in simbolos]
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    inicializar()
    if len(sys.argv) > 1:
        print(reporte(open(sys.argv[1], encoding="utf-8").read()))
    else:
        import ventana
        ventana.abrir()