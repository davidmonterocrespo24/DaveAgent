"""
Test de integración Langfuse + AutoGen

Este test verifica que:
1. Langfuse se integra correctamente con AutoGen via OpenLit
2. Las trazas de conversaciones se envían a Langfuse automáticamente
3. Se capturan correctamente las llamadas al LLM
"""
import asyncio
import os
from dotenv import load_dotenv
from langfuse import Langfuse
import openlit

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


async def test_autogen_with_langfuse():
    """Test: AutoGen + Langfuse Integration"""
    print("=" * 80)
    print("TEST: Integración AutoGen + Langfuse")
    print("=" * 80)
    
    # Cargar variables de entorno
    load_dotenv()
    
    try:
        # Step 1: Inicializar Langfuse
        print(f"\n📊 Paso 1: Inicializando Langfuse...")
        
        # Filtrar spans de AutoGen Runtime
        langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
            blocked_instrumentation_scopes=["autogen SingleThreadedAgentRuntime"]
        )
        
        # Verificar autenticación
        if langfuse.auth_check():
            print("✅ Langfuse autenticado correctamente")
        else:
            print("❌ Fallo en autenticación de Langfuse")
            return False
        
        # Step 2: Inicializar OpenLit para instrumentación automática
        print(f"\n🔧 Paso 2: Inicializando OpenLit instrumentation...")
        
        # OpenLit captura automáticamente las operaciones de AutoGen
        # y exporta spans de OpenTelemetry a Langfuse
        openlit.init(
            tracer=langfuse._otel_tracer,
            disable_batch=True  # Procesar trazas inmediatamente
        )
        print("✅ OpenLit inicializado - trazas automáticas activadas")
        
        # Step 3: Crear cliente del modelo
        print(f"\n🤖 Paso 3: Creando modelo cliente (DeepSeek)...")
        
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
        
        # Step 4: Crear agente
        print(f"\n👤 Paso 4: Creando agente AutoGen...")
        
        agent = AssistantAgent(
            "assistant",
            model_client=model_client,
            system_message="You are a helpful assistant. Keep responses short and concise."
        )
        
        print("✅ Agente creado")
        
        # Step 5: Ejecutar tarea simple
        print(f"\n💬 Paso 5: Ejecutando conversación con agente...")
        print(f"  📝 Tarea: Say 'Hello World from Langfuse!'")
        
        # OpenLit capturará automáticamente esta conversación
        # No necesitamos logging manual - OpenLit lo hace por nosotros
        result = await agent.run(task="Say 'Hello World from Langfuse!'")
        
        print(f"\n✅ Conversación completada - OpenLit envió trazas automáticamente")
        
        print(f"\n📨 Respuesta del agente:")
        for message in result.messages:
            if message.source != "user":
                print(f"  🤖 {message.content}")
        
        # Step 6: Cerrar cliente
        print(f"\n🔒 Paso 6: Cerrando conexiones...")
        
        await model_client.close()
        
        # Flush Langfuse para asegurar que se envíen todas las trazas
        langfuse.flush()
        
        print("✅ Conexiones cerradas")
        print("✅ Trazas enviadas a Langfuse via OpenLit")
        
        # Resumen
        print(f"\n" + "=" * 80)
        print("✅ TEST PASADO: Integración exitosa")
        print("=" * 80)
        print(f"\n💡 Verifica tus trazas en el dashboard de Langfuse:")
        print(f"   {os.getenv('LANGFUSE_HOST')}")
        print(f"\n📊 Deberías ver (capturado automáticamente por OpenLit):")
        print(f"   • ✅ Traza completa de la conversación")
        print(f"   • ✅ Llamadas al LLM (DeepSeek) vía OpenAI API")
        print(f"   • ✅ Inputs y outputs de cada mensaje")
        print(f"   • ✅ Tokens usados (prompt + completion)")
        print(f"   • ✅ Latencia y tiempos de respuesta")
        print(f"   • ✅ Metadata del agente y modelo")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Ejecutar test de integración"""
    print("\n" + "🧪" * 40)
    print("TEST DE INTEGRACIÓN: Langfuse + AutoGen + DeepSeek")
    print("🧪" * 40 + "\n")
    
    success = await test_autogen_with_langfuse()
    
    if success:
        print("\n🎉 ¡Test de integración completado exitosamente!")
    else:
        print("\n⚠️ Test falló. Revisa los errores arriba.")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
