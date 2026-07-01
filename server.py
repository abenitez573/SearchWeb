import os
import requests
from fastmcp import FastMCP
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Crear la instancia del servidor
mcp = FastMCP("xiaozhi-mcp-server")

# Obtener la clave de Serper.dev desde variables de entorno
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# ============================================
# HERRAMIENTA 1: Búsqueda en internet (Serper.dev)
# ============================================
@mcp.tool()
def web_search(query: str, num_results: int = 5) -> str:
    """
    Busca información en Google usando Serper.dev y devuelve los resultados.

    Args:
        query: La consulta de búsqueda (ej. "resultados fútbol 2026")
        num_results: Número de resultados a devolver (máximo 10)

    Returns:
        Lista de resultados con título, descripción y enlace
    """
    if not SERPER_API_KEY:
        return "Error: SERPER_API_KEY no está configurada en las variables de entorno"

    # Limitar el número de resultados a 10 (máximo permitido por Serper)
    num_results = min(num_results, 10)

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q": query,
        "num": num_results
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Lanza excepción si hay error HTTP
        data = response.json()

        # Extraer los resultados orgánicos
        organic_results = data.get("organic", [])
        if not organic_results:
            return f"No se encontraron resultados para: {query}"

        output = f"🔍 Resultados para: {query}\n\n"
        for i, item in enumerate(organic_results[:num_results], 1):
            title = item.get("title", "Sin título")
            snippet = item.get("snippet", "Sin descripción")
            link = item.get("link", "")
            output += f"{i}. **{title}**\n"
            output += f"   {snippet}\n"
            output += f"   🔗 {link}\n\n"
        return output

    except requests.exceptions.RequestException as e:
        return f"Error al realizar la búsqueda (problema de red): {str(e)}"
    except Exception as e:
        return f"Error al realizar la búsqueda: {str(e)}"


# ============================================
# PUNTO DE ENTRADA (OBLIGATORIO)
# ============================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Iniciando servidor MCP en el puerto {port}")
    print("📦 Herramientas disponibles: web_search, get_current_time")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
