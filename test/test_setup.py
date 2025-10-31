"""
Script de prueba rápida para verificar que todos los componentes funcionan
"""
import asyncio
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from tools import read_file, write_file, list_dir


async def test_basic_setup():
    """Prueba básica de configuración"""
    print("Iniciando pruebas de configuracion...")
    print()

    # Test 1: Modelo cliente
    print("[OK] Test 1: Cliente del modelo")
    try:
        model_client = OpenAIChatCompletionClient(
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            api_key="sk-8cb1f4fc5bd74bd3a83f31204b942d60",
            model_capabilities={
                "vision": True,
                "function_calling": True,
                "json_output": True,
            },
        )
        print("  [OK] Cliente del modelo creado correctamente")
    except Exception as e:
        print(f"  [ERROR] Error creando cliente: {e}")
        return

    # Test 2: Herramientas
    print("[OK] Test 2: Herramientas importadas")
    tools = [read_file, write_file, list_dir]
    print(f"  [OK] {len(tools)} herramientas cargadas")

    # Test 3: Agente con herramientas
    print("[OK] Test 3: Creando agente con herramientas")
    try:
        agent = AssistantAgent(
            name="TestAgent",
            model_client=model_client,
            tools=tools,
            system_message="You are a test agent."
        )
        print("  [OK] Agente creado correctamente")
    except Exception as e:
        print(f"  [ERROR] Error creando agente: {e}")
        await model_client.close()
        return

    # Test 4: Prueba simple de herramienta
    print("[OK] Test 4: Probando herramienta list_dir")
    try:
        result = await list_dir(".")
        print(f"  [OK] list_dir ejecutado correctamente")
        print(f"  Resultado (primeras 200 caracteres): {result[:200]}...")
    except Exception as e:
        print(f"  [ERROR] Error ejecutando list_dir: {e}")

    # Cleanup
    await model_client.close()
    print()
    print("[SUCCESS] Todas las pruebas completadas!")


if __name__ == "__main__":
    asyncio.run(test_basic_setup())
