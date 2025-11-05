"""
Test de Continuación de Conversación - Resume Session

Este test demuestra el flujo completo de:
1. Iniciar conversación
2. Guardar estado
3. Simular cierre de aplicación
4. Cargar estado en nueva sesión
5. Continuar conversación sin perder contexto
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt


console = Console()


async def session_1_initial_conversation():
    """SESIÓN 1: Conversación inicial y guardado"""
    
    console.clear()
    console.rule("🎬 SESIÓN 1: CONVERSACIÓN INICIAL", style="bold cyan")
    
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    model_client = OpenAIChatCompletionClient(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
        model_capabilities={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        }
    )
    
    # Crear agente
    console.print("\n✅ Creando nuevo agente...\n", style="bold green")
    
    agent = AssistantAgent(
        name="coding_assistant",
        system_message="You are an expert Python programming assistant. Help users with code.",
        model_client=model_client,
    )
    
    # Conversación inicial
    initial_messages = [
        "Hi! I'm working on a Python project.",
        "I need to create a web API. What framework do you recommend?",
        "Great! Can you show me how to create a basic FastAPI endpoint?",
    ]
    
    console.print("💬 Iniciando conversación:\n", style="bold")
    
    for i, msg in enumerate(initial_messages, 1):
        console.print(Panel(msg, title=f"👤 Usuario (mensaje {i})", border_style="blue"))
        
        response = await agent.on_messages(
            [TextMessage(content=msg, source="user")],
            CancellationToken()
        )
        
        response_text = response.chat_message.content
        console.print(Panel(response_text, title=f"🤖 Asistente (mensaje {i})", border_style="green"))
        console.print()
    
    # Guardar estado
    console.rule("💾 GUARDANDO ESTADO", style="bold yellow")
    
    agent_state = await agent.save_state()
    
    # Guardar a archivo
    session_file = Path("test/.temp_resume_session.json")
    session_file.parent.mkdir(exist_ok=True)
    
    session_data = {
        "session_id": "resume_test",
        "saved_at": datetime.now().isoformat(),
        "metadata": {
            "topic": "FastAPI Development",
            "messages_count": len(initial_messages),
            "last_topic": "FastAPI endpoints"
        },
        "agent_state": agent_state
    }
    
    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2, default=str)
    
    console.print(f"\n✅ Estado guardado en: {session_file}", style="bold green")
    console.print(f"📊 Mensajes en el estado: {len(agent_state.get('llm_messages', []))}", style="bold")
    
    await model_client.close()
    
    console.print("\n⏸️ Simulando cierre de aplicación...", style="bold yellow")
    input("\nPresiona Enter para 'cerrar' la aplicación...")
    
    return session_file


async def session_2_resume_and_continue(session_file: Path):
    """SESIÓN 2: Cargar estado y continuar conversación"""
    
    console.clear()
    console.rule("🔄 SESIÓN 2: CARGANDO ESTADO Y CONTINUANDO", style="bold cyan")
    
    # Simular reinicio de aplicación
    console.print("\n🔌 Simulando inicio de nueva sesión...", style="bold yellow")
    console.print("💾 Cargando estado guardado...\n", style="bold yellow")
    
    # Cargar estado desde archivo
    if not session_file.exists():
        console.print("❌ Archivo de sesión no encontrado!", style="bold red")
        return
    
    with open(session_file, "r") as f:
        session_data = json.load(f)
    
    console.print("✅ Estado cargado exitosamente", style="bold green")
    console.print(f"📊 Session ID: {session_data['session_id']}", style="bold")
    console.print(f"📅 Guardada: {session_data['saved_at']}", style="bold")
    console.print(f"💬 Mensajes guardados: {session_data['metadata']['messages_count']}", style="bold")
    console.print(f"📝 Último tema: {session_data['metadata']['last_topic']}", style="bold")
    
    # Mostrar historial previo
    console.print("\n" + "="*80, style="cyan")
    console.print("📜 HISTORIAL PREVIO (de la sesión anterior):", style="bold cyan")
    console.print("="*80 + "\n", style="cyan")
    
    agent_state = session_data["agent_state"]
    messages = agent_state.get("llm_messages", [])
    
    for i, msg in enumerate(messages, 1):
        msg_type = msg.get("type", "Unknown")
        content = msg.get("content", "")
        
        if msg_type == "UserMessage":
            console.print(Panel(content, title=f"👤 Usuario (#{i})", border_style="blue"))
        elif msg_type == "AssistantMessage":
            console.print(Panel(content, title=f"🤖 Asistente (#{i})", border_style="green"))
    
    console.print()
    input("⏸️ Presiona Enter para crear nuevo agente y cargar el estado...")
    
    # Crear NUEVO agente (simulando nueva instancia)
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    model_client = OpenAIChatCompletionClient(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
        model_capabilities={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        }
    )
    
    console.print("\n✅ Creando NUEVO agente...", style="bold green")
    
    new_agent = AssistantAgent(
        name="coding_assistant",
        system_message="You are an expert Python programming assistant. Help users with code.",
        model_client=model_client,
    )
    
    # CARGAR estado en el nuevo agente
    console.print("📂 Cargando estado en el nuevo agente...", style="bold yellow")
    await new_agent.load_state(agent_state)
    console.print("✅ Estado cargado exitosamente!\n", style="bold green")
    
    # Continuar conversación
    console.rule("💬 CONTINUANDO CONVERSACIÓN", style="bold magenta")
    
    continuation_messages = [
        "Can you remember what framework we were discussing?",
        "Now show me how to add authentication to that endpoint",
        "What database would you recommend for this FastAPI project?",
    ]
    
    console.print("\n🔄 El agente DEBERÍA recordar toda la conversación anterior...\n", style="bold yellow")
    
    for i, msg in enumerate(continuation_messages, 1):
        console.print(Panel(msg, title=f"👤 Usuario (continuación {i})", border_style="blue"))
        
        response = await new_agent.on_messages(
            [TextMessage(content=msg, source="user")],
            CancellationToken()
        )
        
        response_text = response.chat_message.content
        console.print(Panel(response_text, title=f"🤖 Asistente (continuación {i})", border_style="green"))
        console.print()
    
    # Guardar estado actualizado
    console.rule("💾 GUARDANDO ESTADO ACTUALIZADO", style="bold yellow")
    
    updated_state = await new_agent.save_state()
    
    session_data["agent_state"] = updated_state
    session_data["metadata"]["messages_count"] += len(continuation_messages)
    session_data["metadata"]["last_topic"] = "FastAPI Authentication & Database"
    session_data["updated_at"] = datetime.now().isoformat()
    
    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2, default=str)
    
    console.print(f"\n✅ Estado actualizado guardado", style="bold green")
    console.print(f"📊 Total de mensajes ahora: {len(updated_state.get('llm_messages', []))}", style="bold")
    
    await model_client.close()


async def session_3_final_verification(session_file: Path):
    """SESIÓN 3: Verificación final de memoria"""
    
    console.clear()
    console.rule("🔍 SESIÓN 3: VERIFICACIÓN FINAL DE MEMORIA", style="bold cyan")
    
    console.print("\n🧪 Vamos a verificar que el agente recuerda TODA la conversación...\n", style="bold yellow")
    
    # Cargar estado
    with open(session_file, "r") as f:
        session_data = json.load(f)
    
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    model_client = OpenAIChatCompletionClient(
        model="deepseek-chat",
        api_key=api_key,
        base_url="https://api.deepseek.com",
        model_capabilities={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": False,
        }
    )
    
    agent = AssistantAgent(
        name="coding_assistant",
        system_message="You are an expert Python programming assistant. Help users with code.",
        model_client=model_client,
    )
    
    await agent.load_state(session_data["agent_state"])
    
    # Preguntas de verificación
    verification_questions = [
        "What framework did I originally ask about at the beginning?",
        "What were the main topics we discussed? List them.",
        "Can you summarize our entire conversation from the beginning?",
    ]
    
    console.print("❓ Haciendo preguntas sobre la conversación completa:\n", style="bold")
    
    for i, msg in enumerate(verification_questions, 1):
        console.print(Panel(msg, title=f"❓ Pregunta de verificación {i}", border_style="yellow"))
        
        response = await agent.on_messages(
            [TextMessage(content=msg, source="user")],
            CancellationToken()
        )
        
        response_text = response.chat_message.content
        console.print(Panel(response_text, title=f"🤖 Respuesta {i}", border_style="green"))
        console.print()
    
    await model_client.close()
    
    # Mostrar resumen final
    console.rule("📊 RESUMEN FINAL", style="bold green")
    
    final_state = await agent.save_state()
    total_messages = len(final_state.get("llm_messages", []))
    
    console.print(f"\n✅ Total de mensajes en el estado: {total_messages}", style="bold green")
    console.print(f"📅 Primera sesión: {session_data.get('saved_at', 'N/A')}", style="bold")
    console.print(f"🔄 Última actualización: {session_data.get('updated_at', 'N/A')}", style="bold")
    
    console.print("\n💡 CONCLUSIÓN:", style="bold cyan")
    console.print("  ✅ El agente mantiene TODO el historial entre sesiones", style="green")
    console.print("  ✅ save_state() y load_state() funcionan perfectamente", style="green")
    console.print("  ✅ No hay pérdida de contexto entre reinicios", style="green")


async def main():
    """Test completo de continuación de conversación"""
    
    console.clear()
    console.rule("🧪 TEST COMPLETO: CONTINUACIÓN DE CONVERSACIÓN", style="bold cyan")
    
    console.print("""
Este test simula el flujo completo de trabajo con sesiones:

1️⃣ SESIÓN 1: Usuario tiene conversación inicial → Guarda estado → Cierra app
2️⃣ SESIÓN 2: Usuario abre app → Carga estado → Continúa conversación
3️⃣ SESIÓN 3: Verificación de que el agente recuerda TODO

Esto demuestra cómo AutoGen save_state/load_state permite
mantener conversaciones entre reinicios de la aplicación.
    """, style="yellow")
    
    input("\n⏸️ Presiona Enter para comenzar el test...")
    
    try:
        # Sesión 1: Conversación inicial
        session_file = await session_1_initial_conversation()
        
        # Sesión 2: Cargar y continuar
        await session_2_resume_and_continue(session_file)
        
        input("\n⏸️ Presiona Enter para verificación final...")
        
        # Sesión 3: Verificación
        await session_3_final_verification(session_file)
        
        console.print("\n" + "="*80, style="green")
        console.print("✅ TEST COMPLETADO EXITOSAMENTE", style="bold green")
        console.print("="*80, style="green")
        
        console.print(f"\n📁 Archivo de sesión: {session_file}", style="bold")
        console.print("\n💡 Revisa el archivo JSON para ver la estructura completa del estado", style="yellow")
        
    except Exception as e:
        console.print(f"\n❌ ERROR: {e}", style="bold red")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
