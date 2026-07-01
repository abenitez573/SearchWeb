import os
import json
import asyncio
import websockets
from server import mcp

MCP_ENDPOINT = os.getenv("MCP_ENDPOINT")
print(f"🔍 MCP_ENDPOINT: {MCP_ENDPOINT}")

async def main():
    if not MCP_ENDPOINT:
        print("❌ MCP_ENDPOINT no configurado")
        return

    try:
        async with websockets.connect(MCP_ENDPOINT, ping_interval=20, ping_timeout=60) as websocket:
            print("✅ Conectado a Xiaozhi")
            
            async for message in websocket:
                data = json.loads(message)
                print(f"📥 {data}")
                
                if data.get("method") == "initialize":
                    await websocket.send(json.dumps({
                        "jsonrpc": "2.0",
                        "id": data["id"],
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {"tools": {}},
                            "serverInfo": {"name": "gateway", "version": "1.0"}
                        }
                    }))
                    print("📤 Inicialización respondida")
                
                elif data.get("method") == "tools/list":
                    await websocket.send(json.dumps({
                        "jsonrpc": "2.0",
                        "id": data["id"],
                        "result": {
                            "tools": [
                                {
                                    "name": "web_search",
                                    "description": "Busca en internet",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {"type": "string"},
                                            "num_results": {"type": "integer", "default": 5}
                                        },
                                        "required": ["query"]
                                    }
                                },
                                {
                                    "name": "get_current_time",
                                    "description": "Obtiene la hora actual",
                                    "inputSchema": {"type": "object", "properties": {}}
                                }
                            ]
                        }
                    }))
                    print("📤 Lista de herramientas enviada")
                
                elif data.get("method") == "tools/call":
                    tool = data["params"]["name"]
                    args = data["params"].get("arguments", {})
                    print(f"🔧 Llamando a {tool} con {args}")
                    
                    if tool == "web_search":
                        result = mcp.tools["web_search"](**args)
                    elif tool == "get_current_time":
                        result = mcp.tools["get_current_time"]()
                    else:
                        result = f"Herramienta desconocida: {tool}"
                    
                    await websocket.send(json.dumps({
                        "jsonrpc": "2.0",
                        "id": data["id"],
                        "result": {"content": [{"type": "text", "text": str(result)}]}
                    }))
                    print("📤 Respuesta enviada")
                
                elif data.get("method") == "ping":
                    await websocket.send(json.dumps({"jsonrpc": "2.0", "id": data["id"], "result": {}}))
                    print("📤 Pong")

    except Exception as e:
        print(f"❌ Error: {e}")
        return

if __name__ == "__main__":
    asyncio.run(main())
    print("🔄 Manteniendo el proceso vivo...")
    import time
    while True:
        time.sleep(60)
