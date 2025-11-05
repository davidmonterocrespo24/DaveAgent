"""
Script para ejecutar todos los tests de Langfuse

Ejecuta los tests en orden:
1. Test básico (autenticación)
2. Test de integración con AutoGen
3. Test multi-agente
"""
import asyncio
import subprocess
import sys


def run_test(test_file: str, test_name: str) -> bool:
    """Ejecuta un test y retorna True si pasa"""
    print(f"\n{'='*80}")
    print(f"Ejecutando: {test_name}")
    print(f"Archivo: {test_file}")
    print(f"{'='*80}\n")
    
    result = subprocess.run(
        [sys.executable, test_file],
        capture_output=False,
        text=True
    )
    
    passed = result.returncode == 0
    
    if passed:
        print(f"\n✅ {test_name} PASADO")
    else:
        print(f"\n❌ {test_name} FALLIDO")
    
    return passed


def main():
    """Ejecutar todos los tests"""
    print("\n" + "🧪" * 40)
    print("SUITE COMPLETA: Tests de Langfuse")
    print("🧪" * 40)
    
    tests = [
        ("test/test_langfuse_basic.py", "Test Básico de Langfuse"),
        ("test/test_langfuse_autogen_integration.py", "Test de Integración AutoGen"),
        ("test/test_langfuse_multi_agent.py", "Test Multi-Agente"),
    ]
    
    results = []
    
    for test_file, test_name in tests:
        passed = run_test(test_file, test_name)
        results.append((test_name, passed))
    
    # Resumen final
    print("\n" + "=" * 80)
    print("RESUMEN FINAL DE TESTS")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASADO" if passed else "❌ FALLIDO"
        print(f"{status} - {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\n📊 Resultados finales: {total_passed}/{total_tests} tests pasados")
    
    if total_passed == total_tests:
        print("\n🎉 ¡ÉXITO! Todos los tests pasaron")
        print("💡 Langfuse está completamente integrado con AutoGen")
        print(f"💡 Revisa tu dashboard: https://langfuse-u0sg0c8gokgkwwk084844k8o.daveplanet.com")
        return 0
    else:
        print("\n⚠️ Algunos tests fallaron. Revisa los errores arriba.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
