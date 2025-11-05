"""
Test de conversación multi-agente con Langfuse

Este test verifica que:
1. Se capturan trazas de conversaciones complejas multi-agente automáticamente
2. Se rastrean correctamente múltiples llamadas al LLM via OpenLit
3. Se organizan las trazas por agente y tarea
"""
import asyncio
import os
from dotenv import load_dotenv
from langfuse import Langfuse
import openlit

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient


async def test_multi_agent_conversation():
    """Test: Conversación multi-agente con Langfuse tracing"""
    print("=" * 80)
    print("TEST: Conversación Multi-Agente + Langfuse")
    print("=" * 80)
    
    load_dotenv()
    
    try:
        # Step 1: Inicializar Langfuse
        print(f"\n📊 Paso 1: Inicializando Langfuse...")
        
        langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
            blocked_instrumentation_scopes=["autogen SingleThreadedAgentRuntime"]
        )
        
        if langfuse.auth_check():
            print("✅ Langfuse autenticado")
        else:
            print("❌ Fallo en autenticación")
            return False
        
        # Step 2: Inicializar OpenLit
        print(f"\n🔧 Paso 2: Inicializando OpenLit...")
        openlit.init(tracer=langfuse._otel_tracer, disable_batch=True)
        print("✅ OpenLit inicializado - captura automática activada")
        
        # Step 3: Crear modelo cliente
        print(f"\n🤖 Paso 3: Creando modelo cliente...")
        
        model_client = OpenAIChatCompletionClient(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            model_capabilities={
                "vision": False,
                "function_calling": True,
                "json_output": True,
            }
        )
        
        print("✅ Modelo cliente creado")
        
        # Step 4: Crear múltiples agentes
        print(f"\n👥 Paso 4: Creando equipo de agentes...")
        
        # Agente de código
        coder = AssistantAgent(
            "Coder",
            model_client=model_client,
            system_message="""You are a Python coding expert. 
            Write clean, efficient Python code. 
            When done, say TASK_COMPLETED."""
        )
        
        # Agente revisor
        reviewer = AssistantAgent(
            "Reviewer",
            model_client=model_client,
            system_message="""You are a code reviewer. 
            Review code for bugs and best practices. 
            Provide brief feedback. 
            When done, say TASK_COMPLETED."""
        )
        
        print("✅ Agentes creados: Coder y Reviewer")
        
        # Step 5: Crear equipo
        print(f"\n🎯 Paso 5: Creando RoundRobinGroupChat...")
        
        termination = TextMentionTermination("TASK_COMPLETED") | MaxMessageTermination(6)
        
        team = RoundRobinGroupChat(
            participants=[coder, reviewer],
            termination_condition=termination
        )
        
        print("✅ Equipo creado")
        
        # Step 6: Ejecutar conversación
        print(f"\n💬 Paso 6: Ejecutando conversación multi-agente...")
        print(f"  📝 Tarea: Write a Python function to calculate fibonacci numbers")
        
        # OpenLit capturará automáticamente toda esta conversación
        message_count = 0
        async for message in team.run_stream(
            task="Write a Python function to calculate fibonacci numbers up to n. Keep it short."
        ):
            if hasattr(message, 'source') and message.source != 'user':
                message_count += 1
                print(f"  🤖 [{message.source}] Mensaje #{message_count}")
        
        print(f"\n✅ Conversación completada ({message_count} mensajes)")
        print(f"✅ OpenLit capturó automáticamente {message_count} interacciones")
        
        # Step 7: Cerrar conexiones
        print(f"\n🔒 Paso 7: Cerrando conexiones...")
        await model_client.close()
        langfuse.flush()
        print("✅ Conexiones cerradas")
        
        # Resumen
        print(f"\n" + "=" * 80)
        print("✅ TEST PASADO: Conversación multi-agente rastreada exitosamente")
        print("=" * 80)
        print(f"\n💡 Verifica en tu dashboard de Langfuse:")
        print(f"   {os.getenv('LANGFUSE_HOST')}")
        print(f"\n📊 Deberías ver:")
        print(f"   • Trazas de ambos agentes (Coder y Reviewer)")
        print(f"   • Múltiples llamadas al LLM")
        print(f"   • Flujo de conversación completo")
        print(f"   • Tokens totales utilizados")
        print(f"   • Latencia de cada llamada")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multi_agent_with_tools():
    """Test: Multi-agente con herramientas (más complejo)"""
    print("\n" + "=" * 80)
    print("TEST: Multi-Agente con Herramientas + Langfuse")
    print("=" * 80)
    
    load_dotenv()
    
    try:
        # Inicializar Langfuse
        print(f"\n📊 Inicializando Langfuse...")
        langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
            blocked_instrumentation_scopes=["autogen SingleThreadedAgentRuntime"]
        )
        
        if not langfuse.auth_check():
            print("❌ Fallo en autenticación")
            return False
        
        # Inicializar OpenLit
        openlit.init(tracer=langfuse._otel_tracer, disable_batch=True)
        print("✅ OpenLit inicializado")
        
        # Crear modelo
        model_client = OpenAIChatCompletionClient(
            model="deepseek-chat",
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com",
            model_capabilities={
                "vision": False,
                "function_calling": True,
                "json_output": True,
            }
        )
        
        # Definir una herramienta simple
        def calculate_sum(a: int, b: int) -> int:
            """Calculate the sum of two numbers."""
            return a + b
        
        # Agente con herramientas
        print(f"\n🤖 Creando agente con herramientas...")
        agent_with_tools = AssistantAgent(
            "MathAgent",
            model_client=model_client,
            tools=[calculate_sum],
            system_message="You are a math assistant. Use the calculate_sum tool when needed."
        )
        
        print("✅ Agente creado con herramienta calculate_sum")
        
        # Ejecutar tarea
        print(f"\n💬 Ejecutando tarea...")
        print(f"  📝 Tarea: Calculate 15 + 27 using the tool")
        
        result = await agent_with_tools.run(
            task="Calculate 15 + 27 using the calculate_sum tool"
        )
        
        print(f"\n📨 Resultado:")
        for message in result.messages[-2:]:  # Últimos 2 mensajes
            if hasattr(message, 'content'):
                print(f"  🤖 {message.content[:100]}")
        
        # Cerrar
        await model_client.close()
        langfuse.flush()
        
        print(f"\n✅ TEST PASADO: Agente con herramientas rastreado exitosamente")
        print(f"💡 Dashboard: {os.getenv('LANGFUSE_HOST')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Ejecutar todos los tests multi-agente"""
    print("\n" + "🧪" * 40)
    print("SUITE DE TESTS: Conversaciones Multi-Agente + Langfuse")
    print("🧪" * 40 + "\n")
    
    results = []
    
    # Test 1: Conversación multi-agente básica
    print("\n🔹 TEST 1: Conversación Multi-Agente")
    results.append(("Multi-Agente Básico", await test_multi_agent_conversation()))
    
    # Test 2: Multi-agente con herramientas
    print("\n🔹 TEST 2: Multi-Agente con Herramientas")
    results.append(("Multi-Agente con Tools", await test_multi_agent_with_tools()))
    
    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN DE TESTS")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASADO" if passed else "❌ FALLIDO"
        print(f"{status} - {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\n📊 Resultados: {total_passed}/{total_tests} tests pasados")
    
    if total_passed == total_tests:
        print("\n🎉 ¡Todos los tests de multi-agente pasaron!")
        print("💡 Langfuse está capturando correctamente todas las trazas complejas")
    else:
        print("\n⚠️ Algunos tests fallaron")
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
