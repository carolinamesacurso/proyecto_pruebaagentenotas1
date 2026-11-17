from mcp.server.fastmcp import FastMCP
import os
import shutil

# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

HOST = "127.0.0.1"
PORT = 8000

NOTES_DIR = "/home/carolinamesamartine/notasPruebas/misnotas"
RECEPCION_DIR = "/home/carolinamesamartine/notasPruebas/recepcion"
DESCARGAS_DIR = "/home/carolinamesamartine/notasPruebas/descargas"

TEMATICAS = ["cocina", "lectura", "deportes"]

os.makedirs(NOTES_DIR, exist_ok=True)
os.makedirs(RECEPCION_DIR, exist_ok=True)
os.makedirs(DESCARGAS_DIR, exist_ok=True)

mcp = FastMCP("Gestor de Notas", host=HOST, port=PORT)


def validar_nombre_nota(nombre_nota: str) -> str:
    """Comprueba que el nombre sea un nombre de archivo y no una ruta."""
    if not nombre_nota or os.path.basename(nombre_nota) != nombre_nota:
        raise ValueError("Nombre de archivo no válido.")

    if not nombre_nota.endswith(".txt"):
        nombre_nota += ".txt"

    return nombre_nota


# --------------------------------------------------
# HERRAMIENTAS MCP GENERALES
# --------------------------------------------------

@mcp.tool()
def listar_notas_tematicas(nombre_tema: str) -> list[str] | str:
    """Lista las notas que hay dentro de una temática."""
    if nombre_tema not in TEMATICAS:
        return f"Error: La temática '{nombre_tema}' no está permitida."

    carpeta = os.path.join(NOTES_DIR, nombre_tema)

    if not os.path.isdir(carpeta):
        return f"No existe todavía la carpeta de la temática {nombre_tema}."

    return [
        nombre
        for nombre in os.listdir(carpeta)
        if os.path.isfile(os.path.join(carpeta, nombre))
    ]


@mcp.tool()
def crear_nota(nombre_nota: str, contenido_nota: str) -> str:
    """Crea una nota de texto en la carpeta de recepción."""
    try:
        nombre_nota = validar_nombre_nota(nombre_nota)
        destino = os.path.join(RECEPCION_DIR, nombre_nota)

        if os.path.exists(destino):
            return "Error: Ya existe una nota con ese nombre en Recepción."

        with open(destino, "w", encoding="utf-8") as archivo:
            archivo.write(contenido_nota)

        return "Nota Creada exitosamente en la carpeta Recepción."

    except Exception as e:
        return f"Error al crear la nota: {e}"


@mcp.tool()
def Copiar_nota(nombre_nota: str) -> str:
    """Copia una nota concreta desde Descargas a Recepción."""
    try:
        nombre_nota = validar_nombre_nota(nombre_nota)
        origen = os.path.join(DESCARGAS_DIR, nombre_nota)
        destino = os.path.join(RECEPCION_DIR, nombre_nota)

        if not os.path.isfile(origen):
            return "Error: La nota no existe en la carpeta de descargas."

        if os.path.exists(destino):
            return "Error: Ya existe una nota con ese nombre en Recepción."

        shutil.copy2(origen, destino)
        return "Archivo copiado a la carpeta de recepción."

    except Exception as e:
        return f"Error al copiar el archivo: {e}"


@mcp.tool()
def mover_todos_a_recepcion() -> dict:
    """
    Mueve todos los archivos que hay directamente en Descargas a Recepción.
    No mueve carpetas ni sobrescribe archivos existentes.
    """
    movidos = []
    no_movidos = {}

    for nombre in os.listdir(DESCARGAS_DIR):
        origen = os.path.join(DESCARGAS_DIR, nombre)

        if not os.path.isfile(origen):
            continue

        destino = os.path.join(RECEPCION_DIR, nombre)

        if os.path.exists(destino):
            no_movidos[nombre] = "Ya existe un archivo con ese nombre en Recepción."
            continue

        try:
            shutil.move(origen, destino)
            movidos.append(nombre)
        except Exception as e:
            no_movidos[nombre] = str(e)

    return {
        "archivos_movidos": movidos,
        "archivos_no_movidos": no_movidos
    }


@mcp.tool()
def leer_nota(nombre_nota: str) -> str:
    """Lee el contenido de una nota de Recepción."""
    try:
        nombre_nota = validar_nombre_nota(nombre_nota)
        ruta = os.path.join(RECEPCION_DIR, nombre_nota)

        if not os.path.isfile(ruta):
            return "Error: La nota no existe en la carpeta de recepción."

        with open(ruta, "r", encoding="utf-8") as archivo:
            return archivo.read()

    except Exception as e:
        return f"Error al leer la nota: {e}"


@mcp.tool()
def listar_notas_recepcion() -> list[str]:
    """Lista todos los archivos que hay en Recepción."""
    return [
        nombre
        for nombre in os.listdir(RECEPCION_DIR)
        if os.path.isfile(os.path.join(RECEPCION_DIR, nombre))
    ]


# --------------------------------------------------
# HERRAMIENTAS MCP PARA CLASIFICAR Y ORGANIZAR
# --------------------------------------------------

@mcp.tool()
def obtener_notas_recepcion() -> dict[str, str]:
    """
    Devuelve todas las notas .txt de Recepción.
    La clave es el nombre del archivo y el valor es su contenido.
    """
    notas = {}

    if not os.path.isdir(RECEPCION_DIR):
        return {"error": "La carpeta de recepción no existe."}

    for nombre_nota in os.listdir(RECEPCION_DIR):
        ruta = os.path.join(RECEPCION_DIR, nombre_nota)

        if not nombre_nota.endswith(".txt") or not os.path.isfile(ruta):
            continue

        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                notas[nombre_nota] = archivo.read()
        except Exception as e:
            return {"error": f"No se pudo leer {nombre_nota}: {e}"}

    return notas


@mcp.tool()
def mover_archivos(clasificaciones: dict[str, str]) -> dict:
    """
    Recibe todas las clasificaciones en un único diccionario y mueve
    cada nota de Recepción a su carpeta temática correspondiente.

    Ejemplo:
    {
        "nota1.txt": "cocina",
        "nota2.txt": "deportes"
    }
    """
    movidos = {}
    no_movidos = {}

    for nombre_nota, tema in clasificaciones.items():

        # Validar temática.
        if tema not in TEMATICAS:
            no_movidos[nombre_nota] = (
                f"Temática no permitida: {tema}"
            )
            continue

        # Validar nombre y existencia del archivo.
        try:
            nombre_nota = validar_nombre_nota(nombre_nota)
        except ValueError as e:
            no_movidos[str(nombre_nota)] = str(e)
            continue

        origen = os.path.join(RECEPCION_DIR, nombre_nota)
        carpeta_destino = os.path.join(NOTES_DIR, tema)
        destino = os.path.join(carpeta_destino, nombre_nota)

        if not os.path.isfile(origen):
            no_movidos[nombre_nota] = (
                "El archivo no existe en la carpeta de recepción."
            )
            continue

        try:
            os.makedirs(carpeta_destino, exist_ok=True)

            if os.path.exists(destino):
                no_movidos[nombre_nota] = (
                    "Ya existe una nota con ese nombre en la temática."
                )
                continue

            shutil.move(origen, destino)
            movidos[nombre_nota] = tema

        except Exception as e:
            no_movidos[nombre_nota] = str(e)

    return {
        "archivos_movidos": movidos,
        "archivos_no_movidos": no_movidos
    }


# --------------------------------------------------
# ARRANQUE DEL SERVIDOR
# --------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
