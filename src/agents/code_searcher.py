"""
Code Searcher Agent - Agent specialized in code search and analysis
This agent searches and collects relevant information about code before making modifications
"""
import re
from autogen_agentchat.agents import AssistantAgent
from autogen_core.memory import Memory
from autogen_ext.models.openai import OpenAIChatCompletionClient
from typing import Dict, List, Optional, Any, AsyncGenerator

from src.config import CODE_SEARCHER_DESCRIPTION, CODE_SEARCHER_SYSTEM_MESSAGE


class CodeSearcher:
    """
    Agent specialized in searching and analyzing code to provide complete context
    """

    def __init__(
            self,
            model_client: OpenAIChatCompletionClient,
            tools: List,
            memory: Optional[List[Memory]] = None
    ):
        """
        Initializes the CodeSearcher agent

        Args:
            model_client: LLM model client
            tools: List of tools available to the agent
            memory: List of vector memories (optional)
        """
        self.model_client = model_client
        self._search_history: List[Dict[str, Any]] = []  # Search history

        # Create the agent with a specialized system message
        self.searcher_agent = AssistantAgent(
            name="CodeSearcher",
            description=CODE_SEARCHER_DESCRIPTION,
            system_message=CODE_SEARCHER_SYSTEM_MESSAGE,
            model_client=model_client,
            tools=tools,
            max_tool_iterations=10,  # Allow more iterations for exhaustive search
            reflect_on_tool_use=True,  # Reflect on tool results
            memory=memory or []  # Indexed codebase memory
        )

    async def search_code_context(self, query: str) -> Dict[str, Any]:
        """
        Searches and analyzes code related to a query

        Args:
            query: User query about what to search in the code

        Returns:
            Dictionary with the complete code analysis
        """
        from datetime import datetime

        # Execute the agent to search
        result = await self.searcher_agent.run(task=query)

        # Extract information from the result
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

        # Process messages to extract the analysis
        analysis_text = ""
        for msg in result.messages:
            if hasattr(msg, 'content') and hasattr(msg, 'source'):
                if msg.source == "CodeSearcher" and type(msg).__name__ == "TextMessage":
                    analysis_text = msg.content
                    analysis["analysis"] = analysis_text
                    break

        # Extract structured information from the analysis
        if analysis_text:
            # Extract mentioned files
            file_pattern = r'`([^`]+\.(py|js|ts|json|md|txt|csv))`'
            files = re.findall(file_pattern, analysis_text)
            analysis["files"] = [f[0] for f in files]

            # Extract function names
            function_pattern = r'`([a-zA-Z_][a-zA-Z0-9_]*)\(`'
            functions = re.findall(function_pattern, analysis_text)
            analysis["functions"] = list(set(functions))

            # Extract location references (file:line)
            location_pattern = r'`([^`]+\.(py|js|ts)):(\d+)`'
            locations = re.findall(location_pattern, analysis_text)
            analysis["locations"] = [f"{loc[0]}:{loc[2]}" for loc in locations]

        # Save to history
        self._search_history.append(analysis)

        return analysis

    async def search_code_context_stream(self, query: str):
        """
        Searches and analyzes code in streaming mode (to see real-time progress)

        Args:
            query: User query about what to search in the code

        Yields:
            Agent messages as the search is performed

        Note:
            This method does NOT save to history automatically.
            To save, use search_code_context() after streaming.
        """
        async for msg in self.searcher_agent.run_stream(task=query):
            yield msg

    def get_search_summary(self) -> str:
        """
        Gets a summary of searches performed

        Returns:
            Text summary of searches
        """
        if not self._search_history:
            return "📋 No searches have been performed yet."

        summary = f"📋 Search History ({len(self._search_history)} searches):\n\n"

        for i, search in enumerate(self._search_history[-5:], 1):  # Last 5
            query = search.get("query", "Unknown query")
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
        Gets the last search performed

        Returns:
            Dictionary with information from the last search or None
        """
        if self._search_history:
            return self._search_history[-1]
        return None

    def clear_history(self):
        """Clears the search history"""
        self._search_history.clear()

    def get_files_found(self) -> List[str]:
        """
        Gets list of all files found in all searches

        Returns:
            List of unique files found
        """
        all_files = set()
        for search in self._search_history:
            files = search.get("files", [])
            all_files.update(files)
        return sorted(list(all_files))

    def get_functions_found(self) -> List[str]:
        """
        Gets list of all functions found in all searches

        Returns:
            List of unique functions found
        """
        all_functions = set()
        for search in self._search_history:
            functions = search.get("functions", [])
            all_functions.update(functions)
        return sorted(list(all_functions))
