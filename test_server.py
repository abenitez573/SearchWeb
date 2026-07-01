print("🔍 Intentando importar server...")
try:
    from server import mcp
    print(f"✅ server importado correctamente. mcp = {mcp}")
except Exception as e:
    print(f"❌ Error al importar server: {e}")
    import traceback
    traceback.print_exc()
