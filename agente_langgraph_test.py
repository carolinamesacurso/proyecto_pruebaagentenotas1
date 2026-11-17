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


# --------------------------------------------------
# CONFIGURACIÓN
# --------------------------------------------------

MCP_URL = "http://127.0.0.1:8000/mcp"
TEMATICAS = ["cocina", "lectura", "deportes"]

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def obtener_llm(proveedor: str, modelo: str):
    """Crea el modelo indicado: Ollama o Gemini."""

    if proveedor.lower() == "ollama":
        return ChatOllama(
            model=modelo,
            temperature=0,
            base_url="http://localhost:11434"
        )

    elif proveedor.lower() == "gemini":
        if not GEMINI_API_KEY:
            raise ValueError(
                "No se ha encontrado GEMINI_API_KEY en el archivo .env"
            )

        return ChatGoogleGenerativeAI(
            model=modelo,
            temperature=0,
            google_api_key=GEMINI_API_KEY
        )

    else:
        raise ValueError(f"Proveedor no soportado: {proveedor}")


async def ainput(prompt: str) -> str:
    """Permite escribir sin bloquear el bucle de asyncio."""
    return await asyncio.to_thread(input, prompt)


# --------------------------------------------------
# AGENTE LANGGRAPH
# --------------------------------------------------

async def main():

    # Seleccionar el proveedor y el modelo.
    llm = obtener_llm(
        proveedor="gemini",
        modelo="gemini-3.5-flash-lite"
    )

    # Para utilizar Ollama, sustituye la configuración anterior:
    #
    # llm = obtener_llm(
    #     proveedor="ollama",
    #     modelo="llama3.1:8b"
    # )

    # Conexión con el servidor MCP por HTTP.
    async with streamable_http_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Cargar TODAS las herramientas directamente desde MCP.
            mcp_tools = await load_mcp_tools(session)

            nombres_tools = {herramienta.name for herramienta in mcp_tools}

            print("Tools MCP disponibles:", ", ".join(sorted(nombres_tools)))

            # Comprobar que el servidor ofrece las herramientas necesarias.
            necesarias = {
                "obtener_notas_recepcion",
                "mover_archivos"
            }

            faltan = necesarias - nombres_tools

            if faltan:
                raise RuntimeError(
                    "Faltan herramientas en el servidor MCP: "
                    + ", ".join(sorted(faltan))
                )

            memory = MemorySaver()

            system_prompt = f"""
Eres un asistente gestor de notas. Responde siempre en español.

Las temáticas permitidas son: {TEMATICAS}.

INSTRUCCIONES GENERALES

Cuando el usuario quiera crear una nota:
- Pregunta por el nombre si no lo ha proporcionado.
- Pregunta por el contenido si no lo ha proporcionado.
- Cuando tengas ambos datos, utiliza la herramienta MCP crear_nota.
- Comunica el resultado real de la herramienta.

Cuando el usuario quiera listar notas por temática:
- Pregunta qué temática quiere consultar si no la ha indicado.
- Utiliza la herramienta MCP listar_notas_tematicas.
- Comunica el resultado.

Cuando el usuario quiera copiar una nota concreta de Descargas a Recepción:
- Pregunta por el nombre si no lo ha indicado.
- Utiliza la herramienta MCP Copiar_nota.
- Comunica el resultado real.

Cuando el usuario quiera leer una nota:
- Pregunta por el nombre si no lo ha indicado.
- Utiliza la herramienta MCP leer_nota.
- Comunica el contenido devuelto.

Cuando el usuario quiera listar todas las notas de Recepción:
- Utiliza la herramienta MCP listar_notas_recepcion.
- Comunica los nombres devueltos.

Cuando el usuario quiera pasar TODOS los archivos de Descargas a Recepción:
- Utiliza la herramienta MCP mover_todos_a_recepcion.
- Comunica qué archivos se movieron y cuáles no.

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

            # IMPORTANTE: el agente recibe exclusivamente herramientas MCP.
            # No se añaden herramientas locales con @tool.
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

                if pregunta.lower().strip() in ["salir", "exit", "quit"]:
                    print("Chat terminado")
                    break

                print(f"--- Consulta: {pregunta} ---")

                inputs = {"messages": [("user", pregunta)]}
                estado_final = None

                async for estado in app.astream(
                    inputs,
                    config=config,
                    stream_mode="values"
                ):
                    estado_final = estado
                    mensaje = estado["messages"][-1]

                    # Mostrar las llamadas a herramientas MCP.
                    if getattr(mensaje, "tool_calls", None):
                        for llamada in mensaje.tool_calls:
                            print(f"\n[MCP: {llamada['name']}]")
                            print(f"Argumentos enviados: {llamada['args']}")

                if estado_final is not None:
                    # Mostrar resultados de las herramientas de esta consulta.
                    for mensaje in estado_final["messages"]:
                        if getattr(mensaje, "type", None) == "tool":
                            print(f"\n[RESULTADO MCP]: {mensaje.content}")

                    mensaje_final = estado_final["messages"][-1]
                    print(f"\nRESPUESTA FINAL:\n{mensaje_final.content}")


if __name__ == "__main__":
    asyncio.run(main())
