from mcp.server.fastmcp import FastMCP
import os
import shutil

HOST = "127.0.0.1"
PORT = 8000

NOTES_DIR = "/home/pabilion/notasPruebas/misnotas"
RECEPCION_DIR = "/home/pabilion/notasPruebas/recepcion"
DESCARGAS_DIR = "/home/pabilion/notasPruebas/descargas"

TEMATICAS = ["cocina", "lectura", "deportes"]

os.makedirs(NOTES_DIR, exist_ok=True)
os.makedirs(RECEPCION_DIR, exist_ok=True)
os.makedirs(DESCARGAS_DIR, exist_ok=True)

mcp = FastMCP("Gestor de Notas", host=HOST, port=PORT)
# En el código anterior establecemos configuraciones el propio servidor mcp 
    #Puerto y host donde va a lanzarse 
    #Rutas de las carpetas principales y métodos ejecutados para crear estas si no existen cuando se ejecuta el servidor
    #Temáticas a trabajar


#Validamos nombres de las notas para que al clasificar varias notas de una carpeta entera no incluya las carpetas o añada un ".txt" a la ruta de los archivos 
#Se crea esta función debido a que no estamos tratando con una nota individualmente en una sola petición como lo hacemos al crear o copiar nota 
#Utilizamos esta función para tratar en el futuro varias notas en un bucle y limpiar la estructura de donde se utilice
def validar_nombre_nota(nombre_nota: str) -> str:
    """Comprueba que el nombre sea un nombre de archivo y no una ruta."""
    if not nombre_nota or os.path.basename(nombre_nota) != nombre_nota:
        raise ValueError("Nombre de archivo no válido.")

    if not nombre_nota.endswith(".txt"):
        nombre_nota += ".txt"

    return nombre_nota

#Permite listar los nombres de los archivos según la temática 
#En el docstring indicamos que funcionamiento tiene que tener esta función en específico y contexto sobre las ubicaciones las rutas
    #nombre_tema será el parámetro obligatorio que necesitamos para realizar esta tool , el cual nos indicará la temática que quere listar el usuario
    #Indicamos que antes de llamar a esta herramienta se necesita veroficar que el usuario nos ha proporcionado una temática
    #Le comentamos que no puede inventar nombre de archivos que no estén en la propia temática
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

    #Comprobaciones para controlar que quiera listar temáticas inexistentes o que dirpath esté bien construido
    if os.path.commonpath([base, dirpath]) != base:
            return "Error: Acceso denegado fuera del directorio de notas."
    
    if not os.path.isdir(dirpath):
            return f"Error: La carpeta de la temática no existe. Temáticas existentes {TEMATICAS}"
    # Devolvemos los nombre de los archivos separados por saltos de línea (\n) y si no hay archivos devolvemos un mensaje 
    try:
        files = sorted(os.listdir(dirpath))
        return "\n".join(files) if files else "No hay notas aún en esa temática."
    except Exception as e:
        return f"Error al listar notas: {str(e)}"

#Creamos una nota con el nombre y el contenido que nos ha proporcionado el usuario
#En el docstring indicamos cuales son los parámetros adecuados que nos tiene que proporcionar y como debe interpretar el resultado
    #Al poder intentar crear una nota existente o sin alguno de los parámetros obligatorios le mostramos que antes de llamar a esta herramienta tiene que comprobar que tenemos datos suficientes
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


    if not os.path.isdir(base):
            return "Error: La carpeta no existe."
    
    try:
        #crear ruta y comprobaciones de esta
        ruta_completa = os.path.join(base, f"{nombre_nota}.txt")
        
        if os.path.commonpath([base, ruta_completa]) != base:
                return "Error: Acceso denegado a archivos fuera del directorio de notas."

        # Comprobar si el archivo ya existe
        if os.path.exists(ruta_completa):
            return "Error: Ya existe una nota con ese nombre."
        #Crear la nota con f.write en la ruta previamente establecida con el contenido indicado
        with open(ruta_completa, "w", encoding="utf-8") as f:
            f.write(contenido_nota)

        return "Nota Creada exitosamente en la carpeta Recepción."
    except Exception as e:
        return f"Error al crear la nota: {str(e)}"
    
#Copiar/subir una nota de la carpeta de descargas a la de recepción
#En el docstring indicamos que necesitamos el nombre de la nota para poder saber cual subimos
#No se puede llamar a esta herramienta si no tenemos el nombre de la nota que queremos copiar
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
        #leemos la nota en su ruta de origen y guardamos el contenido en una variable 
        with open(archivo_origen, "r", encoding="utf-8") as f:
            contenido = f.read()
        #creamos la nueva nota
        with open(ruta_completa_destino, "w", encoding="utf-8") as f:
            f.write(contenido)

        return "Archivo copiado a la carpeta de recepción"
    except Exception as e:
        return f"Error copiando el archivo: {str(e)}"

#Estas dos últimas funcionalidades están creadas para depender una de la otra ya que el agente 
# primero llamará a obtener_notas_recepción y le enviará a mover_archivos las respuestas del contenido analizado de la primera función

#En esta función entregamos al agente los nombres y los contenidos de los archivos de la carpeta de recepción
#Generando un diccionario con la siguiente estructura notas={nombre:contenido}
@mcp.tool()
def obtener_notas_recepcion() -> dict[str, str]:
    """
    Devuelve todas las notas de recepción en forma de diccionario.
    La clave es el nombre de la nota y el valor es su contenido.
    """
    notas = {}

    if not os.path.isdir(RECEPCION_DIR):
        return {"error": "La carpeta de recepción no existe."}
    #Recorremos todos los elementos que hya dentro de la carpeta recepción
    for nombre_nota in os.listdir(RECEPCION_DIR):
        #construimos la ruta completa
        ruta = os.path.join(RECEPCION_DIR, nombre_nota)

        if not nombre_nota.endswith(".txt") or not os.path.isfile(ruta):
            continue
        #Por cada valor de nombre_nota añadimos al diccionario un registro más 
        #leemos el archivo y guardamos este como valor de su clave(nombre de su nota)
        try:
            with open(ruta, "r", encoding="utf-8") as archivo:
                notas[nombre_nota] = archivo.read()
        except Exception as e:
            return {"error": f"No se pudo leer {nombre_nota}: {e}"}

    return notas


#Una vez el agente haya clasificado todos los archivos en sus temáticas correspodientes , llama a esta tool para realizar el movimiento 
#Mueve todos los archivos a sus carpetas destino 
#En este apartado realizamos como resultado un filtro donde guardamos en dos diccionarios diferentes los archivos que se han movido y los que no 
#Debido a que queremos mantener un seguimiento de cuales han tenido un progreso correcto
#Si la temática no es válida , no existe el archivo en la carpeta, ya existe en la carpeta de destino o el nombre no es válido se procederá a guardar en no_correctos y seguir con el resto de comprobaciones e interacciones
#Se guardará en no_correctos el nombre de la nota y su causa
@mcp.tool()
def mover_archivos(clasificaciones: dict[str, str]) -> dict:
    """
    Recibe un diccionario con todas las notas y sus destinos , mueve cada nota de recepción a su carpeta temática.
     Parámetros:
        - clasificaciones
    Ejemplo:
    {
        "notaprueba1.txt": "cocina",
        "notaprueba2.txt": "deportes",
        "notaprueba3.txt": "lectura",
        "notaprueba4.txt": "deportes"
    }
    """
    correctos = {}
    no_correctos = {}
    #recorremos todas los elementos nota:destino del diccionario clasificaciones
    for nombre, tema in clasificaciones.items():
        # Comprobamos que la temática analizada por el propio agente es una de las validas. Pasamos al siguiente archivo si no es el caso
        if tema not in TEMATICAS:
            no_correctos[nombre] = (f"Temática no permitida: {tema}")
            continue
        
        if not nombre.endswith(".txt"):
                nombre += ".txt"

        # Construimos las diferentes rutas
        origen = os.path.join(RECEPCION_DIR, nombre)
        carpeta_destino = os.path.join(NOTES_DIR, tema)
        destino = os.path.join(carpeta_destino, nombre)

        #Comprobamos que las notas que ha analizado el agente existen en la carpeta o ha pasado un nombre incorrecto
        if not os.path.isfile(origen):
            no_correctos[nombre] = ("El archivo no existe en la carpeta de recepción.")
            continue
        try:
            os.makedirs(carpeta_destino, exist_ok=True)
            #Comprobamos si ya existe un archivo con ese nombre en la carpeta de destino
            if os.path.exists(destino):
                no_correctos[nombre] = ("Nota ya existente en la carpeta de la temática.")
                continue
            #Utilizamos shutil.move para mover los archivos de la carpeta de recepcion a la carpeta de destino y guardamos estos para luego que el agente interprete el resultado
            shutil.move(origen, destino)
            correctos[nombre] = tema

        except Exception as e:
            no_correctos[nombre] = str(e)

    return {
        "archivos_movidos": correctos,
        "archivos_no_movidos": no_correctos
    }

if __name__ == "__main__":
    # Streamable HTTP: el endpoint queda en http://HOST:PORT/mcp
    print(f"Servidor MCP escuchando en http://{HOST}:{PORT}/mcp")
    mcp.run(transport="streamable-http")

#USO DE IA 
#Consultar correcciones sobre comprobaciones necesarias para la tool mover_archivos como validar_nombre_nota
#Buscar documentación sobre guardar errores de comprobaciones
#Buscar documentación sobre el uso de shutil para mover los archivos
#Buscar documentación sobre como mejorar el system_prompt para poder pasar sin errores el diccionario de clasificaciones