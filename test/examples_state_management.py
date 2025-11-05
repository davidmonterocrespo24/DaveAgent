"""
Ejemplos Prácticos de AutoGen State Management

Este archivo contiene código que puedes copiar y pegar directamente
en tu aplicación para implementar gestión de sesiones.
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient


# =============================================================================
# EJEMPLO 1: Guardar y Cargar Estado Básico
# =============================================================================

async def example_1_basic_save_load():
    """Ejemplo básico de save/load state"""
    
    # Configurar agente
    model_client = OpenAIChatCompletionClient(
        model="deepseek-chat",
        api_key="your_api_key",
        base_url="https://api.deepseek.com"
    )
    
    agent = AssistantAgent(
        name="assistant",
        system_message="You are a helpful assistant.",
        model_client=model_client,
    )
    
    # Tener conversación
    await agent.on_messages(
        [TextMessage(content="Hello!", source="user")],
        CancellationToken()
    )
    
    # GUARDAR ESTADO
    agent_state = await agent.save_state()
    
    # Guardar a archivo
    with open("my_session.json", "w") as f:
        json.dump(agent_state, f, indent=2, default=str)
    
    print("✅ Estado guardado en my_session.json")
    
    # --- Más tarde, en una nueva sesión ---
    
    # CARGAR ESTADO
    with open("my_session.json", "r") as f:
        loaded_state = json.load(f)
    
    # Crear nuevo agente y cargar estado
    new_agent = AssistantAgent(
        name="assistant",
        system_message="You are a helpful assistant.",
        model_client=model_client,
    )
    
    await new_agent.load_state(loaded_state)
    
    # Continuar conversación
    response = await new_agent.on_messages(
        [TextMessage(content="Do you remember me?", source="user")],
        CancellationToken()
    )
    
    print(f"🤖 {response.chat_message.content}")
    
    await model_client.close()


# =============================================================================
# EJEMPLO 2: Gestor de Sesiones Simple
# =============================================================================

class SimpleSessionManager:
    """Gestor de sesiones minimalista"""
    
    def __init__(self, sessions_dir: str = ".sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
    
    def save_session(self, session_id: str, agent_state: dict) -> Path:
        """Guarda una sesión"""
        session_file = self.sessions_dir / f"{session_id}.json"
        
        data = {
            "session_id": session_id,
            "saved_at": datetime.now().isoformat(),
            "state": agent_state
        }
        
        with open(session_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        return session_file
    
    def load_session(self, session_id: str) -> dict:
        """Carga una sesión"""
        session_file = self.sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            raise FileNotFoundError(f"Sesión no encontrada: {session_id}")
        
        with open(session_file, "r") as f:
            data = json.load(f)
        
        return data["state"]
    
    def list_sessions(self) -> List[str]:
        """Lista sesiones disponibles"""
        return [f.stem for f in self.sessions_dir.glob("*.json")]


async def example_2_session_manager():
    """Ejemplo usando SimpleSessionManager"""
    
    manager = SimpleSessionManager()
    
    # Crear agente y sesión
    model_client = OpenAIChatCompletionClient(
        model="deepseek-chat",
        api_key="your_api_key",
        base_url="https://api.deepseek.com"
    )
    
    agent = AssistantAgent(
        name="assistant",
        system_message="You are helpful.",
        model_client=model_client,
    )
    
    # Conversación
    await agent.on_messages(
        [TextMessage(content="Help me with Python", source="user")],
        CancellationToken()
    )
    
    # Guardar
    state = await agent.save_state()
    manager.save_session("python_help", state)
    
    # Listar sesiones
    print("Sesiones:", manager.list_sessions())
    
    # Cargar más tarde
    loaded_state = manager.load_session("python_help")
    
    new_agent = AssistantAgent(
        name="assistant",
        system_message="You are helpful.",
        model_client=model_client,
    )
    
    await new_agent.load_state(loaded_state)
    
    await model_client.close()


# =============================================================================
# EJEMPLO 3: Extraer y Mostrar Historial
# =============================================================================

def extract_conversation_history(agent_state: dict) -> List[Dict]:
    """Extrae el historial de mensajes del estado"""
    
    messages = agent_state.get("llm_messages", [])
    
    conversation = []
    for msg in messages:
        conversation.append({
            "type": msg.get("type"),
            "content": msg.get("content"),
            "source": msg.get("source"),
        })
    
    return conversation


def display_conversation(agent_state: dict):
    """Muestra el historial de conversación en consola"""
    
    messages = agent_state.get("llm_messages", [])
    
    print("\n" + "=" * 80)
    print(f"📜 HISTORIAL ({len(messages)} mensajes)")
    print("=" * 80 + "\n")
    
    for i, msg in enumerate(messages, 1):
        msg_type = msg.get("type")
        content = msg.get("content")
        
        if msg_type == "UserMessage":
            print(f"[{i}] 👤 Usuario:")
            print(f"    {content}\n")
        elif msg_type == "AssistantMessage":
            print(f"[{i}] 🤖 Asistente:")
            print(f"    {content}\n")


def example_3_display_history():
    """Ejemplo de visualización de historial"""
    
    # Cargar estado desde archivo
    with open("my_session.json", "r") as f:
        agent_state = json.load(f)
    
    # Mostrar historial
    display_conversation(agent_state)
    
    # Extraer historial
    history = extract_conversation_history(agent_state)
    
    print(f"Total: {len(history)} mensajes")
    for msg in history:
        print(f"- {msg['type']}: {msg['content'][:50]}...")


# =============================================================================
# EJEMPLO 4: Auto-Save Periódico
# =============================================================================

class AutoSaveAgent:
    """Wrapper de agente con auto-save"""
    
    def __init__(
        self,
        agent: AssistantAgent,
        session_id: str,
        save_dir: str = ".autosave"
    ):
        self.agent = agent
        self.session_id = session_id
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        self.message_count = 0
    
    async def on_messages(self, messages, token):
        """Envía mensaje y auto-guarda"""
        
        # Procesar mensaje
        response = await self.agent.on_messages(messages, token)
        
        # Auto-save después de cada mensaje
        self.message_count += 1
        await self._auto_save()
        
        return response
    
    async def _auto_save(self):
        """Guarda estado automáticamente"""
        
        state = await self.agent.save_state()
        
        save_file = self.save_dir / f"{self.session_id}.json"
        
        data = {
            "session_id": self.session_id,
            "saved_at": datetime.now().isoformat(),
            "message_count": self.message_count,
            "state": state
        }
        
        with open(save_file, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"💾 Auto-saved (mensajes: {self.message_count})")


async def example_4_autosave():
    """Ejemplo de auto-save"""
    
    model_client = OpenAIChatCompletionClient(
        model="deepseek-chat",
        api_key="your_api_key",
        base_url="https://api.deepseek.com"
    )
    
    agent = AssistantAgent(
        name="assistant",
        system_message="You are helpful.",
        model_client=model_client,
    )
    
    # Wrap con auto-save
    autosave_agent = AutoSaveAgent(agent, session_id="my_work")
    
    # Cada mensaje se guarda automáticamente
    await autosave_agent.on_messages(
        [TextMessage(content="Msg 1", source="user")],
        CancellationToken()
    )
    # 💾 Auto-saved
    
    await autosave_agent.on_messages(
        [TextMessage(content="Msg 2", source="user")],
        CancellationToken()
    )
    # 💾 Auto-saved
    
    await model_client.close()


# =============================================================================
# EJEMPLO 5: Buscar en Historial
# =============================================================================

def search_in_history(agent_state: dict, query: str) -> List[Dict]:
    """Busca un término en el historial"""
    
    messages = agent_state.get("llm_messages", [])
    results = []
    
    query_lower = query.lower()
    
    for i, msg in enumerate(messages, 1):
        content = msg.get("content", "").lower()
        
        if query_lower in content:
            results.append({
                "index": i,
                "type": msg.get("type"),
                "content": msg.get("content"),
                "source": msg.get("source")
            })
    
    return results


def example_5_search():
    """Ejemplo de búsqueda en historial"""
    
    # Cargar estado
    with open("my_session.json", "r") as f:
        agent_state = json.load(f)
    
    # Buscar término
    results = search_in_history(agent_state, "python")
    
    print(f"Encontrados {len(results)} mensajes con 'python':\n")
    
    for result in results:
        print(f"[{result['index']}] {result['type']}:")
        print(f"    {result['content'][:100]}...\n")


# =============================================================================
# EJEMPLO 6: Estadísticas de Sesión
# =============================================================================

def get_session_statistics(agent_state: dict) -> Dict:
    """Obtiene estadísticas de la sesión"""
    
    messages = agent_state.get("llm_messages", [])
    
    user_msgs = [m for m in messages if m.get("type") == "UserMessage"]
    assistant_msgs = [m for m in messages if m.get("type") == "AssistantMessage"]
    
    return {
        "total_messages": len(messages),
        "user_messages": len(user_msgs),
        "assistant_messages": len(assistant_msgs),
        "total_user_chars": sum(len(m.get("content", "")) for m in user_msgs),
        "total_assistant_chars": sum(len(m.get("content", "")) for m in assistant_msgs),
        "avg_user_length": sum(len(m.get("content", "")) for m in user_msgs) / len(user_msgs) if user_msgs else 0,
        "avg_assistant_length": sum(len(m.get("content", "")) for m in assistant_msgs) / len(assistant_msgs) if assistant_msgs else 0,
    }


def example_6_statistics():
    """Ejemplo de estadísticas"""
    
    with open("my_session.json", "r") as f:
        agent_state = json.load(f)
    
    stats = get_session_statistics(agent_state)
    
    print("📊 Estadísticas de la Sesión:")
    print(f"  Total mensajes: {stats['total_messages']}")
    print(f"  Usuario: {stats['user_messages']} mensajes")
    print(f"  Asistente: {stats['assistant_messages']} mensajes")
    print(f"  Promedio chars usuario: {stats['avg_user_length']:.0f}")
    print(f"  Promedio chars asistente: {stats['avg_assistant_length']:.0f}")


# =============================================================================
# EJEMPLO 7: CLI Interactiva con Sesiones
# =============================================================================

class SessionCLI:
    """CLI interactiva con gestión de sesiones"""
    
    def __init__(self, sessions_dir: str = ".sessions"):
        self.manager = SimpleSessionManager(sessions_dir)
        self.current_session = None
        self.agent = None
        self.model_client = None
    
    async def start(self):
        """Inicia la CLI"""
        
        print("🤖 Session CLI - AutoGen State Management")
        print("\nComandos:")
        print("  /new <session_id> - Nueva sesión")
        print("  /load <session_id> - Cargar sesión")
        print("  /list - Listar sesiones")
        print("  /save - Guardar sesión actual")
        print("  /history - Ver historial")
        print("  /exit - Salir")
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.startswith("/"):
                    await self._handle_command(user_input)
                else:
                    await self._send_message(user_input)
                    
            except (EOFError, KeyboardInterrupt):
                break
        
        if self.model_client:
            await self.model_client.close()
    
    async def _handle_command(self, command: str):
        """Maneja comandos"""
        
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else None
        
        if cmd == "/new":
            if not arg:
                print("Uso: /new <session_id>")
                return
            
            await self._new_session(arg)
        
        elif cmd == "/load":
            if not arg:
                print("Uso: /load <session_id>")
                return
            
            await self._load_session(arg)
        
        elif cmd == "/list":
            sessions = self.manager.list_sessions()
            print(f"\n📋 Sesiones ({len(sessions)}):")
            for s in sessions:
                print(f"  - {s}")
        
        elif cmd == "/save":
            if self.agent:
                state = await self.agent.save_state()
                self.manager.save_session(self.current_session, state)
                print(f"✅ Sesión '{self.current_session}' guardada")
            else:
                print("⚠️ No hay sesión activa")
        
        elif cmd == "/history":
            if self.agent:
                state = await self.agent.save_state()
                display_conversation(state)
            else:
                print("⚠️ No hay sesión activa")
        
        elif cmd == "/exit":
            raise EOFError()
    
    async def _new_session(self, session_id: str):
        """Crea nueva sesión"""
        
        if self.model_client:
            await self.model_client.close()
        
        self.model_client = OpenAIChatCompletionClient(
            model="deepseek-chat",
            api_key="your_api_key",
            base_url="https://api.deepseek.com"
        )
        
        self.agent = AssistantAgent(
            name="assistant",
            system_message="You are a helpful assistant.",
            model_client=self.model_client,
        )
        
        self.current_session = session_id
        print(f"✅ Nueva sesión creada: {session_id}")
    
    async def _load_session(self, session_id: str):
        """Carga sesión existente"""
        
        try:
            state = self.manager.load_session(session_id)
            
            if self.model_client:
                await self.model_client.close()
            
            self.model_client = OpenAIChatCompletionClient(
                model="deepseek-chat",
                api_key="your_api_key",
                base_url="https://api.deepseek.com"
            )
            
            self.agent = AssistantAgent(
                name="assistant",
                system_message="You are a helpful assistant.",
                model_client=self.model_client,
            )
            
            await self.agent.load_state(state)
            
            self.current_session = session_id
            print(f"✅ Sesión cargada: {session_id}")
            
            # Mostrar historial
            display_conversation(state)
            
        except FileNotFoundError as e:
            print(f"❌ {e}")
    
    async def _send_message(self, message: str):
        """Envía mensaje al agente"""
        
        if not self.agent:
            print("⚠️ Crea o carga una sesión primero (/new o /load)")
            return
        
        response = await self.agent.on_messages(
            [TextMessage(content=message, source="user")],
            CancellationToken()
        )
        
        print(f"\n🤖 {response.chat_message.content}")
        
        # Auto-save
        state = await self.agent.save_state()
        self.manager.save_session(self.current_session, state)


async def example_7_cli():
    """Ejemplo de CLI interactiva"""
    
    cli = SessionCLI()
    await cli.start()


# =============================================================================
# MAIN - Ejecutar ejemplos
# =============================================================================

async def main():
    """Ejecuta los ejemplos"""
    
    print("Selecciona un ejemplo:")
    print("1. Básico save/load")
    print("2. Session Manager")
    print("3. Mostrar historial")
    print("4. Auto-save")
    print("5. Buscar en historial")
    print("6. Estadísticas")
    print("7. CLI Interactiva")
    
    choice = input("\nEjemplo (1-7): ").strip()
    
    if choice == "1":
        await example_1_basic_save_load()
    elif choice == "2":
        await example_2_session_manager()
    elif choice == "3":
        example_3_display_history()
    elif choice == "4":
        await example_4_autosave()
    elif choice == "5":
        example_5_search()
    elif choice == "6":
        example_6_statistics()
    elif choice == "7":
        await example_7_cli()
    else:
        print("Opción inválida")


if __name__ == "__main__":
    asyncio.run(main())
