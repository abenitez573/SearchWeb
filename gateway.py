import os
import json
import asyncio
import websockets

MCP_ENDPOINT = os.getenv("MCP_ENDPOINT")

async def main():
    if not MCP_ENDPOINT:
        print("❌ MCP_ENDPOINT no configurado")
        return

    try:
        async with websockets.connect(MCP_ENDPOINT) as websocket:
            print("✅ Conectado a Xiaozhi")
            
            # Esperar el mensaje de inicialización del servidor
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"📥 Recibido del servidor: {data}")
            
            # Responder al "initialize" del servidor
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
            
            # Ahora enviar nuestra propia inicialización
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "gateway", "version": "1.0"}
                }
            }
            await websocket.send(json.dumps(init_msg))
            print("📤 Inicialización enviada")
            
            # Esperar respuesta de nuestro initialize
            resp = await websocket.recv()
            print(f"📥 Respuesta a initialize: {resp}")
            
            # Enviar notificación de inicialización completada
            init_done = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            await websocket.send(json.dumps(init_done))
            print("📤 Inicialización completada")
            
            # Esperar la solicitud de lista de herramientas
            tools_req = await websocket.recv()
            print(f"📥 Solicitud de herramientas: {tools_req}")
            
            # Responder con la lista de herramientas
            tools_response = {
                "jsonrpc": "2.0",
                "id": 1,
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
            }
            await websocket.send(json.dumps(tools_response))
            print("📤 Lista de herramientas enviada")
            
            # Bucle principal: recibir y procesar mensajes
            async for message in websocket:
                data = json.loads(message)
                print(f"📥 Recibido: {data}")
                
                if data.get("method") == "tools/call":
                    # Aquí iría la lógica para ejecutar las herramientas
                    pass
                elif data.get("method") == "ping":
                    await websocket.send(json.dumps({
                        "jsonrpc": "2.0",
                        "id": data.get("id"),
                        "result": {}
                    }))
                    print("📤 Pong")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
