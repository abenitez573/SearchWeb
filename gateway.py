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

# ============================================
# Función de log con flush forzado
# ============================================
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
                            log("📤 Inicialización respondida")
                            continue
                        
                        # ============================================
                        # 2. Manejar "tools/list" (OPCIÓN 2 - DINÁMICA)
                        # ============================================
                        if data.get("method") == "tools/list":
                            # Obtener herramientas desde server.py usando list_tools()
                            tools_list = []
                            try:
                                # FastMCP moderno: list_tools() devuelve una lista de objetos Tool
                                if hasattr(mcp, 'list_tools'):
                                    tools = await mcp.list_tools()
                                    for tool in tools:
                                        # Adaptar al formato que espera Xiaozhi
                                        tools_list.append({
                                            "name": tool.name,
                                            "description": tool.description or f"Herramienta {tool.name}",
                                            "inputSchema": tool.parameters or {
                                                "type": "object",
                                                "properties": {},
                                                "required": []
                                            }
                                        })
                                else:
                                    # Fallback: obtener desde _tool_manager (para versiones anteriores)
                                    if hasattr(mcp, '_tool_manager'):
                                        for tool_name, tool_func in mcp._tool_manager._tools.items():
                                            tools_list.append({
                                                "name": tool_name,
                                                "description": tool_func.__doc__ or f"Herramienta {tool_name}",
                                                "inputSchema": {
                                                    "type": "object",
                                                    "properties": {},
                                                    "required": []
                                                }
                                            })
                                    else:
                                        # Si no funciona, usar lista manual (fallback seguro)
                                        tools_list = [
                                            {
                                                "name": "web_search",
                                                "description": "Busca información en internet usando Serper.dev",
                                                "inputSchema": {
                                                    "type": "object",
                                                    "properties": {
                                                        "query": {
                                                            "type": "string",
                                                            "description": "La consulta de búsqueda"
                                                        },
                                                        "num_results": {
                                                            "type": "integer",
                                                            "description": "Número de resultados",
                                                            "default": 5
                                                        }
                                                    },
                                                    "required": ["query"]
                                                }
                                            }
                                        ]
                            except Exception as e:
                                log(f"⚠️ Error obteniendo herramientas: {e}. Usando lista manual.")
                                tools_list = [
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
                                    }
                                ]
                            
                            response = {
                                "jsonrpc": "2.0",
                                "id": data.get("id"),
                                "result": {"tools": tools_list}
                            }
                            await websocket.send(json.dumps(response))
                            log(f"📤 Lista de herramientas enviada ({len(tools_list)} herramientas)")
                            continue
                        
                        # ============================================
                        # 3. Manejar "tools/call"
                        # ============================================
                        if data.get("method") == "tools/call":
                            params = data.get("params", {})
                            tool_name = params.get("name")
                            args = params.get("arguments", {})
                            
                            log(f"🔧 Llamando a: {tool_name} con args: {args}")
                            
                            try:
                                # Ejecutar la herramienta desde server.py
                                # FastMCP moderno: usar call_tool()
                                if hasattr(mcp, 'call_tool'):
                                    result = await mcp.call_tool(tool_name, args)
                                else:
                                    # Fallback: ejecutar directamente la función
                                    if tool_name == "web_search":
                                        # Importar la función desde server.py
                                        from server import web_search
                                        result = web_search(**args)
                                    else:
                                        result = f"Herramienta desconocida: {tool_name}"
                                
                                # Si el resultado es un objeto ToolResult, extraer el texto
                                if hasattr(result, 'content'):
                                    result_text = "\n".join([c.text for c in result.content if c.type == "text"])
                                else:
                                    result_text = str(result)
                                
                                log(f"📤 Resultado obtenido (primeros 100 chars): {result_text[:100]}...")
                                
                                # Enviar respuesta en el formato esperado
                                response = {
                                    "jsonrpc": "2.0",
                                    "id": data.get("id"),
                                    "result": {
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": result_text
                                            }
                                        ]
                                    }
                                }
                                await websocket.send(json.dumps(response))
                                log("📤 Resultado enviado correctamente")
                                
                            except Exception as e:
                                log(f"❌ Error ejecutando herramienta: {e}")
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
                        # 4. Manejar "ping"
                        # ============================================
                        if data.get("method") == "ping":
                            await websocket.send(json.dumps({
                                "jsonrpc": "2.0",
                                "id": data.get("id"),
                                "result": {}
                            }))
                            log("📤 Pong")
                            continue
                        
                        # ============================================
                        # 5. Manejar notificaciones
                        # ============================================
                        if data.get("method") == "notifications/initialized":
                            log("✅ Inicialización confirmada por el servidor")
                            continue
                        
                    except json.JSONDecodeError:
                        log(f"⚠️ Mensaje no JSON: {message}")
                    except Exception as e:
                        log(f"❌ Error procesando mensaje: {e}")
                        
        except websockets.exceptions.ConnectionClosed as e:
            log(f"❌ Conexión cerrada: {e}")
            log("🔄 Reconectando en 5 segundos...")
            await asyncio.sleep(5)
        except Exception as e:
            log(f"❌ Error en WebSocket: {e}")
            log("🔄 Reconectando en 5 segundos...")
            await asyncio.sleep(5)

# ============================================
# Punto de entrada
# ============================================
if __name__ == "__main__":
    log("🚀 Iniciando gateway")
    log(f"🔍 MCP_ENDPOINT: {MCP_ENDPOINT}")
    
    # Iniciar servidor HTTP en un hilo separado
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Conectar a Xiaozhi (con reconexión)
    asyncio.run(connect_to_xiaozhi())
