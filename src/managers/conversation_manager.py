"""
Gestión de historial de conversaciones en memoria durante la sesión activa.

NOTA: Para persistencia entre sesiones, usar StateManager con save_state/load_state de AutoGen.
Este manager solo mantiene el historial en memoria para estadísticas y tracking durante la sesión.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime


class ConversationManager:
    """
    Gestiona el historial de conversaciones EN MEMORIA durante la sesión activa.
    
    Para persistencia usa StateManager + AutoGen save_state/load_state.
    """

    def __init__(self):
        """Initialize conversation manager for in-memory tracking only"""
        self.conversation_history: List[Dict[str, Any]] = []

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Añade un mensaje al historial en memoria
        
        NOTA: Este historial es solo para estadísticas. El contexto de los agentes
        se maneja automáticamente por AutoGen save_state/load_state.
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.conversation_history.append(message)

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene los mensajes más recientes"""
        return self.conversation_history[-limit:]

    # REMOVED: save_to_file() and load_from_file()
    # Use StateManager with AutoGen's save_state()/load_state() instead
    # This provides official AutoGen support for persisting agent states

    def clear(self):
        """Limpia el historial en memoria"""
        self.conversation_history = []

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas del historial en memoria"""
        return {
            "total_messages": len(self.conversation_history),
            "first_message": self.conversation_history[0]["timestamp"] if self.conversation_history else None,
            "last_message": self.conversation_history[-1]["timestamp"] if self.conversation_history else None,
        }
