"""
Example: Using DaveAgent Memory System

This example demonstrates how to use the memory system to:
1. Index a project codebase
2. Add user preferences
3. Query memory for relevant information
4. See how agents use memory automatically
"""

import asyncio
from pathlib import Path
from src.memory import MemoryManager, DocumentIndexer
from autogen_core.memory import MemoryContent, MemoryMimeType


async def main():
    """Demonstrate memory system usage"""

    print("=" * 60)
    print("DaveAgent Memory System Example")
    print("=" * 60)

    # =========================================================================
    # 1. Initialize Memory Manager
    # =========================================================================
    print("\n[1] Initializing Memory Manager...")

    memory_manager = MemoryManager(
        k=3,  # Return top 3 results
        score_threshold=0.3
    )

    print(f"✓ Memory initialized at: {memory_manager.persistence_path}")

    # =========================================================================
    # 2. Add User Preferences
    # =========================================================================
    print("\n[2] Adding user preferences...")

    await memory_manager.add_preference(
        preference="Always use type hints in Python code",
        category="code_style"
    )

    await memory_manager.add_preference(
        preference="Prefer FastAPI over Flask for APIs",
        category="framework"
    )

    await memory_manager.add_preference(
        preference="Use pytest for testing, not unittest",
        category="tool"
    )

    print("✓ Added 3 user preferences")

    # =========================================================================
    # 3. Add Sample Conversations
    # =========================================================================
    print("\n[3] Adding sample conversations...")

    await memory_manager.add_conversation(
        user_input="Create a REST API endpoint for user authentication",
        agent_response="I've created an authentication endpoint using FastAPI with JWT tokens. "
                       "The endpoint is at POST /api/auth/login and returns an access token.",
        metadata={
            "agents_used": ["Planner", "Coder"],
            "tools_called": ["write_file", "edit_file"]
        }
    )

    await memory_manager.add_conversation(
        user_input="Add error handling to the authentication endpoint",
        agent_response="Added comprehensive error handling including: invalid credentials, "
                       "expired tokens, and rate limiting. All errors return proper HTTP status codes.",
        metadata={
            "agents_used": ["Coder"],
            "tools_called": ["edit_file", "read_file"]
        }
    )

    print("✓ Added 2 sample conversations")

    # =========================================================================
    # 4. Add Architectural Decision
    # =========================================================================
    print("\n[4] Adding architectural decision...")

    await memory_manager.add_decision(
        decision="Use PostgreSQL with SQLAlchemy ORM for data persistence",
        context="After evaluating SQLite, MySQL, and PostgreSQL, we chose PostgreSQL for: "
                "(1) Better JSON support, (2) Full-text search capabilities, "
                "(3) Strong community support, (4) Excellent performance for our use case.",
        metadata={
            "category": "architecture",
            "impact": "high"
        }
    )

    print("✓ Added architectural decision")

    # =========================================================================
    # 5. Index Sample Code
    # =========================================================================
    print("\n[5] Indexing sample code...")

    # Create a small sample file to index
    sample_code = '''
"""
Authentication module for user login
"""
from fastapi import HTTPException
from datetime import datetime, timedelta
import jwt

def create_access_token(user_id: str, expires_delta: timedelta = None) -> str:
    """
    Create JWT access token for authenticated user

    Args:
        user_id: User identifier
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=24)

    expire = datetime.utcnow() + expires_delta
    payload = {
        "user_id": user_id,
        "exp": expire
    }
    return jwt.encode(payload, "SECRET_KEY", algorithm="HS256")


async def authenticate_user(username: str, password: str) -> dict:
    """
    Authenticate user with username and password

    Args:
        username: User's username
        password: User's password

    Returns:
        User data if authentication successful

    Raises:
        HTTPException: If authentication fails
    """
    # Verify credentials (simplified example)
    if not username or not password:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # In real app, verify against database
    user = {"id": "123", "username": username}
    return user
'''

    await memory_manager.add_code_chunk(
        code=sample_code,
        file_path="api/auth.py",
        metadata={
            "functions": ["create_access_token", "authenticate_user"],
            "classes": [],
            "description": "JWT authentication module"
        }
    )

    print("✓ Indexed sample authentication code")

    # =========================================================================
    # 6. Query Memory
    # =========================================================================
    print("\n[6] Querying memory...")

    # Query conversations
    print("\n  a) Query conversations about 'authentication':")
    conv_results = await memory_manager.query_conversations("authentication endpoint")
    for i, result in enumerate(conv_results, 1):
        print(f"     [{i}] Score: {result.metadata.get('score', 'N/A'):.2f}")
        print(f"         Content: {result.content[:100]}...")

    # Query preferences
    print("\n  b) Query preferences about 'Python':")
    pref_results = await memory_manager.query_preferences("Python coding style")
    for i, result in enumerate(pref_results, 1):
        print(f"     [{i}] {result.content}")

    # Query codebase
    print("\n  c) Query codebase for 'JWT token creation':")
    code_results = await memory_manager.query_codebase("how to create JWT token")
    for i, result in enumerate(code_results, 1):
        file_path = result.metadata.get('file_path', 'unknown')
        functions = result.metadata.get('functions', [])
        print(f"     [{i}] File: {file_path}")
        print(f"         Functions: {', '.join(functions) if functions else 'None'}")
        print(f"         Preview: {result.content[:80]}...")

    # Query decisions
    print("\n  d) Query decisions about 'database':")
    decision_results = await memory_manager.query_decisions("database choice PostgreSQL")
    for i, result in enumerate(decision_results, 1):
        print(f"     [{i}] {result.content[:150]}...")

    # =========================================================================
    # 7. Memory Statistics
    # =========================================================================
    print("\n[7] Memory Statistics:")
    print(f"  • Persistence path: {memory_manager.persistence_path}")

    try:
        total_size = sum(f.stat().st_size for f in memory_manager.persistence_path.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(f"  • Total size: {size_mb:.2f} MB")
    except Exception as e:
        print(f"  • Could not calculate size: {e}")

    # =========================================================================
    # 8. Cleanup (optional)
    # =========================================================================
    print("\n[8] Cleanup...")

    # Uncomment to clear all memory
    # await memory_manager.clear_all()
    # print("✓ Memory cleared")

    # Close memory connections
    await memory_manager.close()
    print("✓ Memory connections closed")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
