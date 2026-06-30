import os
import json
import asyncio
import websockets
from server import mcp

MCP_ENDPOINT = os.getenv("MCP_ENDPOINT")

async def main():
    if not MCP_ENDPOINT:
        print("❌ Error: MCP_ENDPOINT no configurado en variables de entorno")
        return

    print(f"🔄 Conectando a {MCP_ENDPOINT}...")

    try:
        async with websockets.connect(
            MCP_ENDPOINT,
            extra_headers={"User-Agent": "xiaozhi-mcp-gateway/1.0"}
        ) as websocket:
            print("✅ WebSocket conectado. Esperando mensajes...")

            # Enviar mensaje de "connect" con el formato esperado
            connect_msg = {
                "type": "connect",
                "name": "xiaozhi-mcp-gateway",
                "capabilities": {
                    "tools": [
                        {"name": "google_search", "description": "Busca en Google"},
                        {"name": "get_current_time", "description": "Obtiene la hora actual"}
                    ]
                }
            }
            await websocket.send(json.dumps(connect_msg))
            print("📤 Mensaje de conexión enviado.")

            # Escuchar mensajes
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"📥 Recibido: {data}")

                    if data.get("type") == "tool_call":
                        tool_name = data.get("name")
                        args = data.get("arguments", {})
                        print(f"🔧 Llamando a herramienta: {tool_name} con args: {args}")

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
                        print("📤 Resultado enviado.")
                except Exception as e:
                    print(f"❌ Error al procesar mensaje: {e}")

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Error de conexión (código HTTP {e.status_code}): {e}")
    except websockets.exceptions.InvalidHandshake as e:
        print(f"❌ Error de handshake: {e}")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    asyncio.run(main())
