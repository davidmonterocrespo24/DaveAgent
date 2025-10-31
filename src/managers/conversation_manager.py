"""
Gestión de historial de conversaciones con compresión inteligente
"""
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from pathlib import Path


class ConversationManager:
    """Gestiona el historial de conversaciones con compresión automática"""

    def __init__(self, max_tokens: int = 8000, summary_threshold: int = 6000):
        """
        Args:
            max_tokens: Límite máximo de tokens antes de forzar compresión
            summary_threshold: Umbral para considerar crear un resumen
        """
        self.max_tokens = max_tokens
        self.summary_threshold = summary_threshold
        self.conversation_history: List[Dict[str, Any]] = []
        self.summary: Optional[str] = None
        self.compressed_count = 0

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Añade un mensaje al historial"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.conversation_history.append(message)

    def estimate_tokens(self, text: str) -> int:
        """Estima el número de tokens (aproximación simple)"""
        # Aproximación: 1 token ≈ 4 caracteres para español
        return len(text) // 4

    def get_total_tokens(self) -> int:
        """Calcula el total de tokens en el historial actual"""
        total = 0
        if self.summary:
            total += self.estimate_tokens(self.summary)

        for msg in self.conversation_history:
            total += self.estimate_tokens(msg["content"])

        return total

    def needs_compression(self) -> bool:
        """Determina si el historial necesita ser comprimido"""
        return self.get_total_tokens() > self.summary_threshold

    def create_summary_prompt(self) -> str:
        """Crea un prompt para generar un resumen del historial"""
        conversation_text = ""

        if self.summary:
            conversation_text += f"RESUMEN PREVIO:\n{self.summary}\n\n"

        conversation_text += "CONVERSACIÓN RECIENTE:\n"
        for msg in self.conversation_history:
            role = msg["role"].upper()
            content = msg["content"]
            conversation_text += f"{role}: {content}\n\n"

        prompt = f"""Crea un resumen conciso pero completo de la siguiente conversación.
El resumen debe incluir:
1. Objetivos principales del usuario
2. Tareas completadas y resultados
3. Problemas encontrados y soluciones aplicadas
4. Estado actual del proyecto
5. Próximos pasos o tareas pendientes

{conversation_text}

Proporciona un resumen estructurado en español:"""

        return prompt

    def compress_history(self, summary_text: str):
        """Comprime el historial usando un resumen"""
        self.summary = summary_text
        # Mantener solo los últimos 3 mensajes para contexto inmediato
        self.conversation_history = self.conversation_history[-3:]
        self.compressed_count += 1

    def get_context_for_agent(self, max_recent_messages: int = 10) -> str:
        """Obtiene el contexto formateado para el agente"""
        context = ""

        if self.summary:
            context += f"=== RESUMEN DE CONVERSACIÓN PREVIA ===\n{self.summary}\n\n"

        context += "=== CONVERSACIÓN ACTUAL ===\n"
        recent_messages = self.conversation_history[-max_recent_messages:]

        for msg in recent_messages:
            role = msg["role"].upper()
            content = msg["content"]
            context += f"{role}: {content}\n\n"

        return context

    def save_to_file(self, filepath: str):
        """Guarda el historial en un archivo JSON"""
        data = {
            "summary": self.summary,
            "conversation_history": self.conversation_history,
            "compressed_count": self.compressed_count,
            "total_tokens": self.get_total_tokens(),
            "saved_at": datetime.now().isoformat()
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_from_file(self, filepath: str):
        """Carga el historial desde un archivo JSON"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.summary = data.get("summary")
        self.conversation_history = data.get("conversation_history", [])
        self.compressed_count = data.get("compressed_count", 0)

    def clear(self):
        """Limpia el historial completo"""
        self.conversation_history = []
        self.summary = None
        self.compressed_count = 0

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas del historial"""
        return {
            "total_messages": len(self.conversation_history),
            "total_tokens": self.get_total_tokens(),
            "compressed_count": self.compressed_count,
            "has_summary": self.summary is not None,
            "needs_compression": self.needs_compression()
        }
