import os
import json
import asyncio
import threading
import sys
import websockets
from http.server import HTTPServer, BaseHTTPRequestHandler
from server import mcp

MCP_ENDPOINT = os.getenv("MCP_ENDPOINT")
PORT = int(os.environ.get("PORT", 10000))

# Forzar flush de print
def log(msg):
    print(msg, flush=True)
    sys.stdout.flush()

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
    log(f"🩺 Health check en puerto {PORT}")
    server.serve_forever()

# ============================================
# Cliente WebSocket (conexión a Xiaozhi)
# ============================================
async def connect_to_xiaozhi():
    if not MCP_ENDPOINT:
        log("❌ MCP_ENDPOINT no configurado")
        return

    while True:  # Bucle de reconexión
        try:
            log("🔄 Conectando a Xiaozhi...")
            async with websockets.connect(MCP_ENDPOINT) as websocket:
                log("✅ Conectado a Xiaozhi")
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        log(f"📥 Recibido: {message}")
                        
                        # ============================================
                        # Manejar "initialize"
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
                            log("📤 Inicialización respondida")
                            continue
                        
                        # ============================================
                        # Manejar "tools/list"
                        # ============================================
                        if data.get("method") == "tools/list":
                            tools_list = []
                            for tool_name, tool_func in mcp.tools.items():
                                tools_list.append({
                                    "name": tool_name,
                                    "description": tool_func.__doc__ or f"Herramienta {tool_name}",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {"type": "string", "description": "Consulta de búsqueda"},
                                            "num_results": {"type": "integer", "description": "Número de resultados", "default": 5}
                                        },
                                        "required": ["query"]
                                    }
                                })
                            
                            response = {
                                "jsonrpc": "2.0",
                                "id": data.get("id"),
                                "result": {"tools": tools_list}
                            }
                            await websocket.send(json.dumps(response))
                            log(f"📤 Lista de herramientas enviada: {tools_list}")
                            continue
                        
                        # ============================================
                        # Manejar "tools/call" (¡AQUÍ ESTÁ LA CLAVE!)
                        # ============================================
                        if data.get("method") == "tools/call":
                            params = data.get("params", {})
                            tool_name = params.get("name")
                            args = params.get("arguments", {})
                            
                            log(f"🔧 Llamando a: {tool_name} con args: {args}")
                            
                            try:
                                # Ejecutar la herramienta
                                if tool_name == "web_search":
                                    result = mcp.tools["web_search"](**args)
                                else:
                                    result = f"Herramienta desconocida: {tool_name}"
                                
                                log(f"📤 Resultado obtenido: {str(result)[:100]}...")
                                
                                # Enviar respuesta en el formato esperado
                                response = {
                                    "jsonrpc": "2.0",
                                    "id": data.get("id"),
                                    "result": {
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": str(result)
                                            }
                                        ]
                                    }
                                }
                                await websocket.send(json.dumps(response))
                                log("📤 Resultado enviado correctamente")
                                
                            except Exception as e:
                                log(f"❌ Error ejecutando herramienta: {e}")
                                # Enviar error como respuesta
                                error_response = {
                                    "jsonrpc": "2.0",
                                    "id": data.get("id"),
                                    "error": {
                                        "code": -32000,
                                        "message": f"Error ejecutando {tool_name}: {str(e)}"
                                    }
                                }
                                await websocket.send(json.dumps(error_response))
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
                            log("📤 Pong")
                            continue
                        
                    except json.JSONDecodeError:
                        log(f"⚠️ Mensaje no JSON: {message}")
                    except Exception as e:
                        log(f"❌ Error procesando mensaje: {e}")
                        
        except Exception as e:
            log(f"❌ Conexión perdida: {e}")
            log("🔄 Reconectando en 5 segundos...")
            await asyncio.sleep(5)

# ============================================
# Punto de entrada
# ============================================
if __name__ == "__main__":
    # Iniciar servidor HTTP en un hilo separado
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Conectar a Xiaozhi (con reconexión)
    asyncio.run(connect_to_xiaozhi())
