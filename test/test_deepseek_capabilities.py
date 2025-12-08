"""
Test para verificar las capacidades REALES de DeepSeek-Reasoner
Este script prueba si DeepSeek-Reasoner soporta:
1. Function calling (herramientas)
2. JSON estructurado
3. Posibles workarounds
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
import json

# Fix encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Cargar variables de entorno
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

DEEPSEEK_API_KEY = os.getenv('DAVEAGENT_API_KEY') or os.getenv('CODEAGENT_API_KEY')  # Compatibility
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

print("="*80)
print("TEST DE CAPACIDADES REALES DE DEEPSEEK-REASONER")
print("="*80)

# ============================================================================
# TEST 1: Function Calling CON function_calling=True
# ============================================================================

async def test_function_calling_enabled():
    """Probar si realmente soporta function calling cuando se habilita"""
    print("\n" + "="*80)
    print("TEST 1: Function Calling HABILITADO (function_calling=True)")
    print("="*80 + "\n")

    try:
        # Cliente CON function_calling habilitado
        client = OpenAIChatCompletionClient(
            model="deepseek-reasoner",
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            model_capabilities={
                "function_calling": True,  # HABILITAR function calling
                "vision": False,
                "json_output": False,
                "structured_output": False,
            }
        )

        # Definir una herramienta simple
        async def get_weather(city: str) -> str:
            """Obtiene el clima de una ciudad"""
            return f"El clima en {city} es soleado, 25 grados"

        # Crear agente con herramienta
        agent = AssistantAgent(
            name="weather_agent",
            model_client=client,
            tools=[get_weather],
            system_message="Eres un asistente que puede consultar el clima usando herramientas.",
        )

        task = "Cual es el clima en Madrid?"

        print(f"Pregunta: {task}")
        print("Ejecutando con function_calling=True...\n")

        result = await agent.run(task=task)

        print("\n--- RESULTADO ---")
        for message in result.messages:
            if hasattr(message, 'source') and message.source != "user":
                print(f"\n[{message.source}]: {message.content}")

        print("\n✅ EXITO: DeepSeek-Reasoner PUEDE usar function calling!")
        return True

    except Exception as e:
        print(f"\n❌ ERROR con function_calling=True:")
        print(f"   {type(e).__name__}: {str(e)}")
        print("\n⚠️ CONFIRMADO: DeepSeek-Reasoner NO soporta function calling nativamente")
        return False


# ============================================================================
# TEST 2: JSON Estructurado CON json_output=True
# ============================================================================

async def test_json_output_enabled():
    """Probar si soporta JSON estructurado cuando se habilita"""
    print("\n" + "="*80)
    print("TEST 2: JSON Output HABILITADO (json_output=True)")
    print("="*80 + "\n")

    try:
        # Cliente CON json_output habilitado
        client = OpenAIChatCompletionClient(
            model="deepseek-reasoner",
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            model_capabilities={
                "function_calling": False,
                "vision": False,
                "json_output": True,  # HABILITAR JSON
                "structured_output": True,
            }
        )

        agent = AssistantAgent(
            name="json_agent",
            model_client=client,
            system_message="""Responde SOLO en formato JSON valido.
Ejemplo: {"respuesta": "valor", "confianza": 0.95}""",
        )

        task = "Dame informacion sobre Python en formato JSON con campos: nombre, tipo, año_creacion"

        print(f"Pregunta: {task}")
        print("Ejecutando con json_output=True...\n")

        result = await agent.run(task=task)

        print("\n--- RESULTADO ---")
        response_text = None
        for message in result.messages:
            if hasattr(message, 'source') and message.source != "user":
                print(f"\n[{message.source}]: {message.content}")
                response_text = message.content

        # Intentar parsear como JSON
        if response_text:
            try:
                parsed = json.loads(response_text)
                print("\n✅ EXITO: La respuesta es JSON valido!")
                print(f"JSON parseado: {json.dumps(parsed, indent=2, ensure_ascii=False)}")
                return True
            except json.JSONDecodeError:
                print("\n⚠️ La respuesta NO es JSON valido")
                return False

    except Exception as e:
        print(f"\n❌ ERROR con json_output=True:")
        print(f"   {type(e).__name__}: {str(e)}")
        return False


# ============================================================================
# TEST 3: JSON via Prompt Engineering (sin habilitar json_output)
# ============================================================================

async def test_json_via_prompt():
    """Probar si puede generar JSON mediante instrucciones en el prompt"""
    print("\n" + "="*80)
    print("TEST 3: JSON via Prompt Engineering (json_output=False)")
    print("="*80 + "\n")

    try:
        # Cliente SIN json_output habilitado
        client = OpenAIChatCompletionClient(
            model="deepseek-reasoner",
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            model_capabilities={
                "function_calling": False,
                "vision": False,
                "json_output": False,
                "structured_output": False,
            }
        )

        agent = AssistantAgent(
            name="json_prompt_agent",
            model_client=client,
            system_message="""Eres un asistente que SIEMPRE responde en formato JSON valido.
IMPORTANTE: Tu respuesta FINAL debe ser SOLO el objeto JSON, sin texto adicional.
No uses markdown, no uses ```json, solo el JSON puro.""",
        )

        task = """Crea un JSON con informacion sobre el lenguaje Python.
Debe tener exactamente estos campos:
- nombre (string)
- tipo (string)
- ano_creacion (number)
- paradigmas (array de strings)

Responde SOLO con el JSON, nada mas."""

        print(f"Pregunta: {task}")
        print("Ejecutando con prompt engineering...\n")

        result = await agent.run(task=task)

        print("\n--- RESULTADO ---")
        response_text = None
        for message in result.messages:
            if hasattr(message, 'source') and message.source != "user":
                content = message.content
                print(f"\n[{message.source}]: {content[:500]}...")
                response_text = content

        # Intentar extraer JSON de la respuesta
        if response_text:
            # Buscar JSON en la respuesta (puede estar dentro de texto)
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group(0))
                    print("\n✅ EXITO: Se pudo extraer JSON de la respuesta!")
                    print(f"JSON parseado: {json.dumps(parsed, indent=2, ensure_ascii=False)}")
                    return True
                except json.JSONDecodeError:
                    print("\n⚠️ Se encontro algo parecido a JSON pero no es valido")
                    return False
            else:
                print("\n⚠️ No se encontro JSON en la respuesta")
                return False

    except Exception as e:
        print(f"\n❌ ERROR:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# TEST 4: Simular Function Calling con ReAct Pattern
# ============================================================================

async def test_react_pattern():
    """Probar si podemos simular function calling con ReAct pattern"""
    print("\n" + "="*80)
    print("TEST 4: Simular Function Calling con ReAct Pattern")
    print("="*80 + "\n")

    try:
        client = OpenAIChatCompletionClient(
            model="deepseek-reasoner",
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
            model_capabilities={
                "function_calling": False,
                "vision": False,
                "json_output": False,
                "structured_output": False,
            }
        )

        agent = AssistantAgent(
            name="react_agent",
            model_client=client,
            system_message="""Eres un asistente que puede usar herramientas siguiendo este patron:

HERRAMIENTAS DISPONIBLES:
1. get_weather(city: str) -> Obtiene el clima de una ciudad
2. calculate(expression: str) -> Calcula una expresion matematica

Para usar una herramienta, responde en este formato:
ACCION: nombre_herramienta
PARAMETROS: {"param": "valor"}

Ejemplo:
ACCION: get_weather
PARAMETROS: {"city": "Madrid"}

Despues de usar la herramienta, recibiras el resultado y podras dar tu respuesta final.""",
        )

        task = "Necesito saber el clima en Barcelona"

        print(f"Pregunta: {task}")
        print("Ejecutando con ReAct pattern...\n")

        result = await agent.run(task=task)

        print("\n--- RESULTADO ---")
        response_text = None
        for message in result.messages:
            if hasattr(message, 'source') and message.source != "user":
                content = message.content
                print(f"\n[{message.source}]: {content}")
                response_text = content

        # Verificar si intenta usar el formato de herramienta
        if response_text and ("ACCION:" in response_text or "PARAMETROS:" in response_text):
            print("\n✅ EXITO: El modelo intenta usar el patron ReAct!")
            print("   Esto significa que podemos simular function calling con preprocesamiento")
            return True
        else:
            print("\n⚠️ El modelo no uso el patron ReAct, respondio directamente")
            return False

    except Exception as e:
        print(f"\n❌ ERROR:")
        print(f"   {type(e).__name__}: {str(e)}")
        return False


# ============================================================================
# MAIN
# ============================================================================

async def main():
    if not DEEPSEEK_API_KEY:
        print("\nERROR: No se encontro DAVEAGENT_API_KEY en .env")
        return

    results = {}

    # Test 1: Function Calling nativo
    results['function_calling'] = await test_function_calling_enabled()

    # Test 2: JSON Output nativo
    results['json_output'] = await test_json_output_enabled()

    # Test 3: JSON via Prompt
    results['json_prompt'] = await test_json_via_prompt()

    # Test 4: ReAct Pattern
    results['react_pattern'] = await test_react_pattern()

    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE RESULTADOS")
    print("="*80)
    print(f"\n1. Function Calling nativo:        {'✅ SI' if results['function_calling'] else '❌ NO'}")
    print(f"2. JSON Output nativo:             {'✅ SI' if results['json_output'] else '❌ NO'}")
    print(f"3. JSON via Prompt Engineering:    {'✅ SI' if results['json_prompt'] else '❌ NO'}")
    print(f"4. ReAct Pattern para herramientas: {'✅ SI' if results['react_pattern'] else '❌ NO'}")

    print("\n" + "="*80)
    print("CONCLUSIONES")
    print("="*80)

    if not results['function_calling']:
        print("\n❌ DeepSeek-Reasoner NO soporta function calling nativo")
        if results['react_pattern']:
            print("✅ PERO podemos simular herramientas con ReAct pattern + preprocesamiento")

    if not results['json_output']:
        print("\n❌ DeepSeek-Reasoner NO soporta JSON estructurado nativo")
        if results['json_prompt']:
            print("✅ PERO puede generar JSON mediante prompt engineering")

    print()


if __name__ == "__main__":
    asyncio.run(main())
