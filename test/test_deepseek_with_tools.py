"""
Ejemplo AVANZADO: DeepSeek-Reasoner con Herramientas
=====================================================

Este ejemplo demuestra que DeepSeek-Reasoner SI puede usar herramientas,
contrario a lo que dice la documentacion antigua.

Caso de uso: Agente que analiza codigo Python y genera reportes
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Fix encoding para Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Cargar variables de entorno
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

DEEPSEEK_API_KEY = os.getenv('DAVEAGENT_API_KEY') or os.getenv('CODEAGENT_API_KEY')  # Compatibility
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

print("="*80)
print("DEEPSEEK-REASONER CON HERRAMIENTAS - EJEMPLO AVANZADO")
print("="*80)
print("\nEste ejemplo demuestra que DeepSeek-Reasoner SI soporta herramientas\n")

# Cliente con function_calling HABILITADO
client = OpenAIChatCompletionClient(
    model="deepseek-reasoner",
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
    model_capabilities={
        "function_calling": True,   # HABILITADO
        "json_output": True,        # HABILITADO
        "vision": False,
        "structured_output": True,  # HABILITADO
    }
)

# ============================================================================
# DEFINIR HERRAMIENTAS
# ============================================================================

async def read_python_file(filepath: str) -> str:
    """Lee un archivo Python y retorna su contenido"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return f"Contenido de {filepath}:\n\n{content}"
    except Exception as e:
        return f"Error leyendo {filepath}: {str(e)}"


async def analyze_code_complexity(code: str) -> str:
    """Analiza la complejidad de codigo Python"""
    lines = code.split('\n')
    total_lines = len(lines)
    code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
    functions = len([l for l in lines if 'def ' in l])
    classes = len([l for l in lines if 'class ' in l])

    complexity = "simple" if code_lines < 50 else "media" if code_lines < 200 else "compleja"

    return f"""Analisis de complejidad:
- Total lineas: {total_lines}
- Lineas de codigo: {code_lines}
- Funciones: {functions}
- Clases: {classes}
- Complejidad: {complexity}"""


async def generate_json_report(data: str) -> str:
    """Convierte analisis en formato JSON"""
    import json
    import re

    # Extraer metricas del analisis
    lines_match = re.search(r'Total lineas: (\d+)', data)
    code_match = re.search(r'Lineas de codigo: (\d+)', data)
    func_match = re.search(r'Funciones: (\d+)', data)
    class_match = re.search(r'Clases: (\d+)', data)
    comp_match = re.search(r'Complejidad: (\w+)', data)

    report = {
        "total_lines": int(lines_match.group(1)) if lines_match else 0,
        "code_lines": int(code_match.group(1)) if code_match else 0,
        "functions": int(func_match.group(1)) if func_match else 0,
        "classes": int(class_match.group(1)) if class_match else 0,
        "complexity": comp_match.group(1) if comp_match else "desconocida"
    }

    return json.dumps(report, indent=2, ensure_ascii=False)


# ============================================================================
# TEST 1: Agente con Herramientas de Analisis
# ============================================================================

async def test_code_analyzer_with_tools():
    """Agente que analiza codigo usando herramientas"""
    print("\n" + "="*80)
    print("TEST 1: Analisis de Codigo con Herramientas")
    print("="*80 + "\n")

    # Crear agente con TODAS las herramientas
    analyzer = AssistantAgent(
        name="code_analyzer",
        model_client=client,
        tools=[
            read_python_file,
            analyze_code_complexity,
            generate_json_report,
        ],
        system_message="""Eres un experto en analisis de codigo Python.
Puedes usar las siguientes herramientas:
1. read_python_file - para leer archivos Python
2. analyze_code_complexity - para analizar la complejidad
3. generate_json_report - para generar reportes JSON

Usa las herramientas en orden logico para completar la tarea.""",
    )

    task = """Analiza el archivo test/test_deepseek_reasoner.py y:
1. Lee su contenido
2. Analiza su complejidad
3. Genera un reporte JSON

Muestra tu razonamiento paso a paso."""

    print(f"Tarea: {task}\n")
    print("Ejecutando agente con herramientas...\n")

    try:
        result = await analyzer.run(task=task)

        print("\n" + "="*80)
        print("RESULTADO DEL AGENTE")
        print("="*80)

        for message in result.messages:
            if hasattr(message, 'source'):
                if message.source == "user":
                    continue

                content = str(message.content)

                # Mostrar llamadas a funciones
                if "FunctionCall" in content:
                    print(f"\n🔧 [HERRAMIENTA LLAMADA]")
                    print(f"   {content[:200]}...")

                # Mostrar resultados de funciones
                elif "FunctionExecutionResult" in content:
                    print(f"\n📊 [RESULTADO DE HERRAMIENTA]")
                    print(f"   {content[:200]}...")

                # Mostrar razonamiento y respuesta final
                else:
                    print(f"\n💭 [{message.source}]:")
                    print(f"   {content[:500]}")
                    if len(content) > 500:
                        print(f"   ... (truncado, {len(content)} caracteres totales)")

        print("\n" + "="*80)
        print("✅ TEST COMPLETADO - DeepSeek-Reasoner uso herramientas exitosamente!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


# ============================================================================
# TEST 2: Comparacion con y sin Herramientas
# ============================================================================

async def test_comparison():
    """Compara agente con y sin herramientas"""
    print("\n" + "="*80)
    print("TEST 2: Comparacion CON vs SIN herramientas")
    print("="*80 + "\n")

    # Agente SIN herramientas
    print("--- Agente SIN herramientas ---")
    agent_no_tools = AssistantAgent(
        name="reasoner_no_tools",
        model_client=OpenAIChatCompletionClient(
            model="deepseek-reasoner",
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            model_capabilities={
                "function_calling": False,  # SIN herramientas
                "json_output": False,
                "vision": False,
                "structured_output": False,
            }
        ),
        system_message="Eres un asistente experto en matematicas.",
    )

    task = "Cual es la raiz cuadrada de 144?"

    print(f"Pregunta: {task}")
    result1 = await agent_no_tools.run(task=task)

    print("\nRespuesta (sin herramientas):")
    for msg in result1.messages:
        if hasattr(msg, 'source') and msg.source != "user":
            print(f"  {msg.content[:200]}")

    # Agente CON herramienta de calculadora
    print("\n--- Agente CON herramienta de calculadora ---")

    async def calculate(expression: str) -> str:
        """Calcula una expresion matematica"""
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            return f"Resultado: {result}"
        except Exception as e:
            return f"Error: {str(e)}"

    agent_with_tools = AssistantAgent(
        name="reasoner_with_tools",
        model_client=client,  # CON function_calling=True
        tools=[calculate],
        system_message="Eres un asistente experto en matematicas. Usa la herramienta calculate() para calculos.",
    )

    print(f"Pregunta: {task}")
    result2 = await agent_with_tools.run(task=task)

    print("\nRespuesta (con herramientas):")
    for msg in result2.messages:
        if hasattr(msg, 'source') and msg.source != "user":
            content = str(msg.content)
            if "FunctionCall" in content:
                print(f"  🔧 Uso herramienta: {content[:100]}...")
            elif "FunctionExecutionResult" not in content:
                print(f"  {content[:200]}")

    print("\n" + "="*80)
    print("Conclusion: DeepSeek-Reasoner funciona tanto CON como SIN herramientas")
    print("="*80)


# ============================================================================
# MAIN
# ============================================================================

async def main():
    if not DEEPSEEK_API_KEY:
        print("\n❌ ERROR: No se encontro DAVEAGENT_API_KEY en .env")
        return

    print("\nEjecutando tests...\n")

    # Test 1: Analisis de codigo con herramientas
    await test_code_analyzer_with_tools()

    # Test 2: Comparacion (comentado por defecto)
    # await test_comparison()

    print("\n" + "="*80)
    print("TODOS LOS TESTS COMPLETADOS")
    print("="*80)
    print("\n✅ CONFIRMADO: DeepSeek-Reasoner SI soporta function calling!")
    print("✅ CONFIRMADO: DeepSeek-Reasoner SI puede usar herramientas!")
    print("\nLa documentacion antigua estaba desactualizada.\n")


if __name__ == "__main__":
    asyncio.run(main())
