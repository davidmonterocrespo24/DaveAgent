"""
Script automatizado para publicar CodeAgent en PyPI
Ejecutar: python publish.py [test|prod]
"""
import subprocess
import sys
import shutil
from pathlib import Path


def run_command(cmd, description):
    """Ejecuta un comando y muestra resultado"""
    print(f"\n{'='*70}")
    print(f"🔧 {description}")
    print(f"{'='*70}")
    print(f"Comando: {cmd}\n")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)

    if result.returncode != 0:
        print(f"\n❌ ERROR:")
        print(result.stderr)
        return False

    print(f"✅ {description} - COMPLETADO")
    return True


def clean_build():
    """Limpia directorios de build anteriores"""
    print("\n🧹 Limpiando builds anteriores...")

    dirs_to_remove = ['dist', 'build', 'src/codeagent_ai.egg-info']
    for dir_name in dirs_to_remove:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  ✓ Eliminado: {dir_name}")

    print("✅ Limpieza completada")


def check_dependencies():
    """Verifica que estén instaladas las herramientas necesarias"""
    print("\n📦 Verificando dependencias...")

    dependencies = ['build', 'twine']
    missing = []

    for dep in dependencies:
        result = subprocess.run(
            f"{sys.executable} -m {dep} --version",
            shell=True,
            capture_output=True
        )
        if result.returncode != 0:
            missing.append(dep)
        else:
            print(f"  ✓ {dep} instalado")

    if missing:
        print(f"\n❌ Faltan dependencias: {', '.join(missing)}")
        print(f"Instalar con: pip install {' '.join(missing)}")
        return False

    print("✅ Todas las dependencias instaladas")
    return True


def build_package():
    """Construye el paquete"""
    return run_command(
        f"{sys.executable} -m build",
        "Construyendo paquete"
    )


def check_package():
    """Verifica que el paquete esté bien formado"""
    return run_command(
        f"{sys.executable} -m twine check dist/*",
        "Verificando integridad del paquete"
    )


def upload_to_testpypi():
    """Sube el paquete a TestPyPI"""
    print("\n" + "="*70)
    print("📤 Subiendo a TestPyPI")
    print("="*70)
    print("\nNOTA: Usa estos credenciales:")
    print("  Username: __token__")
    print("  Password: Tu token de TestPyPI (empieza con 'pypi-')")
    print()

    result = subprocess.run(
        f"{sys.executable} -m twine upload --repository testpypi dist/*",
        shell=True
    )

    return result.returncode == 0


def upload_to_pypi():
    """Sube el paquete a PyPI"""
    print("\n" + "="*70)
    print("🚀 Subiendo a PyPI (PRODUCCIÓN)")
    print("="*70)
    print("\n⚠️  ADVERTENCIA: Esto publicará el paquete públicamente!")
    print("Una vez publicado, NO puedes eliminar esta versión.")
    print()

    confirm = input("¿Estás seguro de que quieres continuar? (escribe 'SI'): ")

    if confirm != "SI":
        print("❌ Publicación cancelada")
        return False

    print("\nNOTA: Usa estos credenciales:")
    print("  Username: __token__")
    print("  Password: Tu token de PyPI (empieza con 'pypi-')")
    print()

    result = subprocess.run(
        f"{sys.executable} -m twine upload dist/*",
        shell=True
    )

    return result.returncode == 0


def show_summary(target):
    """Muestra resumen final"""
    print("\n" + "="*70)
    print("✅ PUBLICACIÓN COMPLETADA")
    print("="*70)

    if target == "test":
        print("\n📦 Paquete publicado en TestPyPI")
        print("Ver en: https://test.pypi.org/project/codeagent-ai/")
        print("\nPara probar la instalación:")
        print("  pip install --index-url https://test.pypi.org/simple/ \\")
        print("              --extra-index-url https://pypi.org/simple/ \\")
        print("              codeagent-ai")
    else:
        print("\n🎉 Paquete publicado en PyPI!")
        print("Ver en: https://pypi.org/project/codeagent-ai/")
        print("\nCualquiera puede instalarlo con:")
        print("  pip install codeagent-ai")

    print("\n🎊 ¡Felicidades!")


def main():
    """Función principal"""
    print("="*70)
    print("📦 CodeAgent - Script de Publicación en PyPI")
    print("="*70)

    # Verificar argumentos
    if len(sys.argv) < 2:
        print("\n❌ Uso: python publish.py [test|prod]")
        print("\n  test - Publicar en TestPyPI (para pruebas)")
        print("  prod - Publicar en PyPI (producción)")
        sys.exit(1)

    target = sys.argv[1].lower()

    if target not in ['test', 'prod']:
        print(f"\n❌ Objetivo inválido: {target}")
        print("Usa 'test' o 'prod'")
        sys.exit(1)

    print(f"\n🎯 Objetivo: {'TestPyPI' if target == 'test' else 'PyPI (PRODUCCIÓN)'}")

    # Verificar dependencias
    if not check_dependencies():
        sys.exit(1)

    # Limpiar builds anteriores
    clean_build()

    # Construir paquete
    if not build_package():
        print("\n❌ Error al construir el paquete")
        sys.exit(1)

    # Verificar paquete
    if not check_package():
        print("\n❌ El paquete tiene errores")
        sys.exit(1)

    # Subir según el objetivo
    if target == 'test':
        success = upload_to_testpypi()
    else:
        success = upload_to_pypi()

    if not success:
        print("\n❌ Error al subir el paquete")
        sys.exit(1)

    # Mostrar resumen
    show_summary(target)


if __name__ == "__main__":
    main()
