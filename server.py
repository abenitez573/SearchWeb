import os
import json
from fastmcp import FastMCP
from googleapiclient.discovery import build
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Crear la instancia del servidor
mcp = FastMCP("xiaozhi-mcp-server")

# Obtener claves de Google desde variables de entorno
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID") # ⬅️ Este es el ID del motor de búsqueda (cx)

# ============================================
# HERRAMIENTA 1: Búsqueda en Google (CORREGIDA)
# ============================================
@mcp.tool()
def google_search(query: str, num_results: int = 5) -> str:
    """
    Busca información en Google y devuelve los resultados.

    Args:
        query: La consulta de búsqueda (ej. "resultados fútbol 2026")
        num_results: Número de resultados a devolver (máximo 10)

    Returns:
        Lista de resultados con título, descripción y enlace
    """
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return "Error: Las claves de Google no están configuradas"

    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        result = service.cse().list(
            q=query,
            cx=GOOGLE_CSE_ID,
            num=min(num_results, 10)
        ).execute()

        if 'items' not in result:
            return f"No se encontraron resultados para: {query}"

        output = f"🔍 Resultados para: {query}\n\n"
        for i, item in enumerate(result['items'], 1):
            output += f"{i}. **{item.get('title', 'Sin título')}**\n"
            output += f" {item.get('snippet', 'Sin descripción')}\n"
            output += f" 🔗 {item.get('link', '')}\n\n"
        return output

    except Exception as e:
        return f"Error al realizar la búsqueda: {str(e)}"

# ============================================
# HERRAMIENTA 2: Hora actual (OPCIONAL, pero útil)
# ============================================
@mcp.tool()
def get_current_time() -> str:
    """Devuelve la fecha y hora actual en formato legible."""
    from datetime import datetime
    now = datetime.now()
    return now.strftime("%A, %d de %B de %Y, %H:%M:%S")

# ============================================
# PUNTO DE ENTRADA (OBLIGATORIO)
# ============================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Iniciando servidor MCP en el puerto {port}")
    print("📦 Herramientas disponibles: google_search, get_current_time")
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
