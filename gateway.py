import os
import json
import asyncio
import threading
import websockets
from http.server import HTTPServer, BaseHTTPRequestHandler
from server import mcp

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
                    # 1. Manejar "initialize"
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
                    # 2. Manejar "tools/list"
                    # ============================================
                    if data.get("method") == "tools/list":
                        response = {
                            "jsonrpc": "2.0",
                            "id": data.get("id"),
                            "result": {
                                "tools": [
                                    {
                                        "name": "web_search",
                                        "description": "Busca información en internet",
                                        "inputSchema": {
                                            "type": "object",
                                            "properties": {
                                                "query": {"type": "string", "description": "Consulta de búsqueda"},
                                                "num_results": {"type": "integer", "description": "Número de resultados", "default": 5}
                                            },
                                            "required": ["query"]
                                        }
                                    },
                                    {
                                        "name": "get_current_time",
                                        "description": "Devuelve la hora y fecha actual",
                                        "inputSchema": {"type": "object", "properties": {}}
                                    }
                                ]
                            }
                        }
                        await websocket.send(json.dumps(response))
                        print("📤 Lista de herramientas enviada")
                        continue
                    
                    # ============================================
                    # 3. Manejar "tools/call"
                    # ============================================
                    if data.get("method") == "tools/call":
                        params = data.get("params", {})
                        tool_name = params.get("name")
                        args = params.get("arguments", {})
                        print(f"🔧 Llamando a: {tool_name} con args: {args}")
                        
                        if tool_name == "web_search":
                            result = mcp.tools["web_search"](**args)
                        elif tool_name == "get_current_time":
                            result = mcp.tools["get_current_time"]()
                        else:
                            result = f"Herramienta desconocida: {tool_name}"
                        
                        await websocket.send(json.dumps({
                            "jsonrpc": "2.0",
                            "id": data.get("id"),
                            "result": {
                                "content": [{"type": "text", "text": str(result)}]
                            }
                        }))
                        print("📤 Resultado enviado")
                        continue
                    
                    # ============================================
                    # 4. Manejar "ping"
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
