import logging
import os
import shutil
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.config.settings import get_settings
from src.managers.rag_manager import RAGManager

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rag_flow():
    print("----------------------------------------------------------------")
    print("Testing RAG Manager Flow")
    print("----------------------------------------------------------------")

    # 1. Load Settings
    settings = get_settings()
    if not settings.api_key:
        print("[Skipping] API Key not configured. Skipping test.")
        return

    print(f"Settings loaded. Model: {settings.model}, Base URL: {settings.base_url}")

    # 2. Initialize RAG Manager with a temporary directory
    test_db_path = "./rag_data_test"

    # Ensure clean slate
    if os.path.exists(test_db_path):
        shutil.rmtree(test_db_path)

    rag = RAGManager(settings=settings, persist_dir=test_db_path)
    print("RAG Manager initialized.")

    # 3. Read Dummy Data
    data_path = Path(__file__).parent / "data" / "dummy_data.txt"
    try:
        with open(data_path, encoding="utf-8") as f:
            text_content = f.read()
    except FileNotFoundError:
        print(f"[Error] Dummy data file not found at {data_path}")
        return

    # 4. Ingest Data
    collection_name = "test_collection"
    print(f"Ingesting document of length {len(text_content)}...")
    source_id = rag.add_document(
        collection_name=collection_name,
        text=text_content,
        metadata={"title": "AI History and RAG", "author": "Test Script"}
    )
    print(f"Document ingested with Source ID: {source_id}")

    # 5. Search
    query = "What is Retrieval-Augmented Generation?"
    print(f"Searching for: '{query}'")

    results = rag.search(collection_name=collection_name, query=query, top_k=3)

    print(f"Found {len(results)} results.")

    if results:
        for i, res in enumerate(results):
            print(f"\nResult {i+1} (Score: {res.get('score', 'N/A')}):")
            print(f"Content: {res['content'][:200]}...")
            print(f"Metadata: {res['metadata']}")
            print(f"Source: {res.get('retrieval_source', 'vector')}")
    else:
        print("[Failure] No results found.")

    # 6. Clean up
    rag.reset_db()
    # Explicitly remove directory if possible (might fail if still locked by dll)
    # shutil.rmtree(test_db_path, ignore_errors=True)
    print("Test completed.")

if __name__ == "__main__":
    test_rag_flow()
