import os
import json
from fastmcp import FastMCP
from googleapiclient.discovery import build
from dotenv import load_dotenv


#Cargar variables de entorno
load_dotenv()


#crear la instancia del servidor 
mcp= FastMCP("xiaozhi-mcp-server")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

@mcp.tool()

def google_search(query:str,num_results:int = 5) -> str:
    """
    Busca informacion  en Google y devuelve los resultados.

    Args:
        query:La consulta de busqueda (ej. "resultados futbol 2026")
        num_results: Numero de resultados a devolver (maximo 10)

    Returns:
        Lista de resultados con titulos, descripcion y enlace
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return "Error: Las claves de Google no estan configuradas"

    try:
        service = build("customsearch","v1",developer=GOOGLE_API_KEY)

        result = service.cse().list(
                q=query,
                cx=GOOGLE_CSE_ID,
                num=min(num_results,10)
        ).execute()

        if 'items' not in result:
            return f"No se encontraron resultados para: {query}"

            output = f"Error al realizar la busqueda: {str(e)}"

        @mcp.tool()
        def get_current_time() -> str:
            """Devuelve la fecha y hora actual en formato legible."""
            from datetime import datetime 
            now = datetime.now()
            return now.strftime("%A, %d de %B de %Y, %H:%M:%S")

        if __name__ == "__main__":
            port = int(os.environ.get("PORT",8000))
            print(f" iniciando servidor MCP en el puerto {port}")
            print("herramienta disponibles: google_search,get_current_time")
            mcp.run(transport="streamable-http",host="0.0.0.0",port=port)