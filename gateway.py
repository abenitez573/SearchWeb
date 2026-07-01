import os
import json
import asyncio
import websockets
from http.server import HTTPServer, BaseHTTPRequestHandler
from server import mcp

MCP_ENDPOINT = os.getenv("MCP_ENDPOINT")
PORT = int(os.environ.get("PORT", 10000))

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    print(f"🩺 Servidor de salud en puerto {PORT}")
    server.serve_forever()

async def connect_to_xiaozhi():
    if not MCP_ENDPOINT:
        print("❌ MCP_ENDPOINT no configurado")
        return

    try:
        async with websockets.connect(MCP_ENDPOINT, ping_interval=20, ping_timeout=60) as websocket:
            print("✅ Conectado a Xiaozhi")
            async for message in websocket:
                # ... (el resto del código de manejo de mensajes)
                pass
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Iniciar el servidor HTTP en un hilo separado
    import threading
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Conectar a Xiaozhi
    asyncio.run(connect_to_xiaozhi())
