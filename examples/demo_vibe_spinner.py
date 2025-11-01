"""
Demo del Vibe Spinner - Sistema de animación con mensajes creativos
"""
import asyncio
import time
from src.utils import VibeSpinner

def demo_basic_spinner():
    """Demo básico del spinner con mensajes rotativos"""
    print("=== Demo 1: Spinner Básico con Mensajes Rotativos ===\n")

    spinner = VibeSpinner(
        spinner_style="dots",
        color="cyan",
        language="es"
    )

    print("Iniciando spinner por 5 segundos...")
    spinner.start()
    time.sleep(5)
    spinner.stop()

    print("✓ Spinner detenido\n")

def demo_custom_message():
    """Demo con un mensaje personalizado"""
    print("=== Demo 2: Spinner con Mensaje Personalizado ===\n")

    spinner = VibeSpinner(
        messages=["procesando tu solicitud"],
        spinner_style="dots",
        color="green",
        language="es"
    )

    print("Iniciando spinner con mensaje custom por 3 segundos...")
    spinner.start()
    time.sleep(3)
    spinner.stop()

    print("✓ Spinner detenido\n")

def demo_different_styles():
    """Demo de diferentes estilos de spinner"""
    print("=== Demo 3: Diferentes Estilos de Spinner ===\n")

    styles = ["dots", "line", "circle", "arrow", "dots2", "box", "bounce"]

    for style in styles:
        print(f"Estilo: {style}")
        spinner = VibeSpinner(
            messages=[f"usando estilo {style}"],
            spinner_style=style,
            color="cyan",
            language="es"
        )
        spinner.start()
        time.sleep(2)
        spinner.stop()
        print()

def demo_context_manager():
    """Demo usando context manager"""
    print("=== Demo 4: Usando Context Manager ===\n")

    print("El spinner se iniciará y detendrá automáticamente...")
    with VibeSpinner(spinner_style="dots", color="magenta", language="es"):
        time.sleep(4)

    print("✓ Spinner detenido automáticamente\n")

def demo_language_switch():
    """Demo con diferentes idiomas"""
    print("=== Demo 5: Spinner en Inglés ===\n")

    print("Spinner con mensajes en inglés por 5 segundos...")
    spinner = VibeSpinner(
        spinner_style="dots",
        color="blue",
        language="en"
    )
    spinner.start()
    time.sleep(5)
    spinner.stop()

    print("✓ Spinner detenido\n")

async def demo_async_usage():
    """Demo de uso en contexto asíncrono"""
    print("=== Demo 6: Uso Asíncrono ===\n")

    spinner = VibeSpinner(
        spinner_style="dots",
        color="yellow",
        language="es"
    )

    print("Iniciando spinner mientras simulamos trabajo asíncrono...")
    spinner.start()

    # Simular trabajo asíncrono
    await asyncio.sleep(3)

    spinner.stop()
    print("✓ Trabajo asíncrono completado\n")

def main():
    """Ejecuta todos los demos"""
    print("\n" + "="*60)
    print("         DEMO DEL VIBE SPINNER - CodeAgent")
    print("="*60 + "\n")

    # Demo 1: Básico
    demo_basic_spinner()
    time.sleep(1)

    # Demo 2: Mensaje custom
    demo_custom_message()
    time.sleep(1)

    # Demo 3: Diferentes estilos
    demo_different_styles()
    time.sleep(1)

    # Demo 4: Context manager
    demo_context_manager()
    time.sleep(1)

    # Demo 5: Inglés
    demo_language_switch()
    time.sleep(1)

    # Demo 6: Asíncrono
    print("Ejecutando demo asíncrono...")
    asyncio.run(demo_async_usage())

    print("="*60)
    print("         ✓ TODOS LOS DEMOS COMPLETADOS")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
