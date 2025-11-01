"""
Script de prueba para verificar la integración del CodeSearcher en el team
"""
import asyncio
import logging
from datetime import datetime
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from src.agents import TaskPlanner, CodeSearcher
from src.managers import ConversationManager


async def test_integration():
    """Prueba la integración del CodeSearcher"""
    print("=" * 70)
    print("TEST: Integracion de CodeSearcher en SelectorGroupChat")
    print("=" * 70)

    # Inicializar componentes básicos sin CLI
    print("\n[1] Inicializando componentes del team...")

    model_client = OpenAIChatCompletionClient(
        model="deepseek-chat",
        base_url="https://api.deepseek.com",
        api_key="sk-8cb1f4fc5bd74bd3a83f31204b942d60",
        model_capabilities={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        },
    )

    # Importar herramientas
    from src.tools import (
        read_file, write_file, list_dir, edit_file, delete_file, file_search,
        codebase_search, grep_search, analyze_python_file,
        find_function_definition, list_all_functions,
    )

    # Crear agentes
    coder_agent = AssistantAgent(
        name="Coder",
        description="Especialista en tareas de codificacion simples",
        system_message="Eres un agente de codigo",
        model_client=model_client,
        tools=[read_file, write_file, list_dir],
        max_tool_iterations=5,
        reflect_on_tool_use=False,
    )

    planner = TaskPlanner(model_client)

    search_tools = [
        codebase_search, grep_search, file_search,
        read_file, list_dir,
        analyze_python_file, find_function_definition, list_all_functions,
    ]
    code_searcher = CodeSearcher(model_client, search_tools)

    # Crear el team
    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(30)

    team = SelectorGroupChat(
        participants=[
            code_searcher.searcher_agent,
            planner.planner_agent,
            coder_agent
        ],
        model_client=model_client,
        termination_condition=termination,
        selector_prompt="Selecciona el agente apropiado: {participants}",
    )

    # Verificar que el team tiene 3 agentes
    print(f"   [OK] Team creado con {len(team._participants)} agentes:")
    for i, agent in enumerate(team._participants, 1):
        print(f"     {i}. {agent.name}: {agent.description[:60]}...")

    # Verificar nombres de agentes
    agent_names = [agent.name for agent in team._participants]
    expected_agents = ["CodeSearcher", "Planner", "Coder"]

    print(f"\n[2] Verificando agentes esperados...")
    for expected in expected_agents:
        if expected in agent_names:
            print(f"   [OK] {expected} encontrado")
        else:
            print(f"   [ERROR] {expected} NO encontrado")
            await model_client.close()
            return False

    # Verificar que CodeSearcher tiene las herramientas correctas
    print(f"\n[3] Verificando herramientas de CodeSearcher...")
    code_searcher_agent = None
    for agent in team._participants:
        if agent.name == "CodeSearcher":
            code_searcher_agent = agent
            break

    if code_searcher_agent:
        tools = code_searcher_agent._tools if hasattr(code_searcher_agent, '_tools') else []
        print(f"   [OK] CodeSearcher tiene {len(tools)} herramientas")

    print(f"\n[4] Verificando selector_prompt...")
    if "participants" in team._selector_prompt:
        print(f"   [OK] Selector prompt configurado")
    else:
        print(f"   [ERROR] Selector prompt NO configurado")
        await model_client.close()
        return False

    print("\n" + "=" * 70)
    print("INTEGRACION EXITOSA")
    print("=" * 70)
    print("\nEl CodeSearcher esta correctamente integrado en el team.")
    print("El sistema ahora puede seleccionar automaticamente entre:")
    print("  - CodeSearcher - Para busqueda y analisis de codigo")
    print("  - Planner - Para tareas complejas con multiples pasos")
    print("  - Coder - Para tareas simples de codificacion")
    print("\nEjemplos de uso:")
    print("  'donde esta la funcion de autenticacion?' -> CodeSearcher")
    print("  'crea un sistema completo de usuarios' -> Planner")
    print("  'lee el archivo config.json' -> Coder")

    await model_client.close()
    return True


if __name__ == "__main__":
    success = asyncio.run(test_integration())
    exit(0 if success else 1)
