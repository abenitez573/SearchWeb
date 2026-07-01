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
            
            # 1. Enviar "initialize" (JSON-RPC 2.0)
            init_msg = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "gateway", "version": "1.0"}
                }
            }
            await websocket.send(json.dumps(init_msg))
            print("📤 Inicialización enviada")
            
            # 2. Esperar respuesta de "initialize"
            response = await websocket.recv()
            print(f"📥 Respuesta: {response}")
            
            # 3. Enviar notificación de inicialización completada
            init_done = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            await websocket.send(json.dumps(init_done))
            print("📤 Inicialización completada")
            
            # 4. Enviar "tools/list" para anunciar las herramientas
            tools_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list",
                "params": {}
            }
            await websocket.send(json.dumps(tools_msg))
            print("📤 Lista de herramientas solicitada")
            
            # 5. Bucle principal: recibir y procesar mensajes
            async for message in websocket:
                data = json.loads(message)
                print(f"📥 Recibido: {data}")
                # Aquí iría el manejo de "tools/call" para ejecutar las herramientas
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
