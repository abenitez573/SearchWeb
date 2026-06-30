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
def google_search(query: str, num_results: int = 5) -> str:
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
