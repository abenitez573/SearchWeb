import os
import json
import asyncio
import websockets
from server import mcp

MCP_ENDPOINT = os.getenv("MCP_ENDPOINT")

async def main():
    if not MCP_ENDPOINT:
        print("❌ Error: MCP_ENDPOINT no configurado")
        return

    print(f"🔄 Conectando a {MCP_ENDPOINT}...")

    try:
        # Asegurar que usamos wss:// si no está
        if MCP_ENDPOINT.startswith("ws://"):
            print("⚠️ Usando ws://, se recomienda wss://")
        async with websockets.connect(MCP_ENDPOINT) as websocket:
            print("✅ Conectado al MCP Access Point de Xiaozhi")
            
            # Mensaje de identificación
            await websocket.send(json.dumps({
                "type": "connect",
                "name": "xiaozhi-mcp-gateway",
                "capabilities": {
                    "tools": [
                        {"name": "google_search", "description": "Busca en Google"},
                        {"name": "get_current_time", "description": "Obtiene la hora actual"}
                    ]
                }
            }))
            print("📤 Mensaje de conexión enviado.")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"📥 Recibido: {data}")
                    if data.get("type") == "tool_call":
                        tool_name = data.get("name")
                        args = data.get("arguments", {})
                        if tool_name == "google_search":
                            result = await mcp.tools["google_search"](**args)
                        elif tool_name == "get_current_time":
                            result = await mcp.tools["get_current_time"](**args)
                        else:
                            result = f"Herramienta desconocida: {tool_name}"
                        await websocket.send(json.dumps({
                            "type": "tool_result",
                            "result": result
                        }))
                except Exception as e:
                    print(f"❌ Error procesando mensaje: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(main())
