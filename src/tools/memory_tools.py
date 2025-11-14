"""
Memory Tools - RAG-based tools for querying agent memory

These tools allow agents to query different memory stores without using
the AutoGen memory parameter (which causes issues with DeepSeek and other
LLMs that don't support multiple system messages).
"""
from typing import Annotated
from autogen_core.tools import FunctionTool


# Global memory manager instance (set by main.py)
_memory_manager = None


def set_memory_manager(manager):
    """Set the global memory manager instance"""
    global _memory_manager
    _memory_manager = manager


async def query_conversation_memory(
    query: Annotated[str, "The search query to find relevant past conversations"]
) -> str:
    """
    Query conversation memory to find relevant past conversations.

    Use this to:
    - Remember what was discussed before
    - Find similar problems solved in the past
    - Understand user's previous requests

    Args:
        query: What you want to search for in past conversations

    Returns:
        Relevant conversation excerpts with context
    """
    if _memory_manager is None:
        return "❌ Memory system not initialized"

    try:
        results = await _memory_manager.query_conversations(query)

        if not results:
            return f"No relevant conversations found for: {query}"

        # Format results
        output = f"📚 Found {len(results)} relevant conversation(s):\n\n"

        for i, result in enumerate(results, 1):
            content = result.content[:500]  # Limit length
            metadata = result.metadata or {}

            output += f"--- Conversation {i} ---\n"
            if "agents_used" in metadata:
                output += f"Agents: {metadata['agents_used']}\n"
            if "tools_called" in metadata:
                output += f"Tools: {metadata['tools_called']}\n"
            output += f"\n{content}\n\n"

        return output

    except Exception as e:
        return f"❌ Error querying conversation memory: {str(e)}"


async def query_codebase_memory(
    query: Annotated[str, "The search query to find relevant code"]
) -> str:
    """
    Query codebase memory to find relevant indexed code.

    Use this to:
    - Find where specific functionality is implemented
    - Understand existing code patterns
    - Locate functions, classes, or modules

    Args:
        query: What code or functionality you want to find

    Returns:
        Relevant code chunks with file paths
    """
    if _memory_manager is None:
        return "❌ Memory system not initialized"

    try:
        results = await _memory_manager.query_codebase(query)

        if not results:
            return f"No relevant code found for: {query}"

        # Format results
        output = f"📝 Found {len(results)} relevant code chunk(s):\n\n"

        for i, result in enumerate(results, 1):
            content = result.content[:800]  # Show more for code
            metadata = result.metadata or {}

            file_path = metadata.get("file_path", "unknown")
            language = metadata.get("language", "unknown")

            output += f"--- Code {i}: {file_path} ({language}) ---\n"
            output += f"{content}\n\n"

        return output

    except Exception as e:
        return f"❌ Error querying codebase memory: {str(e)}"


async def query_decision_memory(
    query: Annotated[str, "The search query to find relevant architectural decisions"]
) -> str:
    """
    Query decision memory to find relevant architectural decisions and patterns.

    Use this to:
    - Understand why certain design choices were made
    - Find established patterns to follow
    - Avoid repeating past mistakes

    Args:
        query: What decisions or patterns you want to find

    Returns:
        Relevant decisions with context
    """
    if _memory_manager is None:
        return "❌ Memory system not initialized"

    try:
        results = await _memory_manager.query_decisions(query)

        if not results:
            return f"No relevant decisions found for: {query}"

        # Format results
        output = f"🎯 Found {len(results)} relevant decision(s):\n\n"

        for i, result in enumerate(results, 1):
            content = result.content
            metadata = result.metadata or {}

            output += f"--- Decision {i} ---\n"
            output += f"{content}\n\n"

        return output

    except Exception as e:
        return f"❌ Error querying decision memory: {str(e)}"


async def query_preferences_memory(
    query: Annotated[str, "The search query to find relevant user preferences"]
) -> str:
    """
    Query user preferences memory to find relevant preferences and coding styles.

    Use this to:
    - Follow user's preferred coding style
    - Use their preferred frameworks/tools
    - Respect their workflow preferences

    Args:
        query: What preferences you want to find

    Returns:
        Relevant user preferences
    """
    if _memory_manager is None:
        return "❌ Memory system not initialized"

    try:
        results = await _memory_manager.query_preferences(query)

        if not results:
            return f"No relevant preferences found for: {query}"

        # Format results
        output = f"⚙️ Found {len(results)} relevant preference(s):\n\n"

        for i, result in enumerate(results, 1):
            content = result.content
            metadata = result.metadata or {}
            category = metadata.get("category", "general")

            output += f"--- Preference {i} ({category}) ---\n"
            output += f"{content}\n\n"

        return output

    except Exception as e:
        return f"❌ Error querying preferences memory: {str(e)}"


async def query_user_memory(
    query: Annotated[str, "The search query to find relevant user information"]
) -> str:
    """
    Query user memory to find relevant information about the user.

    Use this to:
    - Remember user's name, role, or background
    - Understand user's expertise level
    - Recall user's projects and goals

    Args:
        query: What user information you want to find

    Returns:
        Relevant user information
    """
    if _memory_manager is None:
        return "❌ Memory system not initialized"

    try:
        results = await _memory_manager.query_user_info(query)

        if not results:
            return f"No relevant user information found for: {query}"

        # Format results
        output = f"👤 Found {len(results)} relevant user info:\n\n"

        for i, result in enumerate(results, 1):
            content = result.content
            metadata = result.metadata or {}

            output += f"--- Info {i} ---\n"
            output += f"{content}\n\n"

        return output

    except Exception as e:
        return f"❌ Error querying user memory: {str(e)}"


async def save_user_info(
    info: Annotated[str, "User information to save (name, role, preferences, expertise, etc.)"],
    category: Annotated[str, "Category of information (personal, expertise, project, goal, etc.)"] = "general"
) -> str:
    """
    Save important information about the user to memory.

    Use this when:
    - User mentions their name, role, or background
    - User describes their expertise level
    - User shares project goals or context
    - User states important preferences

    Args:
        info: The information to save
        category: Type of information (personal, expertise, project, goal, etc.)

    Returns:
        Confirmation message
    """
    if _memory_manager is None:
        return "❌ Memory system not initialized"

    try:
        await _memory_manager.add_user_info(
            info=info,
            category=category
        )

        return f"✅ User information saved to memory (category: {category})"

    except Exception as e:
        return f"❌ Error saving user info: {str(e)}"


async def save_decision(
    decision: Annotated[str, "The architectural decision or pattern to save"],
    context: Annotated[str, "Context and reasoning for this decision"]
) -> str:
    """
    Save an important architectural decision or pattern to memory.

    Use this when:
    - Making significant design choices
    - Establishing patterns to follow
    - Learning from mistakes

    Args:
        decision: The decision made
        context: Why this decision was made

    Returns:
        Confirmation message
    """
    if _memory_manager is None:
        return "❌ Memory system not initialized"

    try:
        await _memory_manager.add_decision(
            decision=decision,
            context=context
        )

        return f"✅ Decision saved to memory"

    except Exception as e:
        return f"❌ Error saving decision: {str(e)}"


async def save_preference(
    preference: Annotated[str, "The user preference to save"],
    category: Annotated[str, "Category (code_style, framework, tool, workflow, etc.)"] = "general"
) -> str:
    """
    Save a user preference or coding style to memory.

    Use this when:
    - User expresses coding style preferences
    - User mentions preferred tools/frameworks
    - User describes their workflow

    Args:
        preference: The preference statement
        category: Type of preference

    Returns:
        Confirmation message
    """
    if _memory_manager is None:
        return "❌ Memory system not initialized"

    try:
        await _memory_manager.add_preference(
            preference=preference,
            category=category
        )

        return f"✅ Preference saved to memory (category: {category})"

    except Exception as e:
        return f"❌ Error saving preference: {str(e)}"


# Export as FunctionTool instances
query_conversation_memory_tool = FunctionTool(
    query_conversation_memory,
    description="Query past conversations to find relevant context and history"
)

query_codebase_memory_tool = FunctionTool(
    query_codebase_memory,
    description="Query indexed codebase to find relevant code and implementations"
)

query_decision_memory_tool = FunctionTool(
    query_decision_memory,
    description="Query architectural decisions and patterns from past work"
)

query_preferences_memory_tool = FunctionTool(
    query_preferences_memory,
    description="Query user's coding preferences and styles"
)

query_user_memory_tool = FunctionTool(
    query_user_memory,
    description="Query information about the user (name, expertise, projects, etc.)"
)

save_user_info_tool = FunctionTool(
    save_user_info,
    description="Save important information about the user to memory"
)

save_decision_tool = FunctionTool(
    save_decision,
    description="Save architectural decisions or patterns to memory"
)

save_preference_tool = FunctionTool(
    save_preference,
    description="Save user preferences or coding styles to memory"
)
