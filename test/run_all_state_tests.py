"""
Script para ejecutar todos los tests de AutoGen State Management

Ejecuta los tests en orden lógico y muestra resultados
"""
import subprocess
import sys
from pathlib import Path


def print_header(title):
    """Imprime un encabezado bonito"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def run_test(test_file, description):
    """Ejecuta un test y muestra el resultado"""
    print_header(f"🧪 {description}")
    print(f"📁 Archivo: {test_file}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            cwd=Path(__file__).parent.parent,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n✅ {description} - COMPLETADO")
            return True
        else:
            print(f"\n❌ {description} - FALLÓ")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR ejecutando {test_file}: {e}")
        return False


def main():
    """Ejecuta todos los tests"""
    
    print("\n" + "=" * 80)
    print("  🧪 SUITE DE TESTS: AUTOGEN STATE MANAGEMENT")
    print("=" * 80)
    
    print("""
Este script ejecutará todos los tests de AutoGen State Management
para demostrar cómo funciona save_state() y load_state().

Los tests incluyen:
  1. Test básico de estructura de estado
  2. Test de sesiones múltiples
  3. Test de visualización de historial
  4. Test de continuación de conversación

Asegúrate de tener:
  ✓ DEEPSEEK_API_KEY en tu archivo .env
  ✓ Todas las dependencias instaladas (pip install -r requirements.txt)
  ✓ Rich instalado (pip install rich)
    """)
    
    input("⏸️ Presiona Enter para comenzar...")
    
    tests = [
        ("test/test_autogen_state_basics.py", "Test Básico - Estructura del Estado"),
        ("test/test_autogen_state_sessions.py", "Test de Sesiones Múltiples"),
        ("test/test_autogen_state_history_viewer.py", "Test de Visualización de Historial"),
        ("test/test_autogen_state_resume.py", "Test de Continuación de Conversación"),
    ]
    
    results = []
    
    for test_file, description in tests:
        success = run_test(test_file, description)
        results.append((description, success))
        
        if not success:
            print(f"\n⚠️ El test falló. ¿Continuar con los siguientes? (s/n)")
            choice = input().strip().lower()
            if choice != 's':
                break
    
    # Resumen final
    print_header("📊 RESUMEN DE TESTS")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total - passed
    
    print(f"Total de tests: {total}")
    print(f"✅ Pasados: {passed}")
    print(f"❌ Fallidos: {failed}")
    print()
    
    for description, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"  {status} - {description}")
    
    print("\n" + "=" * 80)
    
    if failed == 0:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
    else:
        print(f"⚠️ {failed} test(s) fallaron. Revisa los errores arriba.")
    
    print("=" * 80)
    
    # Mostrar archivos generados
    print_header("📁 ARCHIVOS GENERADOS")
    
    temp_files = [
        "test/.temp_test_state.json",
        "test/.temp_state_analysis.json",
        "test/.temp_history_example.json",
        "test/.temp_resume_session.json",
    ]
    
    print("Archivos individuales:")
    for file in temp_files:
        if Path(file).exists():
            print(f"  ✓ {file}")
    
    sessions_dir = Path("test/.temp_sessions")
    if sessions_dir.exists():
        print("\nSesiones guardadas:")
        for session_file in sessions_dir.glob("*.json"):
            print(f"  ✓ {session_file}")
    
    print("\n💡 Revisa estos archivos JSON para entender la estructura del estado")
    print("\n📚 Lee la documentación en:")
    print("  - docs/AUTOGEN_STATE_STRUCTURE.md")
    print("  - docs/MIGRATION_TO_AUTOGEN_STATE.md")
    print("  - test/README_STATE_TESTS.md")


if __name__ == "__main__":
    main()
