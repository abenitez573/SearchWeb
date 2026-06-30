import os
import json
import asyncio
import threading
import websockets
from http.server import HTTPServer, BaseHTTPRequestHandler
from server import mcp

MCP_ENDPOINT = os.getenv("MCP_ENDPOINT")
PORT = int(os.environ.get("PORT", 8000))

# Servidor HTTP para health check
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    print(f"🩺 Servidor health check en puerto {PORT}")
    server.serve_forever()

# Cliente MCP
async def main():
    if not MCP_ENDPOINT:
        print("❌ Error: MCP_ENDPOINT no configurado")
        return

    print(f"🔄 Conectando a {MCP_ENDPOINT}...")

    try:
        async with websockets.connect(MCP_ENDPOINT) as websocket:
            print("✅ Conectado al MCP Access Point de Xiaozhi")

            # Mensaje de conexión en el formato esperado por Xiaozhi
            await websocket.send(json.dumps({
                "method": "connect",
                "params": {
                    "type": "mcp",
                    "client_info": {
                        "name": "xiaozhi-mcp-gateway",
                        "version": "1.0.0"
                    }
                }
            }))
            print("📤 Mensaje de conexión enviado.")

            # Bucle para recibir mensajes
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"📥 Recibido: {data}")

                    if data.get("method") == "tool_call":
                        tool_name = data.get("params", {}).get("name")
                        args = data.get("params", {}).get("arguments", {})

                        if tool_name == "google_search":
                            result = await mcp.tools["google_search"](**args)
                        elif tool_name == "get_current_time":
                            result = await mcp.tools["get_current_time"](**args)
                        else:
                            result = f"Herramienta desconocida: {tool_name}"

                        # Responder con el resultado
                        await websocket.send(json.dumps({
                            "jsonrpc": "2.0",
                            "id": data.get("id"),
                            "result": result
                        }))
                        print("📤 Resultado enviado.")

                except Exception as e:
                    print(f"❌ Error procesando mensaje: {e}")

    except Exception as e:
        print(f"❌ Error en conexión WebSocket: {e}")

if __name__ == "__main__":
    http_thread = threading.Thread(target=run_health_server, daemon=True)
    http_thread.start()
    asyncio.run(main())
