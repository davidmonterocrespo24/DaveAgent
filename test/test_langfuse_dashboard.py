"""
Test para verificar que los datos aparecen en el dashboard de Langfuse

Este test crea traces VISIBLES en el dashboard usando la API directa.
"""
import os
from dotenv import load_dotenv
from langfuse import Langfuse
import time
from datetime import datetime


def test_create_visible_trace():
    """Crear una traza que DEFINITIVAMENTE aparezca en el dashboard"""
    print("\n" + "=" * 80)
    print("TEST: Crear Traza Visible en Dashboard de Langfuse")
    print("=" * 80)
    
    load_dotenv()
    
    try:
        # Inicializar Langfuse
        print("\n📊 Inicializando Langfuse...")
        langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            host=os.getenv("LANGFUSE_HOST")
        )
        
        if not langfuse.auth_check():
            print("❌ Autenticación fallida")
            return False
        
        print("✅ Langfuse autenticado")
        
        # MÉTODO 1: Crear trace manualmente
        print("\n📝 Método 1: Creando trace manual...")
        
        trace = langfuse.trace(
            name="test-trace-manual",
            user_id="user-123",
            metadata={
                "test": "dashboard_visibility",
                "environment": "testing",
                "timestamp": time.time()
            },
            tags=["test", "manual", "visibility"]
        )
        
        print(f"✅ Trace creado - ID: {trace.id}")
        
        # Agregar una generación al trace
        generation = trace.generation(
            name="test-generation",
            model="deepseek-chat",
            input=[{"role": "user", "content": "Hello from Langfuse test!"}],
            output="This is a test response from DaveAgent",
            metadata={"tokens": 50, "latency_ms": 450}
        )
        
        print(f"✅ Generation agregada al trace")
        
        # MÉTODO 2: Crear span
        print("\n📝 Método 2: Creando span...")
        
        span = trace.span(
            name="test-span",
            input={"action": "test_dashboard"},
            output={"status": "success"}
        )
        
        print(f"✅ Span creado")
        
        # MÉTODO 3: Crear evento
        print("\n📝 Método 3: Creando evento...")
        
        event = trace.event(
            name="test-event",
            metadata={
                "message": "Test event for dashboard",
                "priority": "high"
            }
        )
        
        print(f"✅ Evento creado")
        
        # MÉTODO 4: Crear score (evaluación)
        print("\n📝 Método 4: Creando score...")
        
        langfuse.score(
            trace_id=trace.id,
            name="quality",
            value=0.95,
            comment="Test quality score"
        )
        
        print(f"✅ Score agregado")
        
        # Flush para asegurar que todo se envíe
        print("\n🔄 Enviando datos a Langfuse...")
        langfuse.flush()
        
        print("✅ Datos enviados")
        
        # Información para el usuario
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETADO - Trace creado exitosamente")
        print("=" * 80)
        print(f"\n📊 Ve tu trace en el dashboard:")
        print(f"   {os.getenv('LANGFUSE_HOST')}")
        print(f"\n🔍 Busca por:")
        print(f"   • Trace ID: {trace.id}")
        print(f"   • Name: test-trace-manual")
        print(f"   • User ID: user-123")
        print(f"   • Tags: test, manual, visibility")
        print(f"\n💡 El trace contiene:")
        print(f"   ✓ 1 Generation (LLM call simulado)")
        print(f"   ✓ 1 Span (operación)")
        print(f"   ✓ 1 Event (evento)")
        print(f"   ✓ 1 Score (evaluación)")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simple_trace():
    """Crear una traza simple y clara"""
    print("\n" + "=" * 80)
    print("TEST: Crear Traza Simple en Dashboard")
    print("=" * 80)
    
    load_dotenv()
    
    try:
        # Inicializar Langfuse
        print("\n📊 Inicializando Langfuse...")
        langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            host=os.getenv("LANGFUSE_HOST")
        )
        
        if not langfuse.auth_check():
            print("❌ Autenticación fallida")
            return False
        
        print("✅ Langfuse autenticado")
        
        # Crear trace simple
        print("\n📝 Creando trace simple...")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        trace = langfuse.trace(
            name=f"DaveAgent Test - {timestamp}",
            user_id="david-test-user",
            session_id=f"session-{int(time.time())}",
            metadata={
                "test_type": "dashboard_visibility",
                "environment": "testing",
                "framework": "DaveAgent",
                "timestamp": timestamp
            },
            tags=["test", "daveagent", "visibility-check"]
        )
        
        print(f"✅ Trace creado - ID: {trace.id}")
        print(f"   Name: DaveAgent Test - {timestamp}")
        print(f"   Session: session-{int(time.time())}")
        
        # Agregar una generación (simulando una llamada al LLM)
        print("\n📝 Agregando generation (LLM call)...")
        
        generation = trace.generation(
            name="deepseek-test-call",
            model="deepseek-chat",
            input=[
                {"role": "system", "content": "You are DaveAgent, a helpful AI assistant"},
                {"role": "user", "content": "Hello! Can you see this in Langfuse?"}
            ],
            output="Yes! I can see this trace in the Langfuse dashboard. This is a test from DaveAgent.",
            metadata={
                "tokens_prompt": 25,
                "tokens_completion": 18,
                "tokens_total": 43,
                "latency_ms": 450,
                "cost_usd": 0.0001
            },
            usage={
                "prompt_tokens": 25,
                "completion_tokens": 18,
                "total_tokens": 43
            }
        )
        
        print(f"✅ Generation agregada")
        
        # Agregar un span (operación)
        print("\n📝 Agregando span...")
        
        span = trace.span(
            name="process-user-query",
            input={"query": "Test query from DaveAgent"},
            output={"result": "success", "response_length": 100},
            metadata={"operation": "query_processing"}
        )
        
        print(f"✅ Span creado")
        
        # Agregar score
        print("\n📝 Agregando score (evaluación)...")
        
        langfuse.score(
            trace_id=trace.id,
            name="response_quality",
            value=0.95,
            comment="Test score - excellent response"
        )
        
        print(f"✅ Score agregado")
        
        # Flush
        print("\n🔄 Enviando todo a Langfuse...")
        langfuse.flush()
        time.sleep(2)  # Esperar a que se procese
        
        print("✅ Datos enviados y procesados")
        
        # Información
        print("\n" + "=" * 80)
        print("✅ TEST COMPLETADO")
        print("=" * 80)
        print(f"\n📊 Abre tu dashboard AHORA:")
        print(f"   {os.getenv('LANGFUSE_HOST')}")
        print(f"\n🔍 Busca en el dashboard:")
        print(f"   • Trace Name: 'DaveAgent Test - {timestamp}'")
        print(f"   • User ID: david-test-user")
        print(f"   • Tags: test, daveagent, visibility-check")
        print(f"   • Trace ID: {trace.id}")
        print(f"\n📦 El trace contiene:")
        print(f"   ✓ 1 Generation (llamada a deepseek-chat)")
        print(f"   ✓ 1 Span (operación de procesamiento)")
        print(f"   ✓ 1 Score (evaluación de calidad: 0.95)")
        print(f"   ✓ Metadata completa con tokens y latencia")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


@observe()
def test_with_decorator():
    """Test usando decorator @observe() - más fácil de usar"""
    print("\n" + "=" * 80)
    print("TEST: Usando @observe() Decorator")
    print("=" * 80)
    
    load_dotenv()
    
    try:
        print("\n📝 Ejecutando función decorada con @observe()...")
        
        # Esta función será automáticamente rastreada
        result = process_with_langfuse("Hello from decorator!")
        
        print(f"✅ Resultado: {result}")
        
        # Actualizar el trace actual con metadata
        langfuse_context.update_current_trace(
            name="test-trace-decorator",
            user_id="user-456",
            session_id="session-test-001",
            tags=["decorator", "auto-trace"],
            metadata={"method": "decorator", "framework": "langfuse"}
        )
        
        print("✅ Trace actualizado con metadata")
        
        # Flush
        from langfuse import Langfuse
        langfuse = Langfuse()
        langfuse.flush()
        
        print("\n✅ TEST COMPLETADO con @observe()")
        print(f"💡 Busca en el dashboard: session-test-001")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


@observe()
def process_with_langfuse(message: str) -> str:
    """Función automáticamente rastreada por Langfuse"""
    # Simular procesamiento
    time.sleep(0.1)
    
    # Agregar score
    langfuse_context.score_current_observation(
        name="processing_quality",
        value=0.98
    )
    
    return f"Processed: {message}"


def main():
    """Ejecutar todos los tests"""
    print("\n" + "🔬" * 40)
    print("SUITE: Tests de Visibilidad en Dashboard de Langfuse")
    print("🔬" * 40)
    
    results = []
    
    # Test 1: Trace manual
    results.append(("Trace Manual", test_create_visible_trace()))
    
    # Test 2: Con decorator
    results.append(("Decorator @observe()", test_with_decorator()))
    
    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\n📊 {total_passed}/{len(results)} tests pasados")
    
    if total_passed == len(results):
        print("\n🎉 ¡Todos los traces fueron enviados!")
        print(f"\n📊 Abre tu dashboard ahora:")
        print(f"   {os.getenv('LANGFUSE_HOST')}")
        print(f"\n🔍 Deberías ver:")
        print(f"   • Trace: test-trace-manual (con 4 elementos)")
        print(f"   • Trace: test-trace-decorator (con @observe)")
        print(f"   • Session: session-test-001")
    
    return total_passed == len(results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
