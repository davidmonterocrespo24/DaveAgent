"""
Test de DeepSeek-Reasoner con AutoGen 0.4
Este ejemplo muestra como usar el modelo deepseek-reasoner con AutoGen.

DeepSeek-R1 (deepseek-reasoner) es un modelo especializado en razonamiento logico
que muestra su proceso de pensamiento antes de dar la respuesta final.

COMPATIBILIDAD CON AUTOGEN:
- ✓ Compatible con AutoGen 0.4
- ✓ Funciona con AssistantAgent
- ✓ Funciona con RoundRobinGroupChat
- ✗ NO soporta function_calling (herramientas)
- ✗ NO soporta structured_output (JSON)
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Cargar variables de entorno
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Configuracion de DeepSeek-Reasoner
DEEPSEEK_API_KEY = os.getenv('DAVEAGENT_API_KEY') or os.getenv('CODEAGENT_API_KEY')  # Compatibility
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-reasoner"

print(f"""
{'='*80}
CONFIGURACION DE DEEPSEEK-REASONER
{'='*80}
Modelo:    {DEEPSEEK_MODEL}
Base URL:  {DEEPSEEK_BASE_URL}
API Key:   {'Configurada OK' if DEEPSEEK_API_KEY else 'NO configurada'}
{'='*80}
""")

# Crear el cliente de DeepSeek-Reasoner
deepseek_client = OpenAIChatCompletionClient(
    model=DEEPSEEK_MODEL,
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
    model_capabilities={
        "json_output": False,
        "function_calling": False,
        "vision": False,
        "structured_output": False,
    }
)

# ============================================================================
# TEST 1: Razonamiento Matematico Simple
# ============================================================================

async def test_simple_math():
    """Test 1: Pregunta matematica simple"""
    print("\n" + "="*80)
    print("TEST 1: Razonamiento Matematico Simple")
    print("="*80 + "\n")

    agent = AssistantAgent(
        name="math_reasoner",
        model_client=deepseek_client,
        system_message="Eres un experto en matematicas. Explica tu razonamiento.",
    )

    task = "Si tengo 5 manzanas y compro 3 mas, pero luego regalo 2, cuantas me quedan?"

    print(f"Pregunta: {task}\n")
    print("Pensando...\n")

    result = await agent.run(task=task)

    for message in result.messages:
        if hasattr(message, 'source') and message.source != "user":
            print(f"\n[{message.source}]: {message.content}\n")


# ============================================================================
# TEST 2: Problema Logico
# ============================================================================

async def test_logic_puzzle():
    """Test 2: Problema de logica"""
    print("\n" + "="*80)
    print("TEST 2: Problema de Logica")
    print("="*80 + "\n")

    agent = AssistantAgent(
        name="logic_expert",
        model_client=deepseek_client,
        system_message="Eres un experto en logica. Resuelve problemas paso a paso.",
    )

    task = """
    Hay 3 cajas: una con manzanas, una con naranjas, y una con ambas frutas.
    Todas las etiquetas estan INCORRECTAS.
    Si puedes sacar UNA fruta de UNA caja, como determinas el contenido de todas?
    """

    print(f"Problema: {task}\n")
    print("Analizando...\n")

    result = await agent.run(task=task)

    for message in result.messages:
        if hasattr(message, 'source') and message.source != "user":
            print(f"\n[{message.source}]: {message.content}\n")


# ============================================================================
# TEST 3: Multi-Agente (Profesor y Estudiante)
# ============================================================================

async def test_multi_agent():
    """Test 3: Conversacion multi-agente"""
    print("\n" + "="*80)
    print("TEST 3: Conversacion Multi-Agente (Profesor - Estudiante)")
    print("="*80 + "\n")

    teacher = AssistantAgent(
        name="profesor",
        model_client=deepseek_client,
        system_message="""Eres un profesor paciente. Explica conceptos de forma clara.
Usa ejemplos simples.""",
    )

    student = AssistantAgent(
        name="estudiante",
        model_client=deepseek_client,
        system_message="""Eres un estudiante curioso. Haz preguntas sobre lo que no entiendas.
Cuando entiendas el concepto, di TERMINATE.""",
    )

    team = RoundRobinGroupChat(
        participants=[teacher, student],
        termination_condition=TextMentionTermination("TERMINATE"),
        max_turns=4,
    )

    task = "Explica que es un algoritmo usando un ejemplo de la vida diaria."

    print(f"Tema: {task}\n")
    print("Iniciando conversacion...\n")

    await Console(team.run_stream(task=task))


# ============================================================================
# TEST 4: Problema de Codigo
# ============================================================================

async def test_code_reasoning():
    """Test 4: Razonamiento sobre codigo"""
    print("\n" + "="*80)
    print("TEST 4: Razonamiento Sobre Codigo")
    print("="*80 + "\n")

    agent = AssistantAgent(
        name="code_analyzer",
        model_client=deepseek_client,
        system_message="Eres un experto en programacion. Analiza codigo y explica su comportamiento.",
    )

    task = """
    Analiza este codigo y explica que hace:

    def mystery(n):
        if n <= 1:
            return n
        return mystery(n-1) + mystery(n-2)

    Que valor retorna mystery(5)?
    """

    print(f"Codigo a analizar:\n{task}\n")
    print("Analizando...\n")

    result = await agent.run(task=task)

    for message in result.messages:
        if hasattr(message, 'source') and message.source != "user":
            print(f"\n[{message.source}]: {message.content}\n")


# ============================================================================
# MAIN - Selector de Tests
# ============================================================================

async def main():
    """Menu principal - selecciona que tests ejecutar"""

    if not DEEPSEEK_API_KEY:
        print("\nERROR: No se encontro DAVEAGENT_API_KEY en el archivo .env")
        print("Configura tu API key de DeepSeek en el archivo .env\n")
        return

    print("""
TESTS DISPONIBLES:
==================
1. Razonamiento Matematico Simple (rapido)
2. Problema de Logica (medio)
3. Conversacion Multi-Agente (medio)
4. Razonamiento sobre Codigo (medio)
5. Ejecutar TODOS los tests (lento)

Por defecto se ejecuta el Test 1 (mas rapido para verificar funcionamiento)
    """)

    try:
        # Por defecto ejecutar solo el test 1 (mas rapido)
        # Descomenta otros tests segun necesites

        await test_simple_math()          # Test 1: Rapido
        # await test_logic_puzzle()       # Test 2: Medio
        # await test_multi_agent()        # Test 3: Medio (requiere mas tiempo)
        # await test_code_reasoning()     # Test 4: Medio

        print("\n" + "="*80)
        print("TESTS COMPLETADOS EXITOSAMENTE!")
        print("="*80)
        print("\nPara ejecutar mas tests, descomenta las lineas en main()")
        print("Los tests comentados son mas complejos y toman mas tiempo.\n")

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
