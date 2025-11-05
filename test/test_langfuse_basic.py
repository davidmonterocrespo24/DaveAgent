"""
Test básico de Langfuse - Verificar autenticación y conexión

Este test verifica que:
1. Las credenciales de Langfuse son válidas
2. La conexión al servidor funciona correctamente
3. El cliente se inicializa sin errores
"""
import asyncio
import os
from dotenv import load_dotenv
from langfuse import Langfuse


def test_langfuse_authentication():
    """Test 1: Verificar autenticación con Langfuse"""
    print("=" * 80)
    print("TEST 1: Verificación de Autenticación con Langfuse")
    print("=" * 80)
    
    # Cargar variables de entorno
    load_dotenv()
    
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    host = os.getenv("LANGFUSE_HOST")
    
    print(f"\n📝 Configuración:")
    print(f"  • Secret Key: {secret_key[:20]}..." if secret_key else "  • Secret Key: ❌ NO CONFIGURADA")
    print(f"  • Public Key: {public_key[:20]}..." if public_key else "  • Public Key: ❌ NO CONFIGURADA")
    print(f"  • Host: {host}")
    
    # Inicializar cliente Langfuse
    print(f"\n🔌 Inicializando cliente Langfuse...")
    
    try:
        # Filter out Autogen OpenTelemetry spans
        langfuse = Langfuse(
            secret_key=secret_key,
            public_key=public_key,
            host=host,
            blocked_instrumentation_scopes=["autogen SingleThreadedAgentRuntime"]
        )
        
        print("✅ Cliente Langfuse creado exitosamente")
        
        # Verificar autenticación
        print(f"\n🔐 Verificando autenticación...")
        
        if langfuse.auth_check():
            print("✅ Langfuse client is authenticated and ready!")
            print(f"\n✅ TEST PASADO: Autenticación exitosa")
            return True
        else:
            print("❌ Authentication failed. Please check your credentials and host.")
            print(f"\n❌ TEST FALLIDO: Autenticación falló")
            return False
            
    except Exception as e:
        print(f"❌ Error inicializando Langfuse: {e}")
        print(f"\n❌ TEST FALLIDO: Error en inicialización")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Flush any pending traces
        if 'langfuse' in locals():
            langfuse.flush()


def test_langfuse_event_logging():
    """Test 2: Crear un evento en Langfuse"""
    print("\n" + "=" * 80)
    print("TEST 2: Registro de Eventos")
    print("=" * 80)
    
    load_dotenv()
    
    try:
        langfuse = Langfuse(
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            host=os.getenv("LANGFUSE_HOST"),
            blocked_instrumentation_scopes=["autogen SingleThreadedAgentRuntime"]
        )
        
        print(f"\n📊 Creando evento de prueba...")
        
        # Crear un evento usando create_event
        event = langfuse.create_event(
            name="test_event",
            metadata={"test": "basic_event_creation", "version": "1.0"}
        )
        
        print(f"✅ Evento creado")
        
        # Flush para enviar datos
        langfuse.flush()
        print(f"✅ Datos enviados a Langfuse")
        
        print(f"\n✅ TEST PASADO: Evento creado exitosamente")
        print(f"💡 Revisa tu dashboard de Langfuse: {os.getenv('LANGFUSE_HOST')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando evento: {e}")
        print(f"\n❌ TEST FALLIDO")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todos los tests"""
    print("\n" + "🧪" * 40)
    print("SUITE DE TESTS: Langfuse Básico")
    print("🧪" * 40 + "\n")
    
    results = []
    
    # Test 1: Autenticación
    results.append(("Autenticación", test_langfuse_authentication()))
    
    # Test 2: Registro de eventos
    results.append(("Registro de Eventos", test_langfuse_event_logging()))
    
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
        print("\n🎉 ¡Todos los tests pasaron exitosamente!")
        print("💡 Langfuse está configurado correctamente y listo para usar")
    else:
        print("\n⚠️ Algunos tests fallaron. Revisa la configuración.")
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
