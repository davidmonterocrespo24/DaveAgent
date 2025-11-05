"""
Test de Sesiones Múltiples - Simula flujo de trabajo real

Este test demuestra:
1. Crear múltiples sesiones de conversación
2. Guardar cada sesión con un ID único
3. Listar todas las sesiones guardadas
4. Cargar una sesión específica
5. Continuar conversación desde sesión cargada
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
from typing import Dict, List


class SessionManager:
    """Gestor de sesiones para pruebas"""
    
    def __init__(self, sessions_dir: Path):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def save_session(self, session_id: str, agent_state: dict, metadata: dict = None):
        """Guarda una sesión con metadata"""
        session_data = {
            "session_id": session_id,
            "saved_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "agent_state": agent_state
        }
        
        session_file = self.sessions_dir / f"session_{session_id}.json"
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2, default=str)
        
        return session_file
    
    def load_session(self, session_id: str) -> dict:
        """Carga una sesión"""
        session_file = self.sessions_dir / f"session_{session_id}.json"
        
        if not session_file.exists():
            raise FileNotFoundError(f"Sesión no encontrada: {session_id}")
        
        with open(session_file, "r") as f:
            return json.load(f)
    
    def list_sessions(self) -> List[Dict]:
        """Lista todas las sesiones guardadas"""
        sessions = []
        
        for session_file in self.sessions_dir.glob("session_*.json"):
            try:
                with open(session_file, "r") as f:
                    data = json.load(f)
                
                sessions.append({
                    "session_id": data.get("session_id"),
                    "saved_at": data.get("saved_at"),
                    "metadata": data.get("metadata", {}),
                    "file_path": str(session_file)
                })
            except Exception as e:
                print(f"⚠️ Error leyendo {session_file}: {e}")
        
        # Ordenar por fecha
        sessions.sort(key=lambda x: x.get("saved_at", ""), reverse=True)
        return sessions
    
    def delete_session(self, session_id: str):
        """Elimina una sesión"""
        session_file = self.sessions_dir / f"session_{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            return True
        return False


async def create_conversation_session(
    session_id: str,
    conversations: List[str],
    model_client,
    session_manager: SessionManager
):
    """Crea una sesión de conversación completa"""
    
    print(f"\n{'='*80}")
    print(f"📝 CREANDO SESIÓN: {session_id}")
    print(f"{'='*80}")
    
    # Crear agente
    agent = AssistantAgent(
        name="assistant",
        system_message="You are a helpful assistant. Be concise.",
        model_client=model_client,
    )
    
    # Tener conversación
    responses = []
    for i, msg in enumerate(conversations, 1):
        print(f"\n[{i}/{len(conversations)}] 👤 Usuario: {msg}")
        
        response = await agent.on_messages(
            [TextMessage(content=msg, source="user")],
            CancellationToken()
        )
        
        response_text = response.chat_message.content
        responses.append(response_text)
        print(f"[{i}/{len(conversations)}] 🤖 Agente: {response_text}")
    
    # Guardar estado
    agent_state = await agent.save_state()
    
    # Guardar sesión con metadata
    metadata = {
        "num_messages": len(conversations),
        "last_user_message": conversations[-1],
        "last_agent_response": responses[-1]
    }
    
    session_file = session_manager.save_session(session_id, agent_state, metadata)
    print(f"\n✅ Sesión guardada: {session_file}")
    
    return agent_state


async def load_and_continue_session(
    session_id: str,
    continuation_messages: List[str],
    model_client,
    session_manager: SessionManager
):
    """Carga una sesión y continúa la conversación"""
    
    print(f"\n{'='*80}")
    print(f"📂 CARGANDO SESIÓN: {session_id}")
    print(f"{'='*80}")
    
    # Cargar sesión
    session_data = session_manager.load_session(session_id)
    agent_state = session_data["agent_state"]
    
    print(f"\n📊 Metadata de la sesión:")
    print(f"  - Guardada: {session_data['saved_at']}")
    print(f"  - Mensajes: {session_data['metadata'].get('num_messages', 'N/A')}")
    print(f"  - Último mensaje: {session_data['metadata'].get('last_user_message', 'N/A')}")
    
    # Crear nuevo agente
    new_agent = AssistantAgent(
        name="assistant",
        system_message="You are a helpful assistant. Be concise.",
        model_client=model_client,
    )
    
    # Cargar estado
    await new_agent.load_state(agent_state)
    print("\n✅ Estado cargado exitosamente")
    
    # Continuar conversación
    print(f"\n{'='*80}")
    print("💬 CONTINUANDO CONVERSACIÓN")
    print(f"{'='*80}")
    
    for i, msg in enumerate(continuation_messages, 1):
        print(f"\n[{i}/{len(continuation_messages)}] 👤 Usuario: {msg}")
        
        response = await new_agent.on_messages(
            [TextMessage(content=msg, source="user")],
            CancellationToken()
        )
        
        response_text = response.chat_message.content
        print(f"[{i}/{len(continuation_messages)}] 🤖 Agente: {response_text}")
    
    # Guardar estado actualizado
    updated_state = await new_agent.save_state()
    session_manager.save_session(
        session_id,
        updated_state,
        metadata={
            "num_messages": session_data["metadata"]["num_messages"] + len(continuation_messages),
            "last_user_message": continuation_messages[-1],
            "updated_at": datetime.now().isoformat()
        }
    )
    
    print(f"\n✅ Sesión actualizada: {session_id}")


async def display_session_history(session_id: str, session_manager: SessionManager):
    """Muestra todo el historial de una sesión"""
    
    print(f"\n{'='*80}")
    print(f"📜 HISTORIAL DE SESIÓN: {session_id}")
    print(f"{'='*80}")
    
    # Cargar sesión
    session_data = session_manager.load_session(session_id)
    agent_state = session_data["agent_state"]
    
    # Extraer mensajes
    if "llm_messages" in agent_state:
        messages = agent_state["llm_messages"]
        
        print(f"\n📊 Total de mensajes: {len(messages)}")
        print(f"📅 Sesión guardada: {session_data['saved_at']}")
        
        print(f"\n{'='*80}")
        print("💬 HISTORIAL COMPLETO")
        print(f"{'='*80}")
        
        for i, msg in enumerate(messages, 1):
            msg_type = msg.get("type", "Unknown")
            source = msg.get("source", "Unknown")
            content = msg.get("content", "")
            
            # Formatear según tipo
            if msg_type == "UserMessage":
                print(f"\n[{i}] 👤 Usuario:")
                print(f"    {content}")
            elif msg_type == "AssistantMessage":
                print(f"\n[{i}] 🤖 Asistente:")
                print(f"    {content}")
            else:
                print(f"\n[{i}] ⚙️ {msg_type} ({source}):")
                print(f"    {str(content)[:200]}...")
    else:
        print("⚠️ No se encontraron mensajes en el estado")


async def main():
    """Test completo de sesiones múltiples"""
    
    print("\n" + "="*80)
    print("🧪 TEST DE SESIONES MÚLTIPLES - AUTOGEN STATE MANAGEMENT")
    print("="*80)
    
    # Setup
    load_dotenv()
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        print("❌ ERROR: DEEPSEEK_API_KEY no encontrada en .env")
        return
    
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
    
    session_manager = SessionManager(Path("test/.temp_sessions"))
    
    try:
        # =====================================================================
        # ESCENARIO 1: Crear sesión de trabajo de Python
        # =====================================================================
        await create_conversation_session(
            session_id="python_work",
            conversations=[
                "I'm learning Python. Can you help me?",
                "What is a list comprehension?",
                "Can you give me an example?"
            ],
            model_client=model_client,
            session_manager=session_manager
        )
        
        # =====================================================================
        # ESCENARIO 2: Crear sesión de trabajo de JavaScript
        # =====================================================================
        await create_conversation_session(
            session_id="javascript_work",
            conversations=[
                "I need help with JavaScript",
                "What are arrow functions?",
                "Show me async/await syntax"
            ],
            model_client=model_client,
            session_manager=session_manager
        )
        
        # =====================================================================
        # ESCENARIO 3: Crear sesión personal
        # =====================================================================
        await create_conversation_session(
            session_id="personal_chat",
            conversations=[
                "Hello! My name is David",
                "I live in Colombia",
                "I enjoy coding and coffee"
            ],
            model_client=model_client,
            session_manager=session_manager
        )
        
        # =====================================================================
        # LISTAR TODAS LAS SESIONES
        # =====================================================================
        print(f"\n{'='*80}")
        print("📋 LISTANDO TODAS LAS SESIONES")
        print(f"{'='*80}")
        
        sessions = session_manager.list_sessions()
        print(f"\n✅ Total de sesiones: {len(sessions)}\n")
        
        for i, session in enumerate(sessions, 1):
            print(f"{i}. {session['session_id']}")
            print(f"   Guardada: {session['saved_at']}")
            print(f"   Mensajes: {session['metadata'].get('num_messages', 'N/A')}")
            print(f"   Archivo: {session['file_path']}")
            print()
        
        # =====================================================================
        # CARGAR Y VISUALIZAR HISTORIAL DE UNA SESIÓN
        # =====================================================================
        await display_session_history("personal_chat", session_manager)
        
        # =====================================================================
        # CARGAR Y CONTINUAR UNA SESIÓN
        # =====================================================================
        await load_and_continue_session(
            session_id="personal_chat",
            continuation_messages=[
                "Do you remember my name?",
                "Where did I say I live?",
                "What are my hobbies?"
            ],
            model_client=model_client,
            session_manager=session_manager
        )
        
        # =====================================================================
        # VISUALIZAR HISTORIAL ACTUALIZADO
        # =====================================================================
        await display_session_history("personal_chat", session_manager)
        
        # =====================================================================
        # RESUMEN FINAL
        # =====================================================================
        print(f"\n{'='*80}")
        print("✅ TEST COMPLETADO EXITOSAMENTE")
        print(f"{'='*80}")
        
        print("\n📁 Sesiones creadas:")
        for session in session_manager.list_sessions():
            print(f"  - {session['session_id']} ({session['metadata'].get('num_messages', 0)} mensajes)")
        
        print(f"\n📂 Directorio de sesiones: {session_manager.sessions_dir}")
        print("\n💡 Puedes inspeccionar los archivos JSON para ver la estructura completa")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await model_client.close()


if __name__ == "__main__":
    asyncio.run(main())
