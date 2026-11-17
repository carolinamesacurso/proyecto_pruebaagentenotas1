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

MCP_URL = "http://127.0.0.1:8000/mcp"
TEMATICAS = ["cocina", "lectura", "deportes"]

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


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



async def main():

    # Configurar el LLM
    # llm = ChatOllama(
    #     # model='llama3.1:8b-instruct-q4_K_M',
    #     model='llama3.1:8b',
    #     temperature=0,
    #     base_url="http://localhost:11434"
    #     # base_url="http://10.42.68.45:11434"
    #     # base_url="http://127.0.0.1:11434",
    # )

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

            # nombres_tools = {herramienta.name for herramienta in mcp_tools}

            # print("Tools MCP disponibles:", ", ".join(sorted(nombres_tools)))

            # # Comprobar que el servidor ofrece las herramientas necesarias.
            # necesarias = {
            #     "obtener_notas_recepcion",
            #     "mover_archivos"
            # }

            # faltan = necesarias - nombres_tools

            # if faltan:
            #     raise RuntimeError(
            #         "Faltan herramientas en el servidor MCP: "
            #         + ", ".join(sorted(faltan))
            #     )

            memory = MemorySaver()

            system_prompt = f"""
   Eres un asistente que usa herramientas MCP para ayudar al usuario. Responde en español.

            Tus funciones principales van a ser crear una nota , copiar una nota de la carpeta de descargas a la carpeta de recepción y leer el contenido de una nota específica.  
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

            Cuando el usuario quiera leer una nota:
             - Pregunta al usuario el nombre de la nota si no lo ha proporcionado.
             - No inventes ni supongas un nombre de nota
             - Cuando tengas el nombre de la nota, llama a la herramienta leer_nota con el parámetro nombre_nota que has obtenido anteriormente.
             - Utiliza el resultado devuelto por la herramienta para comunicar al usuario el contenido de la nota.
             - Si la herramienta devuelve un error , comunícaselo al usuario.
            
            Cuando el usuario quiera listar todas las notas de la carpeta de recepción:
            - Llama a la herramienta listar_notas_recepcion.
            - Utiliza el resultado devuelto por la herramienta para comunicar al ususario la lista de notas encontradas en esa carpeta.
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

            8. No llames a mover_archivo: esa herramienta no forma parte del proceso.
            La única herramienta para mover las notas clasificadas es mover_archivos.

            9. Examina el resultado devuelto por mover_archivos. Comunica qué archivos
            se han movido y cuáles no. No afirmes que un archivo se movió si el
            resultado indica un error.

            10. Termina con un resumen de las clasificaciones, los movimientos y
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

          
            app = create_agent(
                llm,
                tools=mcp_tools,
                checkpointer=memory,
                system_prompt=system_prompt
            )

            config = {"configurable": {"thread_id": "mcp_user_1"}}

            # Bucle de conversación.
            while True:
                pregunta = await ainput("Pregunta>>> ")

                if pregunta.lower() in ["salir", "exit", "quit"]:
                    print("Chat terminado")
                    break

                print(f"--- Consulta: {pregunta} ---")
                inputs = {"messages": [("user", pregunta)]}

                async for s in app.astream(inputs, config=config, stream_mode="values"):


                    ##prueba temporal 
                    # print("\n--- HISTORIAL DE MENSAJES ---")

                    # for msg in s["messages"]:
                    #     print(f"\nTipo: {msg.type}")
                    #     print(f"Contenido: {msg.content}")

                    #     if hasattr(msg, "tool_calls") and msg.tool_calls:
                    #         print(f"Llamadas: {msg.tool_calls}")

                    # print("--- FIN DEL HISTORIAL ---")




                    message = s["messages"][-1]
                    # if hasattr(message, "tool_calls") and message.tool_calls:
                    #     print(f"   [MCP: Llamando a {message.tool_calls[0]['name']}...]")
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for llamada in message.tool_calls:
                            print(f"   [MCP: Llamando a {llamada['name']}]")
                            print(f"   Argumentos enviados: {llamada['args']}")
                
                for msg in s["messages"]:
                    if msg.type == "tool":
                        print(f"\n[RESULTADO MCP]: {msg.content}")

                print(f"\nRESPUESTA FINAL:\n{message.content}")



if __name__ == "__main__":
    asyncio.run(main())
