# ============================================
# Manejar "tools/list" (Obtener herramientas desde server.py)
# ============================================
if data.get("method") == "tools/list":
    # Obtener la lista de herramientas desde el servidor MCP
    tools_list = []
    for tool_name, tool_func in mcp.tools.items():
        tools_list.append({
            "name": tool_name,
            "description": tool_func.__doc__ or f"Herramienta {tool_name}",
            "inputSchema": {
                "type": "object",
                "properties": {
                    # Esto es opcional, pero puedes extraer parámetros si es necesario
                },
                "required": []
            }
        })
    
    response = {
        "jsonrpc": "2.0",
        "id": data.get("id"),
        "result": {"tools": tools_list}
    }
    await websocket.send(json.dumps(response))
    print("📤 Lista de herramientas enviada (desde server.py)", flush=True)
    continue
