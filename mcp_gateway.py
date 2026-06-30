import os
import json
import asyncio
import websockets
from server import mcp # Importa tu servidor MCP

MCP_ENDPOINT = os.getenv("MCP_ENDPOINT") # Esta variable la pondremos en Render

async def main():
    if not MCP_ENDPOINT:
        print("Error: MCP_ENDPOINT no configurado en variables de entorno")
        return

    print(f"Conectando a {MCP_ENDPOINT}...")
    
    try:
        async with websockets.connect(MCP_ENDPOINT) as websocket:
            print("✅ Conectado al MCP Access Point de Xiaozhi")
            
            # Envía un mensaje de identificación
            await websocket.send(json.dumps({
                "type": "connect",
                "name": "xiaozhi-mcp-server",
                "capabilities": {
                    "tools": [
                        "google_search",
                        "get_current_time"
                    ]
                }
            }))
            
            # Escucha y procesa mensajes
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"📥 Recibido: {data}")
                    
                    if data.get("type") == "tool_call":
                        tool_name = data.get("tool")
                        args = data.get("arguments", {})
                        
                        # Ejecuta la herramienta correspondiente
                        if tool_name == "google_search":
                            result = await mcp.tools["google_search"](**args)
                        elif tool_name == "get_current_time":
                            result = await mcp.tools["get_current_time"](**args)
                        else:
                            result = f"Herramienta {tool_name} no encontrada"
                        
                        # Envía la respuesta
                        await websocket.send(json.dumps({
                            "type": "tool_result",
                            "result": result
                        }))
                        
                except Exception as e:
                    print(f"❌ Error procesando mensaje: {e}")
                    
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    asyncio.run(main())
