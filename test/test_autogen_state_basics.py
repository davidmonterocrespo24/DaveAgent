"""
Test básico de save_state/load_state de AutoGen

Este test demuestra:
1. Cómo funciona save_state() en un agente
2. La estructura del objeto de estado
3. Cómo funciona load_state() para restaurar
4. Qué información se persiste exactamente
"""
import asyncio
import json
from pathlib import Path
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
import os
from dotenv import load_dotenv


async def test_basic_save_load_state():
    """Test básico: guardar y cargar estado de un agente"""
    
    print("\n" + "="*80)
    print("TEST 1: Básico de save_state() y load_state()")
    print("="*80)
    
    # Cargar variables de entorno
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        print("❌ ERROR: DEEPSEEK_API_KEY no encontrada en .env")
        return
    
    # Crear modelo client usando model_capabilities (como en main.py)
    model_client = OpenAIChatCompletionClient(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
        model_capabilities={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        }
    )
    
    # =========================================================================
    # PASO 1: Crear agente y tener una conversación
    # =========================================================================
    print("\n📝 PASO 1: Creando agente y teniendo conversación inicial...")
    
    agent = AssistantAgent(
        name="test_agent",
        system_message="You are a helpful assistant. Answer concisely.",
        model_client=model_client,
    )
    
    # Primera interacción
    print("\n👤 Usuario: What is the capital of France?")
    response1 = await agent.on_messages(
        [TextMessage(content="What is the capital of France?", source="user")],
        CancellationToken()
    )
    print(f"🤖 Agente: {response1.chat_message.content}")
    
    # Segunda interacción
    print("\n👤 Usuario: What about Spain?")
    response2 = await agent.on_messages(
        [TextMessage(content="What about Spain?", source="user")],
        CancellationToken()
    )
    print(f"🤖 Agente: {response2.chat_message.content}")
    
    # =========================================================================
    # PASO 2: Guardar el estado
    # =========================================================================
    print("\n💾 PASO 2: Guardando estado del agente...")
    
    agent_state = await agent.save_state()
    
    print(f"\n📊 Tipo de estado: {type(agent_state)}")
    print(f"📊 Es un dict: {isinstance(agent_state, dict)}")
    
    # Analizar estructura del estado
    print("\n🔍 ESTRUCTURA DEL ESTADO:")
    print(json.dumps(agent_state, indent=2, default=str))
    
    # Guardar a archivo para inspección
    state_file = Path("test/.temp_test_state.json")
    state_file.parent.mkdir(exist_ok=True)
    with open(state_file, "w") as f:
        json.dump(agent_state, f, indent=2, default=str)
    print(f"\n✅ Estado guardado en: {state_file}")
    
    # =========================================================================
    # PASO 3: Crear NUEVO agente y cargar el estado
    # =========================================================================
    print("\n📂 PASO 3: Creando NUEVO agente y cargando estado...")
    
    # Cerrar el cliente del agente anterior
    await model_client.close()
    
    # Crear nuevo cliente
    model_client_new = OpenAIChatCompletionClient(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
        model_capabilities={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        }
    )
    
    # Crear NUEVO agente (simulando reinicio de aplicación)
    new_agent = AssistantAgent(
        name="test_agent",
        system_message="You are a helpful assistant. Answer concisely.",
        model_client=model_client_new,
    )
    
    # Cargar el estado guardado
    await new_agent.load_state(agent_state)
    print("✅ Estado cargado exitosamente")
    
    # =========================================================================
    # PASO 4: Verificar que el agente recuerda la conversación
    # =========================================================================
    print("\n🧪 PASO 4: Verificando que el agente recuerda...")
    
    print("\n👤 Usuario: What was the first capital I asked about?")
    response3 = await new_agent.on_messages(
        [TextMessage(content="What was the first capital I asked about?", source="user")],
        CancellationToken()
    )
    print(f"🤖 Agente: {response3.chat_message.content}")
    
    # =========================================================================
    # PASO 5: Analizar el contenido del estado
    # =========================================================================
    print("\n" + "="*80)
    print("📊 ANÁLISIS DETALLADO DEL ESTADO")
    print("="*80)
    
    if "llm_messages" in agent_state:
        messages = agent_state["llm_messages"]
        print(f"\n✅ Número de mensajes guardados: {len(messages)}")
        
        print("\n📝 MENSAJES GUARDADOS:")
        for i, msg in enumerate(messages, 1):
            print(f"\n--- Mensaje {i} ---")
            print(f"Tipo: {msg.get('type', 'N/A')}")
            print(f"Source: {msg.get('source', 'N/A')}")
            print(f"Content: {msg.get('content', 'N/A')}")
    
    print("\n🔑 CLAVES EN EL ESTADO:")
    for key in agent_state.keys():
        print(f"  - {key}: {type(agent_state[key])}")
    
    # Cleanup
    await model_client_new.close()
    
    print("\n" + "="*80)
    print("✅ TEST COMPLETADO")
    print("="*80)


async def test_state_structure_exploration():
    """Explorar la estructura del estado en detalle"""
    
    print("\n" + "="*80)
    print("TEST 2: Exploración Profunda de la Estructura del Estado")
    print("="*80)
    
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    model_client = OpenAIChatCompletionClient(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
        model_capabilities={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        }
    )
    
    agent = AssistantAgent(
        name="explorer",
        system_message="You are a test assistant.",
        model_client=model_client,
    )
    
    # Tener varias conversaciones
    conversations = [
        "Hello, my name is John",
        "I like programming in Python",
        "Can you remember my name?",
    ]
    
    for msg in conversations:
        print(f"\n👤 {msg}")
        response = await agent.on_messages(
            [TextMessage(content=msg, source="user")],
            CancellationToken()
        )
        print(f"🤖 {response.chat_message.content}")
    
    # Guardar estado
    state = await agent.save_state()
    
    print("\n" + "="*80)
    print("🔍 ANÁLISIS COMPLETO DEL ESTADO")
    print("="*80)
    
    def explore_dict(d, prefix=""):
        """Explora recursivamente un diccionario"""
        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                print(f"\n{full_key}: <dict>")
                explore_dict(value, full_key)
            elif isinstance(value, list):
                print(f"\n{full_key}: <list> con {len(value)} elementos")
                if value and len(value) > 0:
                    print(f"  Primer elemento tipo: {type(value[0])}")
                    if isinstance(value[0], dict):
                        print(f"  Claves del primer elemento: {list(value[0].keys())}")
            else:
                print(f"\n{full_key}: {type(value).__name__} = {str(value)[:100]}")
    
    explore_dict(state)
    
    # Guardar análisis completo
    analysis_file = Path("test/.temp_state_analysis.json")
    with open(analysis_file, "w") as f:
        json.dump(state, f, indent=2, default=str)
    
    print(f"\n\n✅ Análisis completo guardado en: {analysis_file}")
    
    await model_client.close()


async def main():
    """Ejecutar todos los tests"""
    
    print("\n" + "="*80)
    print("🧪 TESTS DE AUTOGEN STATE MANAGEMENT")
    print("="*80)
    
    try:
        # Test 1: Básico
        await test_basic_save_load_state()
        
        # Test 2: Exploración profunda
        await test_state_structure_exploration()
        
        print("\n" + "="*80)
        print("✅ TODOS LOS TESTS COMPLETADOS")
        print("="*80)
        print("\n📁 Archivos generados:")
        print("  - test/.temp_test_state.json")
        print("  - test/.temp_state_analysis.json")
        print("\n💡 Revisa estos archivos para entender la estructura del estado")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
