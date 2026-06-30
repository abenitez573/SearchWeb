import os
import json
import asyncio
import threading
import websockets
import signal
from http.server import HTTPServer, BaseHTTPRequestHandler
from server import mcp

MCP_ENDPOINT = os.getenv("MCP_ENDPOINT")
PORT = int(os.environ.get("PORT", 8000))

# ============================================
# Servidor HTTP para health check (Render)
# ============================================
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
    print(f"🩺 Health check en puerto {PORT}")
    server.serve_forever()

# ============================================
# Cliente MCP para Xiaozhi (con reconexión)
# ============================================
async def connect_to_xiaozhi():
    if not MCP_ENDPOINT:
        print("❌ Error: MCP_ENDPOINT no configurado")
        return

    while True:
        try:
            print(f"🔄 Conectando a {MCP_ENDPOINT}...")
            async with websockets.connect(
                MCP_ENDPOINT,
                ping_interval=20,
                ping_timeout=60
            ) as websocket:
                print("✅ WebSocket conectado")

                # Enviar mensaje de conexión
                await websocket.send(json.dumps({
                    "type": "connect",
                    "name": "xiaozhi-mcp-gateway",
                    "capabilities": {
                        "google_search": {
                            "description": "Busca en Google"
                        },
                        "get_current_time": {
                            "description": "Obtiene la hora actual"
                        }
                    }
                }))
                print("📤 Conexión solicitada")

                # Bucle principal
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        print(f"📥 Mensaje: {data}")

                        # Manejar "initialize" (lo que pide Xiaozhi)
                        if data.get("method") == "initialize":
                            await websocket.send(json.dumps({
                                "jsonrpc": "2.0",
                                "id": data.get("id"),
                                "result": {
                                    "protocolVersion": "2024-11-05",
                                    "capabilities": {
                                        "tools": {}
                                    },
                                    "serverInfo": {
                                        "name": "xiaozhi-mcp-gateway",
                                        "version": "1.0.0"
                                    }
                                }
                            }))
                            print("📤 Inicialización respondida")

                        # Manejar "tools/call"
                        elif data.get("method") == "tools/call":
                            params = data.get("params", {})
                            tool_name = params.get("name")
                            args = params.get("arguments", {})

                            if tool_name == "google_search":
                                result = await mcp.tools["google_search"](**args)
                            elif tool_name == "get_current_time":
                                result = await mcp.tools["get_current_time"](**args)
                            else:
                                result = f"Herramienta desconocida: {tool_name}"

                            await websocket.send(json.dumps({
                                "jsonrpc": "2.0",
                                "id": data.get("id"),
                                "result": {
                                    "content": [{
                                        "type": "text",
                                        "text": result
                                    }]
                                }
                            }))
                            print("📤 Resultado enviado")

                    except Exception as e:
                        print(f"❌ Error en mensaje: {e}")

        except Exception as e:
            print(f"❌ Conexión perdida: {e}")
            print("🔄 Reconectando en 5 segundos...")
            await asyncio.sleep(5)

# ============================================
# Punto de entrada
# ============================================
if __name__ == "__main__":
    # Iniciar health check
    http_thread = threading.Thread(target=run_health_server, daemon=True)
    http_thread.start()

    # Ejecutar cliente WebSocket con reconexión
    try:
        asyncio.run(connect_to_xiaozhi())
    except KeyboardInterrupt:
        print("🛑 Servidor detenido")
