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

@mcp.tool()
def listar_notas_tematicas(nombre_tema: str) -> str:
    """
    Lista todos los nombres de los archivos de notas que se encuentran dentro de la carpeta nombrada igual que la temática dada por el usuario 
    La carpeta de cada temática se encuentra dentro de la carpeta misNotas y debe coincidir con el nombre de la temática.
    
    Parámetros:
    - nombre_tema: nombre de la temática de las notas a listar (debe coincidir con el nombre de la carpeta que contiene las notas de esa temática)

    IMPORTANTE:
    - Antes de llamar a esta herramienta, asegúrate de que la temática ha sido proporcionada por el usuario.
    - No inventes nombres de archivos ni afirmes que el listado de notas se ha obtenido si la herramienta no ha realizado la operación correctamente.
    """
    base = os.path.realpath(NOTES_DIR)

    # if nombre_tema not in TEMÁTICAS:
    #         return "Error: La temática no es válida. "

    dirpath = os.path.realpath(os.path.join(base, nombre_tema))

    if os.path.commonpath([base, dirpath]) != base:
            return "Error: Acceso denegado fuera del directorio de notas."
    
    if not os.path.isdir(dirpath):
            return f"Error: La carpeta de la temática no existe. Temáticas existentes {TEMATICAS}"
    
    try:
        files = sorted(os.listdir(dirpath))
        return "\n".join(files) if files else "No hay notas aún en esa temática."
    except Exception as e:
        return f"Error al listar notas: {str(e)}"
    
@mcp.tool()
def crear_nota(nombre_nota: str,contenido_nota: str) -> str:
    """Crea una nota como un archivo .txt para guardarlo en la carpeta de recepción .
    Parámetros 
    - nombre_nota: nombre de la nota a crear (sin extensión .txt)
    - contenido_nota: contenido de la nota a crear

    Interpretación del resultado:
    Si devuelve "Nota Creada exitosamente en la carpeta Recepción.", significa que el archivo se ha creado correctamente.
    Si devuelve un mensaje que comienza por "Error:", significa que la operación no se ha completado correctamente.

    IMPORTANTE:
    - Antes de llamar a esta herramienta, asegúrate de que el nombre y contenido de la nota han sido proporcionados por el usuario.
    - No afirmes que la nota se ha creado si la herramienta no ha realizado la operación correctamente.
    
    """
    base = os.path.realpath(RECEPCION_DIR)

#   # Añadir .txt solamente si no está presente
#         if not nombre_nota.endswith(".txt"):
#             nombre_nota += ".txt"


    if not os.path.isdir(base):
            return "Error: La carpeta no existe."
    
    try:
        ruta_completa = os.path.join(base, f"{nombre_nota}.txt")
        
        if os.path.commonpath([base, ruta_completa]) != base:
                return "Error: Acceso denegado a archivos fuera del directorio de notas."

        # Comprobar si el archivo ya existe
        if os.path.exists(ruta_completa):
            return "Error: Ya existe una nota con ese nombre."
        
        with open(ruta_completa, "w", encoding="utf-8") as f:
            f.write(contenido_nota)

        return "Nota Creada exitosamente en la carpeta Recepción."
    except Exception as e:
        return f"Error al crear la nota: {str(e)}"

@mcp.tool()
def Copiar_nota(nombre_nota: str) -> str:
    """Copia un archivo indicado por el usuario de la carpeta local de descargas a la carpeta local de recepcion.
    
    Parámetros:
    - nombre_nota: nombre del archivo a copiar

    Interpretación del resultado:
    Si devuelve "Archivo copiado a la carpeta de recepción.", significa que el archivo se ha copiado correctamente.
    Si devuelve un mensaje que comienza por "Error:", significa que la operación no se ha completado correctamente
    
    IMPORTANTE:
    - Antes de llamar a esta herramienta, asegúrate de que el nombre del archivo ha sido proporcionado por el usuario.
    - No afirmes que la nota se ha copiado si la herramienta no ha realizado la operación correctamente.
    - Interpreta el resultado de la herramienta antes de responder.
    - Si el resultado contiene el texto "Archivo copiado a la carpeta de recepción", considera que la copia ha sido correcta.

    """
    base = os.path.realpath(DESCARGAS_DIR)
    destino = os.path.realpath(RECEPCION_DIR)


    if not nombre_nota.endswith(".txt"):
        nombre_nota += ".txt"

    archivo_origen = os.path.realpath(os.path.join(base, nombre_nota))

    # Comprobar que el archivo está dentro de la carpeta de notas
    if os.path.commonpath([base, archivo_origen]) != base:
        return "Error: Acceso denegado a archivos fuera del directorio de notas."

    if not os.path.isfile(archivo_origen):
        return f"Error: La nota no existe.{archivo_origen}"
    
    try:
        ruta_completa_destino = os.path.join(destino, f"{nombre_nota}")

        with open(archivo_origen, "r", encoding="utf-8") as f:
            contenido = f.read()
        
        with open(ruta_completa_destino, "w", encoding="utf-8") as f:
            f.write(contenido)

        return "Archivo copiado a la carpeta de recepción"
    except Exception as e:
        return f"Error copiando el archivo: {str(e)}"

    
   

@mcp.tool()
def leer_nota(nombre_nota: str) -> str:
    """."""
    """
    Lee el contenido de una nota específica en la carpeta de recepción
    La nota se encuentra dentro de la carpeta recepcion dentro de misnotas y debe coincidir con el nombre del archivo.
    
    Parámetros:
    - nombre_nota: nombre de la nota 

    IMPORTANTE:
    - Antes de llamar a esta herramienta, asegúrate de que el nombre ha sido proporcionada por el usuario.
    - No inventes nombres de notas ni afirmes que la nota se ha leído si la herramienta no ha realizado la operación correctamente.
    """
    base = os.path.realpath(RECEPCION_DIR)

    if not nombre_nota.endswith(".txt"):
            nombre_nota += ".txt"

    filepath = os.path.realpath(os.path.join(base, nombre_nota))

    # Comprobar que el archivo está dentro de la carpeta de notas
    if os.path.commonpath([base, filepath]) != base:
        return "Error: Acceso denegado a archivos fuera del directorio de notas."

    if not os.path.isfile(filepath):
        return "Error: La nota no existe."

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error leyendo el archivo: {str(e)}"

@mcp.tool()
def listar_notas_recepcion() -> str:
    """
    Lista todos los nombres de los archivos de notas que se encuentran SOLO dentro de la carpeta recepcion    

    IMPORTANTE:
    - Solo lista los nombres de los archivos en esa carpeta
    - No inventes nombres de archivos ni afirmes que el listado de notas se ha obtenido si la herramienta no ha realizado la operación correctamente.
    """
    base = os.path.realpath(RECEPCION_DIR)
    
    if not os.path.isdir(base):
            return f"Error: La carpeta recepción no existe."
    
    try:
        files = sorted(os.listdir(base))
        return "\n".join(files) if files else "No hay notas aún en esa carpeta."
    except Exception as e:
        return f"Error al listar notas: {str(e)}"



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
