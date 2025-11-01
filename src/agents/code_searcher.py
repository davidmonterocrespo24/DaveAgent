"""
Code Searcher Agent - Agente especializado en búsqueda y análisis de código
Este agente busca y recopila información relevante sobre el código antes de hacer modificaciones
"""
from typing import Dict, List, Optional, Any, AsyncGenerator
import re
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient


class CodeSearcher:
    """
    Agente especializado en buscar y analizar código para proporcionar contexto completo
    """

    def __init__(self, model_client: OpenAIChatCompletionClient, tools: List):
        """
        Inicializa el agente CodeSearcher

        Args:
            model_client: Cliente del modelo LLM
            tools: Lista de herramientas disponibles para el agente
        """
        self.model_client = model_client
        self._search_history: List[Dict[str, Any]] = []  # Historial de búsquedas

        # Crear el agente con un system message especializado
        self.searcher_agent = AssistantAgent(
            name="CodeSearcher",
            description="""Agente especializado en BÚSQUEDA y ANÁLISIS de código.

Úsalo cuando necesites:
- Encontrar referencias a funciones, clases o variables
- Entender cómo funciona una parte específica del código
- Buscar dónde se usa una funcionalidad
- Analizar dependencias entre archivos
- Obtener contexto antes de modificar código
- Mapear la estructura de un proyecto

Este agente NO modifica código, solo lo analiza y proporciona información.""",

            system_message="""Eres un experto analista de código especializado en búsqueda y comprensión.

TU OBJETIVO:
Cuando el usuario te pide información sobre código, debes:

1. BUSCAR exhaustivamente en el código base usando las herramientas disponibles
2. ANALIZAR las funciones, clases, variables y dependencias relacionadas
3. PROPORCIONAR un informe detallado y estructurado con:
   - Nombres de funciones/clases relevantes
   - Ubicación exacta (archivo:línea)
   - Fragmentos de código completos
   - Explicación de qué hace cada componente
   - Dependencias y relaciones
   - Variables importantes y su uso
   - Sugerencias de qué archivos modificar

ESTRATEGIA DE BÚSQUEDA:

1. **Búsqueda Inicial**: Usa `grep_search` o `codebase_search` para encontrar menciones
2. **Análisis de Archivos**: Lee los archivos relevantes con `read_file`
3. **Análisis de Funciones**: Si es Python, usa `analyze_python_file` para detalles
4. **Contexto Amplio**: Busca referencias cruzadas y dependencias
5. **Resumen Estructurado**: Organiza toda la información de forma clara

FORMATO DE RESPUESTA:

Proporciona tu respuesta en este formato estructurado:

## 🔍 Análisis de Código: [Tema]

### 📍 Archivos Relevantes
- `archivo1.py` (líneas X-Y): Descripción
- `archivo2.py` (líneas A-B): Descripción

### 🔧 Funciones Encontradas

#### Función: `nombre_funcion`
- **Ubicación**: `archivo.py:123`
- **Parámetros**: param1, param2
- **Retorna**: tipo de retorno
- **Propósito**: Qué hace la función

**Código**:
```python
def nombre_funcion(param1, param2):
    # código completo
    pass
```

**Usado en**:
- `archivo_x.py:45` - contexto de uso
- `archivo_y.py:78` - contexto de uso

### 📦 Variables/Constantes Importantes
- `VARIABLE_NAME`: valor, uso, ubicación

### 🔗 Dependencias
- Importa: módulos externos
- Depende de: otras funciones/clases internas

### 💡 Recomendaciones
- Para modificar X, debes editar: archivo1.py, archivo2.py
- Ten en cuenta: consideraciones importantes
- Funciones relacionadas que pueden verse afectadas: lista

### 📝 Código Relevante Completo

```python
# Fragmentos de código completos y contextualizados
```

IMPORTANTE:
- Siempre proporciona código COMPLETO, no solo referencias
- Incluye números de línea exactos
- Explica el propósito de cada componente
- Identifica todas las dependencias
- Sé exhaustivo en la búsqueda

Usa estas herramientas en este orden típico:
1. `codebase_search` o `grep_search` - para buscar
2. `read_file` - para leer archivos completos
3. `analyze_python_file` - para análisis detallado de Python
4. `find_function_definition` - para localizar definiciones exactas
5. `list_all_functions` - para ver estructura general

Responde SIEMPRE en español con formato Markdown claro.""",

            model_client=model_client,
            tools=tools,
            max_tool_iterations=10,  # Permitir más iteraciones para búsqueda exhaustiva
            reflect_on_tool_use=True,  # Reflexionar sobre resultados de herramientas
        )

    async def search_code_context(self, query: str) -> Dict[str, Any]:
        """
        Busca y analiza código relacionado con una consulta

        Args:
            query: Consulta del usuario sobre qué buscar en el código

        Returns:
            Diccionario con el análisis completo del código
        """
        from datetime import datetime

        # Ejecutar el agente para buscar
        result = await self.searcher_agent.run(task=query)

        # Extraer información del resultado
        analysis = {
            "query": query,
            "messages": result.messages,
            "analysis": "",
            "files": [],
            "functions": [],
            "variables": [],
            "recommendations": [],
            "locations": [],
            "timestamp": datetime.now().isoformat(),
            "raw_result": result
        }

        # Procesar mensajes para extraer el análisis
        analysis_text = ""
        for msg in result.messages:
            if hasattr(msg, 'content') and hasattr(msg, 'source'):
                if msg.source == "CodeSearcher" and type(msg).__name__ == "TextMessage":
                    analysis_text = msg.content
                    analysis["analysis"] = analysis_text
                    break

        # Extraer información estructurada del análisis
        if analysis_text:
            # Extraer archivos mencionados
            file_pattern = r'`([^`]+\.(py|js|ts|json|md|txt|csv))`'
            files = re.findall(file_pattern, analysis_text)
            analysis["files"] = [f[0] for f in files]

            # Extraer nombres de funciones
            function_pattern = r'`([a-zA-Z_][a-zA-Z0-9_]*)\(`'
            functions = re.findall(function_pattern, analysis_text)
            analysis["functions"] = list(set(functions))

            # Extraer referencias a ubicaciones (archivo:línea)
            location_pattern = r'`([^`]+\.(py|js|ts)):(\d+)`'
            locations = re.findall(location_pattern, analysis_text)
            analysis["locations"] = [f"{loc[0]}:{loc[2]}" for loc in locations]

        # Guardar en historial
        self._search_history.append(analysis)

        return analysis

    async def search_code_context_stream(self, query: str):
        """
        Busca y analiza código en modo streaming (para ver progreso en tiempo real)

        Args:
            query: Consulta del usuario sobre qué buscar en el código

        Yields:
            Mensajes del agente conforme realiza la búsqueda

        Note:
            Este método NO guarda en el historial automáticamente.
            Para guardar, usa search_code_context() después del streaming.
        """
        async for msg in self.searcher_agent.run_stream(task=query):
            yield msg

    def get_search_summary(self) -> str:
        """
        Obtiene un resumen de las búsquedas realizadas

        Returns:
            Resumen en texto de las búsquedas
        """
        if not self._search_history:
            return "📋 No se han realizado búsquedas todavía."

        summary = f"📋 Historial de Búsquedas ({len(self._search_history)} búsquedas):\n\n"

        for i, search in enumerate(self._search_history[-5:], 1):  # Últimas 5
            query = search.get("query", "Consulta desconocida")
            files = search.get("files", [])
            functions = search.get("functions", [])

            summary += f"{i}. {query[:60]}...\n"
            if files:
                summary += f"   Archivos: {', '.join(files[:3])}\n"
            if functions:
                summary += f"   Funciones: {', '.join(functions[:3])}\n"
            summary += "\n"

        return summary

    def get_last_search(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene la última búsqueda realizada

        Returns:
            Diccionario con información de la última búsqueda o None
        """
        if self._search_history:
            return self._search_history[-1]
        return None

    def clear_history(self):
        """Limpia el historial de búsquedas"""
        self._search_history.clear()

    def get_files_found(self) -> List[str]:
        """
        Obtiene lista de todos los archivos encontrados en todas las búsquedas

        Returns:
            Lista de archivos únicos encontrados
        """
        all_files = set()
        for search in self._search_history:
            files = search.get("files", [])
            all_files.update(files)
        return sorted(list(all_files))

    def get_functions_found(self) -> List[str]:
        """
        Obtiene lista de todas las funciones encontradas en todas las búsquedas

        Returns:
            Lista de funciones únicas encontradas
        """
        all_functions = set()
        for search in self._search_history:
            functions = search.get("functions", [])
            all_functions.update(functions)
        return sorted(list(all_functions))
