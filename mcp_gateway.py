import os
import json
import asyncio
import threading
import websockets
from http.server import HTTPServer, BaseHTTPRequestHandler
from server import mcp
import signal

MCP_ENDPOINT = os.getenv("MCP_ENDPOINT")
PORT = int(os.environ.get("PORT", 8000))

# ============================================
# Servidor HTTP para health check
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
# Cliente MCP para Xiaozhi (formato correcto)
# ============================================
async def main():
    if not MCP_ENDPOINT:
        print("❌ Error: MCP_ENDPOINT no configurado")
        return

    print(f"🔄 Conectando a {MCP_ENDPOINT}...")

    try:
        async with websockets.connect(MCP_ENDPOINT) as websocket:
            print("✅ WebSocket conectado")

            # 1. Enviar mensaje de conexión (formato que Xiaozhi espera)
            await websocket.send(json.dumps({
                "type": "connect",
                "version": "1.0.0",
                "client_info": {
                    "name": "xiaozhi-mcp-gateway"
                }
            }))
            print("📤 Conexión solicitada")

            # Bucle principal
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"📥 Mensaje: {data}")

                    # Manejar la inicialización del servidor (JSON-RPC)
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
                        print("📤 Respuesta de inicialización enviada")

                    # Manejar llamadas a herramientas
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
        print(f"❌ Error de conexión: {e}")

# ============================================
# Punto de entrada
# ============================================
if __name__ == "__main__":
    # Iniciar health check en hilo separado
    http_thread = threading.Thread(target=run_health_server, daemon=True)
    http_thread.start()

    # Ejecutar cliente WebSocket
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Servidor detenido")
