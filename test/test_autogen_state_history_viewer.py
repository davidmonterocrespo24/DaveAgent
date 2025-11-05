"""
Test de Visualización de Historial - UI Console Display

Este test demuestra cómo mostrar el historial de mensajes en consola
de forma amigable, similar a como lo haría una UI de chat.
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
from rich.markdown import Markdown
from rich.table import Table


class HistoryViewer:
    """Visualizador de historial de conversación"""
    
    def __init__(self):
        self.console = Console()
    
    def display_message(self, msg_type: str, source: str, content: str, index: int):
        """Muestra un mensaje formateado"""
        
        if msg_type == "UserMessage":
            # Mensaje del usuario
            self.console.print(
                Panel(
                    content,
                    title=f"👤 Usuario (#{index})",
                    border_style="blue",
                    padding=(1, 2)
                )
            )
        elif msg_type == "AssistantMessage":
            # Mensaje del asistente
            self.console.print(
                Panel(
                    Markdown(content),
                    title=f"🤖 Asistente (#{index})",
                    border_style="green",
                    padding=(1, 2)
                )
            )
        else:
            # Otros mensajes
            self.console.print(
                Panel(
                    content[:200] + "..." if len(content) > 200 else content,
                    title=f"⚙️ {msg_type} - {source} (#{index})",
                    border_style="yellow",
                    padding=(1, 2)
                )
            )
    
    def display_session_info(self, session_data: dict):
        """Muestra información de la sesión"""
        
        table = Table(title="📊 Información de la Sesión", show_header=True)
        table.add_column("Campo", style="cyan")
        table.add_column("Valor", style="green")
        
        table.add_row("Session ID", session_data.get("session_id", "N/A"))
        table.add_row("Guardada", session_data.get("saved_at", "N/A"))
        
        metadata = session_data.get("metadata", {})
        for key, value in metadata.items():
            table.add_row(key, str(value))
        
        self.console.print(table)
    
    def display_message_list(self, messages: list):
        """Muestra lista de mensajes"""
        
        table = Table(title="📜 Lista de Mensajes", show_header=True)
        table.add_column("#", style="cyan", width=5)
        table.add_column("Tipo", style="yellow", width=20)
        table.add_column("Source", style="blue", width=15)
        table.add_column("Preview", style="white")
        
        for i, msg in enumerate(messages, 1):
            msg_type = msg.get("type", "Unknown")
            source = msg.get("source", "Unknown")
            content = str(msg.get("content", ""))
            preview = content[:60] + "..." if len(content) > 60 else content
            
            table.add_row(str(i), msg_type, source, preview)
        
        self.console.print(table)
    
    def display_conversation_history(self, agent_state: dict, session_data: dict = None):
        """Muestra todo el historial de conversación de forma amigable"""
        
        self.console.clear()
        self.console.rule("📜 HISTORIAL DE CONVERSACIÓN", style="bold blue")
        
        # Mostrar info de sesión si está disponible
        if session_data:
            self.console.print()
            self.display_session_info(session_data)
        
        # Extraer mensajes
        if "llm_messages" not in agent_state:
            self.console.print("\n⚠️ No se encontraron mensajes en el estado", style="yellow")
            return
        
        messages = agent_state["llm_messages"]
        
        self.console.print(f"\n✅ Total de mensajes: {len(messages)}", style="bold green")
        
        # Mostrar lista resumida
        self.console.print()
        self.display_message_list(messages)
        
        # Preguntar si quiere ver mensajes completos
        self.console.print()
        self.console.print("💬 Mostrando conversación completa:", style="bold")
        self.console.print()
        
        # Mostrar cada mensaje formateado
        for i, msg in enumerate(messages, 1):
            msg_type = msg.get("type", "Unknown")
            source = msg.get("source", "Unknown")
            content = str(msg.get("content", ""))
            
            self.display_message(msg_type, source, content, i)
            self.console.print()  # Espacio entre mensajes
        
        self.console.rule("✅ FIN DEL HISTORIAL", style="bold green")


async def test_history_visualization():
    """Test de visualización de historial"""
    
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        print("❌ ERROR: DEEPSEEK_API_KEY no encontrada en .env")
        return
    
    viewer = HistoryViewer()
    viewer.console.clear()
    viewer.console.rule("🧪 TEST DE VISUALIZACIÓN DE HISTORIAL", style="bold cyan")
    
    # =========================================================================
    # PASO 1: Crear una conversación
    # =========================================================================
    viewer.console.print("\n📝 PASO 1: Creando conversación de ejemplo...\n")
    
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
        name="assistant",
        system_message="You are a helpful coding assistant. Provide clear, concise answers.",
        model_client=model_client,
    )
    
    # Conversación de ejemplo
    conversation = [
        "Hi! I need help with Python decorators.",
        "Can you explain what they are?",
        "Show me a simple example.",
        "How can I create my own decorator?",
        "Thanks! Can you show a real-world use case?"
    ]
    
    for msg in conversation:
        response = await agent.on_messages(
            [TextMessage(content=msg, source="user")],
            CancellationToken()
        )
    
    # Guardar estado
    agent_state = await agent.save_state()
    
    # Crear session data
    session_data = {
        "session_id": "demo_visualization",
        "saved_at": datetime.now().isoformat(),
        "metadata": {
            "topic": "Python Decorators",
            "num_messages": len(conversation),
            "language": "Python"
        }
    }
    
    # =========================================================================
    # PASO 2: Visualizar el historial
    # =========================================================================
    input("\n⏸️ Presiona Enter para ver el historial completo...")
    
    viewer.display_conversation_history(agent_state, session_data)
    
    # =========================================================================
    # PASO 3: Mostrar estructura del estado
    # =========================================================================
    input("\n⏸️ Presiona Enter para ver la estructura del estado...")
    
    viewer.console.clear()
    viewer.console.rule("🔍 ESTRUCTURA DEL ESTADO", style="bold cyan")
    
    viewer.console.print("\n📊 Estructura JSON del estado:\n", style="bold")
    viewer.console.print_json(json.dumps(agent_state, default=str))
    
    # Guardar para inspección
    output_file = Path("test/.temp_history_example.json")
    with open(output_file, "w") as f:
        json.dump({
            "session_data": session_data,
            "agent_state": agent_state
        }, f, indent=2, default=str)
    
    viewer.console.print(f"\n✅ Estado guardado en: {output_file}", style="bold green")
    
    await model_client.close()


async def test_load_and_display():
    """Test de cargar sesión existente y mostrar historial"""
    
    load_dotenv()
    viewer = HistoryViewer()
    
    # Buscar sesiones en directorio de prueba
    sessions_dir = Path("test/.temp_sessions")
    
    if not sessions_dir.exists() or not list(sessions_dir.glob("*.json")):
        viewer.console.print(
            "\n⚠️ No hay sesiones guardadas. Ejecuta primero test_autogen_state_sessions.py",
            style="yellow"
        )
        return
    
    viewer.console.clear()
    viewer.console.rule("📂 CARGANDO Y VISUALIZANDO SESIÓN", style="bold cyan")
    
    # Listar sesiones disponibles
    viewer.console.print("\n📋 Sesiones disponibles:\n", style="bold")
    
    sessions = []
    for session_file in sessions_dir.glob("session_*.json"):
        with open(session_file, "r") as f:
            data = json.load(f)
            sessions.append(data)
            viewer.console.print(f"  • {data['session_id']} ({data['saved_at']})")
    
    if not sessions:
        viewer.console.print("\n⚠️ No se encontraron sesiones válidas", style="yellow")
        return
    
    # Cargar primera sesión
    viewer.console.print(f"\n📂 Cargando sesión: {sessions[0]['session_id']}", style="bold green")
    
    input("\n⏸️ Presiona Enter para visualizar...")
    
    # Visualizar
    viewer.display_conversation_history(
        sessions[0]["agent_state"],
        sessions[0]
    )


async def main():
    """Ejecutar tests de visualización"""
    
    try:
        # Test 1: Crear y visualizar
        await test_history_visualization()
        
        # Test 2: Cargar y visualizar sesiones existentes
        input("\n⏸️ Presiona Enter para probar carga de sesiones existentes...")
        await test_load_and_display()
        
        print("\n✅ Tests de visualización completados")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
