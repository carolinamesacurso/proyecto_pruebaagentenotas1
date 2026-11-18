import asyncio
import os

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
#Variables de configuración del servidor mcp al que nos vamos a conectar y temáticas permitidas preestablecidas
MCP_URL = "http://127.0.0.1:8000/mcp"
TEMATICAS = ["cocina", "lectura", "deportes"]
#Cargamos de antemano la api key de gemini que se necesiatará en el caso de indicar que el proveedor se llama "gemini"
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

#Creamos un método donde devolvemsos el modelo de lenguaje que va a utilizar el agente 
#En este se recibe el proveedor y el nombre del modelo
#De esta forma se puede cambiar de modelo sin tener que repetir código o modificar una estructura estática
def obtener_llm(proveedor: str, modelo: str):

    if proveedor.lower() == "ollama":

        return ChatOllama(
            model=modelo,
            temperature=0,
            base_url="http://localhost:11434"
        )

    elif proveedor.lower() == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError("No se ha encontrado GEMINI_API_KEY en el archivo .env")
    
        return ChatGoogleGenerativeAI(
            model=modelo,
            temperature=0,
            google_api_key=GEMINI_API_KEY
        )

    else:
        raise ValueError(f"Proveedor no soportado: {proveedor}")

    
async def ainput(prompt: str) -> str:
    # Permite que el loop de asyncio siga corriendo mientras el usuario escribe
    return await asyncio.to_thread(input, prompt)

#En este ejericio solo vamos a crear un agente esto debido a que :
    #1 . Todas las herramientas a trabajar tiene la misma temática que es trabajar con notas , no necesitamos que un nodo se especialize en una tarea en concreto 
        #ya que el propio prompt puede interpretar la temática de los archivos debido al contenido y que se le indican las temáticas preestablecidas
    #2 . No necesitan seguir un orden o un recorrido establecido , es decir , el usuario puede empezar la conversación quieriendo listar unas notas en vez de crear
    #3 . Si creamos nodos dividiendo las responsabilidades , tendríamso que añadir una estructura adicional para dirigir peticiones a cada operación
        #Mientrás que al tener un nodo y el servidor mcp disponemos de una estructura clara ya que uno de encarga de las operaciones y otro de interpretar al usuario
    #4 . Trabajamos con un system_prompt desarrollado para que siga unos pasos y un orden en concreto
async def main():

    #para ollama
    # llm = obtener_llm(
    #     proveedor="ollama",
    #     modelo="llama3.1:8b"
    # )

    #para gemini
    llm = obtener_llm(
    proveedor="gemini",
    modelo="gemini-3.5-flash-lite"
    )

    # Conexión con el servidor MCP por HTTP.
    async with streamable_http_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Cargar TODAS las herramientas directamente desde MCP.
            mcp_tools = await load_mcp_tools(session)
            print("Tools disponibles:", ", ".join(t.name for t in mcp_tools))

            memory = MemorySaver()
            #Definimos el prompt del sistema que contiene los pasos a seguir durante cada acción pedida por el ususario
            #Declaramos que tiene que preguntar si faltan parámetros necesarios , como interpretar los resultados si son correctos o no , cuando llamar a las funciones 
            #FUNCIONES : 
                #En el caso de que el usuario quiera clasificar la carpeta de recepción desarrollamos unos pasos específicos, 
                #esto debido a que al decidir la temática de cada nota necesitamos pasar en un diccionario las diferentes notas y los futuros destinos al método moover_archivos
                #En el resto de los casos indicamos parámetros necesarios , como llamar a las funciones y como interpertar el resultado
                #Resumen de las funciones : listar por temática , crear nota , subir/copiar nota y clasificar notas
            system_prompt = f"""
   Eres un asistente que usa herramientas MCP para ayudar al usuario. Responde en español.

            Estos serán los pasos a seguir para cada función:

            Cuando el usuario quiera crear una nota:
            - Pregunta al usuario el nombre de la nota si no lo ha proporcionado.
            - Pregunta al usuario el contenido de la nota si no lo ha proporcionado.
            - Utiliza a la herramienta crear_nota SOLO cuando tengas el nombre y contenido de la nota.
            - Cuando tengas el nombre y contenido de la nota, llama a la herramienta crear_nota con los parámetros nombre_nota y contenido_nota que has obtenido anteriormente.
            - No afirmes que la nota se ha creado si la herramienta no ha realizado la operación correctamente.
            - Interpreta el resultado de la herramienta antes de responder.
            - Si el resultado contiene el texto "Nota Creada exitosamente en la carpeta Recepción.", considera que la creación ha sido correcta.
            
            Cuando el usuario quiera listar las notas por temática:
            - Pregunta al usuario la temática de las notas si no lo ha proporcionado.
            - Si no lo ha indicado , pregúntale qué temática quiere listar
            - No inventes ni supongas una temática
            - Cuando tengas la temática de las notas, llama a la herramienta listar_notas_tematicas con el parámetro temática que has obtenido anteriormente.
            - Utiliza el resultado devuelto por la herramienta para comunicar al ususario la lista de notas encontradas en esa temática.
            - Si la herramienta devuelve un error , comunícaselo al usuario.

            Cuando el usuario quiera almacenar o subir una nota desde la carpeta de descargas a la carpeta de recepción:
            - Pregunta al usuario el nombre de la nota si no lo ha proporcionado.
            - No inventes ni supongas un nombre de nota
            - Cuando tengas el nombre de la nota, llama a la herramienta Copiar_nota con el parámetro nombre_nota que has obtenido anteriormente.
            - No afirmes que la nota se ha copiado si la herramienta no ha realizado la operación correctamente.
            - Interpreta el resultado de la herramienta antes de responder.
            - Si el resultado contiene el texto "Archivo copiado a la carpeta de recepción", considera que la copia ha sido correcta.
            - Si la herramienta devuelve un error , comunícaselo al usuario.

            CLASIFICAR Y MOVER TODAS LAS NOTAS DE RECEPCIÓN

            Cuando el usuario solicite clasificar u organizar todas las notas de Recepción,
            sigue obligatoriamente este procedimiento:

            1. Llama UNA SOLA VEZ a la herramienta MCP obtener_notas_recepcion.
            Esta herramienta devuelve un diccionario cuyas claves son los nombres
            de los archivos y cuyos valores son sus contenidos.

            2. No pidas al usuario los nombres de los archivos. Debes procesar todos
            los archivos .txt que devuelve la herramienta.

            3. Si el resultado contiene la clave "error", comunica el error.
            Si el diccionario está vacío, informa de que Recepción no contiene notas.

            4. Lee y analiza el contenido de cada nota. Decide una única temática
            para cada archivo, utilizando exclusivamente estas opciones:
            cocina, lectura o deportes.
            Clasifica por el contenido, nunca solamente por el nombre del archivo. 
        
            5. Mantén las correspondencias exactas entre cada nombre de archivo
            y la temática que has decidido. Prepara un único diccionario con
            esta estructura:
            {{
                "nota1.txt": "cocina",
                "nota2.txt": "deportes",
                "nota3.txt": "lectura"
            }}

            6. Si una nota no encaja razonablemente en ninguna temática, no la incluyas
            en el diccionario que vas a mover. Recuerda su nombre para informar
            de que queda pendiente.

            7. Cuando hayas terminado de clasificar todas las notas, llama UNA SOLA VEZ
            a la herramienta MCP mover_archivos y pásale el diccionario completo
            mediante el argumento clasificaciones.

            8. Examina el resultado devuelto por mover_archivos. Comunica qué archivos
            se han movido y cuáles no. No afirmes que un archivo se movió si el
            resultado indica un error.

            9. Termina con un resumen de las clasificaciones, los movimientos y
                las notas que hayan quedado pendientes.

            REGLAS IMPORTANTES:
            - No crees herramientas ni funciones propias.
            - Utiliza exclusivamente las herramientas proporcionadas por MCP.
            - Para clasificar y organizar, utiliza obtener_notas_recepcion y mover_archivos.
            - La llamada a mover_archivos debe contener todas las notas clasificadas,
            no una llamada por archivo.
            - No inventes nombres, contenidos, temáticas ni resultados.
            - El objetivo es procesar todos los archivos de Recepción.
"""

          #Creamos el agente con create_agent():
            # le pasamos la configuración completa del llm , las tools del servidor previamente arrancado, el sistema encargado del estado de las conversaciones y el prompt creado con anterioridad
            app = create_agent(
                llm,
                tools=mcp_tools,
                checkpointer=memory,
                system_prompt=system_prompt
            )
        #Definimos hilo de la conversación para checkpointer 
            config = {"configurable": {"thread_id": "mcp_user_1"}}

            # Bucle de conversación.
            while True:
                #Recogemos en una variable la petición del usuario
                pregunta = await ainput("Pregunta>>> ")
                #Opción para finalizar la conversación
                if pregunta.lower() in ["salir", "exit", "quit"]:
                    print("Chat terminado")
                    break

                print(f"--- Consulta: {pregunta} ---")
                inputs = {"messages": [("user", pregunta)]}

                # Ejecutamos el agente para trabajar de forma asíncrona
                async for s in app.astream(inputs, config=config, stream_mode="values"):


                    message = s["messages"][-1]
                    # if hasattr(message, "tool_calls") and message.tool_calls:
                    #     print(f"   [MCP: Llamando a {message.tool_calls[0]['name']}...]")

                    #Visualizamos por consola que herramientas está decidiendo ejecutar el agente y que parámetros está proporcionando al mcp
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for llamada in message.tool_calls:
                            print(f"   [MCP: Llamando a {llamada['name']}]")
                            print(f"   Argumentos enviados: {llamada['args']}")
                # Visualizamos resultado final de mcp , es decir , mostramos el mensaje de tipo tool
                for msg in s["messages"]:
                    if msg.type == "tool":
                        print(f"\n[RESULTADO MCP]: {msg.content}")
                # Respuesta final interpretada por el agente , el cual mostrará de la manera indicada según las indicaciones establecidas en el prompt del sistema
                print(f"\nRESPUESTA FINAL:\n{message.content}")



if __name__ == "__main__":
    asyncio.run(main())
