import os
import json
import asyncio
import threading
import websockets
from http.server import HTTPServer, BaseHTTPRequestHandler

MCP_ENDPOINT = os.getenv("MCP_ENDPOINT")
PORT = int(os.environ.get("PORT", 10000))

# ============================================
# Servidor HTTP para health check (Render)
# ============================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    print(f"🩺 Health check en puerto {PORT}")
    server.serve_forever()

# ============================================
# Cliente WebSocket (conexión a Xiaozhi)
# ============================================
async def connect_to_xiaozhi():
    if not MCP_ENDPOINT:
        print("❌ MCP_ENDPOINT no configurado")
        return

    try:
        async with websockets.connect(MCP_ENDPOINT) as websocket:
            print("✅ Conectado a Xiaozhi")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"📥 {message}")
                    
                    # ============================================
                    # Manejar "initialize" (OBLIGATORIO)
                    # ============================================
                    if data.get("method") == "initialize":
                        response = {
                            "jsonrpc": "2.0",
                            "id": data.get("id"),
                            "result": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {"tools": {}},
                                "serverInfo": {"name": "gateway", "version": "1.0"}
                            }
                        }
                        await websocket.send(json.dumps(response))
                        print("📤 Inicialización respondida")
                        continue
                    
                    # ============================================
                    # Manejar "ping"
                    # ============================================
                    if data.get("method") == "ping":
                        await websocket.send(json.dumps({
                            "jsonrpc": "2.0",
                            "id": data.get("id"),
                            "result": {}
                        }))
                        print("📤 Pong")
                        continue
                        
                except json.JSONDecodeError:
                    print(f"⚠️ Mensaje no JSON: {message}")
                except Exception as e:
                    print(f"❌ Error procesando mensaje: {e}")
                    
    except Exception as e:
        print(f"❌ Error en WebSocket: {e}")

# ============================================
# Punto de entrada
# ============================================
if __name__ == "__main__":
    # Iniciar servidor HTTP en un hilo separado
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Conectar a Xiaozhi (bloquea el hilo principal)
    asyncio.run(connect_to_xiaozhi())
