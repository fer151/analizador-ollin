"""Analizador léxico OLLIN.
Este módulo NO tiene interfaz gráfica; la ventana (ventana.py) lo llama.
"""
import re
from collections import namedtuple

import pyodbc

#  Identidad
NOMBRE = "Analizador léxico OLLIN"
VERSION = "2.0"
AUTORES = ("Vallejo Espinoza Daniela Guadalupe; Campos Villanueva Fernando G.; "
           "Villa Vargas Karla Astrid")

#  Conexión
# Cambia solo estas tres líneas si cambian tu servidor, base o driver.
SERVIDOR = r"localhost\SQLEXPRESS"
BASE = "OLLIN"
DRIVER = "ODBC Driver 17 for SQL Server"

#  Constantes
INICIAL = "q0"          # estado de inicio de cada token
ERROR = "qERR"          # estado trampa: no hay transición válida
SANGRIA_MULTIPLO = 5    # la sangría debe ser múltiplo de 5 espacios
TIPOS_DATO = {"PR_INTEGER": "INTEGER", "PR_DECIMAL": "DECIMAL", "PR_STRING": "STRING"}

Token = namedtuple("Token", "linea columna lexema categoria")
ErrorLexico = namedtuple("ErrorLexico", "linea columna fragmento texto sugerencia")

# Matriz en memoria; la llena inicializar()
MATRIZ_TRANS = None     # MATRIZ_TRANS[estado][columna] = destino
MATRIZ_CAT = None       # MATRIZ_CAT[estado] = categoría del token (None si no es final)
NUM_ESTADOS = 0
NUM_SIMBOLOS = 0


#  1. CONEXIÓN
def conectar(servidor=SERVIDOR, base=BASE, driver=DRIVER):
    """Abre la conexión a SQL Server con la cuenta de Windows (sin contraseña)."""
    return pyodbc.connect(
        f"DRIVER={{{driver}}};SERVER={servidor};DATABASE={base};Trusted_Connection=yes;"
    )


def cargar_desde_bd(con):
    """Lee las tres tablas y regresa la matriz como diccionarios.

    Regresa (transiciones, categorias, nombre_de_simbolo):
      transiciones[estado][nombre_simbolo] = estado_destino
      categorias[estado]                   = categoría del token o None
      nombre_de_simbolo[id]                = carácter de la columna
    """
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


def inicializar(con=None):
    """Carga la matriz desde la base. Se llama una sola vez al iniciar la aplicación.

    Si no se pasa una conexión, abre una y la cierra al terminar.
    Regresa el número de estados cargados.
    """
    global MATRIZ_TRANS, MATRIZ_CAT, NUM_ESTADOS, NUM_SIMBOLOS
    propia = con is None
    con = con or conectar()
    MATRIZ_TRANS, MATRIZ_CAT, simbolos = cargar_desde_bd(con)
    NUM_ESTADOS = len(MATRIZ_TRANS)
    NUM_SIMBOLOS = len(simbolos)
    if propia:
        con.close()
    return NUM_ESTADOS


#  2. RECORRIDO
def columna(c):
    """Nombre de la columna de la matriz para un carácter.

    El espacio se guarda en la base con el nombre 'ESP'. Cualquier carácter
    que no esté en el alfabeto (por ejemplo una minúscula) no tiene columna.
    """
    return "ESP" if c == " " else c


def paso(estado, c):
    """Un solo paso del autómata: estado actual + carácter -> estado siguiente."""
    destino = MATRIZ_TRANS[estado].get(columna(c))
    return destino if destino else ERROR


def mayor_lexema(linea, i):
    """Lexema más largo que empieza en la posición i (maximal munch).

    Avanza mientras haya transición. Cada vez que el estado tiene categoría,
    guarda la posición. Al final regresa (fin, categoría) o None si no hay ninguna.
    """
    estado, mejor = INICIAL, None
    for pos in range(i, len(linea)):
        estado = paso(estado, linea[pos])
        if estado == ERROR:
            break
        if MATRIZ_CAT.get(estado):
            mejor = (pos + 1, MATRIZ_CAT[estado])
    return mejor


#  3. ERRORES
def sugerir(fragmento):
    """Regresa una sugerencia breve para el fragmento que no es válido."""
    if fragmento.isalpha() and fragmento.islower():
        return f"El lenguaje solo acepta mayúsculas: escriba '{fragmento.upper()}' en lugar de '{fragmento}'."
    c = fragmento[0]
    if c.isdigit():
        return "Número mal formado. Ejemplos válidos: 10, 3.14, 2.5E3."
    if c in "&|":
        return f"Use AND / OR en lugar de '{c}'."
    if c == "!":
        return "'!' solo es válido dentro de '!=' ."
    if c == "'":
        return 'Para cadenas use comillas dobles ( " ).'
    if c == '"':
        return 'Cadena sin cerrar: agregue la comilla doble de cierre.'
    return "Símbolo o texto fuera del alfabeto de OLLIN: elimínelo o reemplácelo."


def analizar(texto):
    """Separa el programa en tokens, errores y tabla de símbolos.

    Regresa un diccionario con las claves:
        tokens, errores, simbolos, tabulacion
    """
    tokens, errores = [], []
    for num, linea in enumerate(texto.splitlines() or [""], 1):
        i = 0
        while i < len(linea):
            if linea[i] in (" ", "\t"):          # separadores: no forman token
                i += 1
                continue
            m = mayor_lexema(linea, i)
            if m is None:                        # ningún lexema válido: error
                # Agrupa los caracteres seguidos que no forman token (ej. 'var' = un error)
                j = i + 1
                while j < len(linea) and linea[j] not in (" ", "\t") and mayor_lexema(linea, j) is None:
                    j += 1
                fragmento = linea[i:j]
                errores.append(ErrorLexico(num, i + 1, fragmento, linea, sugerir(fragmento)))
                i = j
                continue
            fin, categoria = m
            if categoria != "COMENTARIO":        # los comentarios no son tokens
                tokens.append(Token(num, i + 1, linea[i:fin], categoria))
            i = fin

    return {
        "tokens": tokens,
        "errores": errores,
        "simbolos": construir_tabla(tokens, errores),
        "tabulacion": revisar_sangrias(texto),
    }


#  4. TABLA DE SÍMBOLOS
def construir_tabla(tokens, errores=()):
    """Tabla de símbolos: un registro por identificador distinto.

    Campos: numero, nombre, tipo, valor, linea (primera aparición).
    - tipo:  se toma de la declaración 'VAR <TIPO> nombre'. Si no hay, 'sin declarar'.
    - valor: se toma de la última asignación 'nombre = constante' en la misma línea,
             sin errores léxicos entre ellos. Si no hay, vacío.
    """
    lineas_con_error = {(e.linea, e.columna) for e in errores}  # posiciones de error
    tabla, indice = [], {}
    # Primera pasada: crear un registro por identificador, en orden de aparición
    for t in tokens:
        if t.categoria == "IDENTIFICADOR" and t.lexema not in indice:
            indice[t.lexema] = len(tabla)
            tabla.append({"numero": len(tabla) + 1, "nombre": t.lexema,
                          "tipo": "sin declarar", "valor": "", "linea": t.linea})

    # Segunda pasada: completar tipo y valor mirando los tokens vecinos
    for k, t in enumerate(tokens):
        if t.categoria != "IDENTIFICADOR":
            continue
        registro = tabla[indice[t.lexema]]
        if k >= 2 and tokens[k - 2].categoria == "PR_VAR" and tokens[k - 1].categoria in TIPOS_DATO:
            registro["tipo"] = TIPOS_DATO[tokens[k - 1].categoria]
        if (k + 2 < len(tokens) and tokens[k + 1].categoria == "ASIGNACION"
                and tokens[k + 2].categoria in ("CN", "CADENA")
                and tokens[k + 1].linea == t.linea and tokens[k + 2].linea == t.linea
                and not _hay_error_entre(t, tokens[k + 1], lineas_con_error)):
            registro["valor"] = tokens[k + 2].lexema
    return tabla


def _hay_error_entre(a, b, posiciones_error):
    """True si hay un error léxico en la misma línea entre los tokens a y b."""
    return any(linea == a.linea and a.columna < col < b.columna
               for linea, col in posiciones_error)


def buscar(tabla, texto, modo="exacta"):
    """Búsqueda secuencial (lineal) en la tabla de símbolos.

    Recorre la tabla registro por registro y compara el nombre:
      modo 'exacta': el nombre es igual al texto buscado.
      modo 'prefijo': el nombre empieza con el texto buscado.
    Regresa la lista de registros encontrados.
    """
    if modo == "prefijo":
        return [s for s in tabla if s["nombre"].startswith(texto)]
    return [s for s in tabla if s["nombre"] == texto]


#  5. TABULACIÓN
def revisar_sangrias(texto):
    """Revisa la sangría (espacios al inicio de cada línea).

    Regla: la sangría debe ser múltiplo de 5 espacios y no debe llevar tabuladores.
    Regresa una lista de advertencias en texto.
    """
    avisos = []
    for num, linea in enumerate(texto.splitlines(), 1):
        sangria = re.match(r"[ \t]*", linea).group(0)
        if not sangria:
            continue
        if "\t" in sangria:
            avisos.append(f"línea {num}: contiene tabulador. Use espacios, en múltiplos de {SANGRIA_MULTIPLO}.")
        elif len(sangria) % SANGRIA_MULTIPLO:
            sugerido = -(-len(sangria) // SANGRIA_MULTIPLO) * SANGRIA_MULTIPLO
            avisos.append(f"línea {num}: sangría de {len(sangria)} espacios. "
                          f"Debe ser múltiplo de {SANGRIA_MULTIPLO} (sugerido: {sugerido}).")
    return avisos


#  6. DIAGRAMA UML
UML_MERMAID = """classDiagram
    class Ventana {
        +abrir()
        +analizar()
        +guardar_resultado()
        +guardar_uml()
        +buscar_simbolo()
    }
    class Analizador {
        +inicializar()
        +analizar(texto)
        +reporte(texto)
    }
    class MatrizTransicion {
        +cargar_desde_bd(con)
        +paso(estado, c)
        +mayor_lexema(linea, i)
    }
    class TablaSimbolos {
        +construir_tabla(tokens)
        +buscar(tabla, texto, modo)
    }
    class Token {
        linea
        columna
        lexema
        categoria
    }
    class ErrorLexico {
        linea
        columna
        fragmento
        sugerencia
    }
    Ventana --> Analizador
    Analizador --> MatrizTransicion
    Analizador --> TablaSimbolos
    Analizador --> Token
    Analizador --> ErrorLexico
"""

UML_SECUENCIA = """sequenceDiagram
    participant U as Usuario
    participant V as Ventana
    participant A as Analizador
    participant BD as SQL Server
    U->>V: Escribe o carga el programa
    U->>V: Presiona Analizar
    V->>A: reporte(texto)
    Note over A,BD: Al iniciar, una sola vez
    A->>BD: SELECT estados, simbolos, transiciones
    BD-->>A: matriz de transición
    loop cada línea y cada lexema
        A->>A: mayor_lexema (paso por la matriz)
    end
    A-->>V: tokens, errores, tabulación, tabla de símbolos
    V-->>U: muestra el resultado
"""


def diagrama_uml():
    """Texto del diagrama UML en Mermaid (se pega en mermaid.live para verlo)."""
    return UML_MERMAID + "\n" + UML_SECUENCIA


#  7. REPORTE
def _linea_con_marca(texto_linea, columna, fragmento):
    """Muestra la línea y una marca ^ bajo todo el fragmento con error."""
    return f"      | {texto_linea}\n      | {' ' * (columna - 1)}{'^' * len(fragmento)}"


def reporte(texto):
    """Arma el texto completo del resultado que se muestra en la ventana."""
    if MATRIZ_TRANS is None:
        inicializar()
    r = analizar(texto)
    out = [f"{NOMBRE}  v{VERSION}",
           f"Autores: {AUTORES}",
           f"Matriz: {NUM_ESTADOS} estados, {NUM_SIMBOLOS} símbolos (base {BASE})",
           ""]

    out.append(f"ARCHIVO DE TOKENS ({len(r['tokens'])})")
    for t in r["tokens"]:
        out.append(f"  línea {t.linea:>3}, col {t.columna:>3}: {t.categoria:<26} {t.lexema}")

    out.append(f"\nERRORES LÉXICOS ({len(r['errores'])})")
    for e in r["errores"]:
        out.append(f"  línea {e.linea}, columna {e.columna}: texto no válido '{e.fragmento}'")
        out.append(_linea_con_marca(e.texto, e.columna, e.fragmento))
        out.append(f"      Solución rápida: {e.sugerencia}")
    if not r["errores"]:
        out.append("  Sin errores léxicos.")

    out.append(f"\nADVERTENCIAS DE TABULACIÓN ({len(r['tabulacion'])})")
    out += [f"  {a}" for a in r["tabulacion"]] or ["  Sin advertencias."]

    out.append(f"\nTABLA DE SÍMBOLOS ({len(r['simbolos'])})")
    out.append(f"  {'Nº':>3}  {'NOMBRE':<20} {'TIPO DE DATO':<14} {'VALOR':<12} LÍNEA")
    for s in r["simbolos"]:
        out.append(f"  {s['numero']:>3}  {s['nombre']:<20} {s['tipo']:<14} {s['valor']:<12} {s['linea']}")

    out.append("\nDIAGRAMA UML DEL ANÁLISIS (Mermaid)")
    out.append(diagrama_uml())
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    inicializar()
    if len(sys.argv) > 1:
        print(reporte(open(sys.argv[1], encoding="utf-8").read()))
    else:
        import ventana
        ventana.abrir()