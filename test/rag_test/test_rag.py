import sys
import os
import shutil
import asyncio
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.managers.rag_manager import RAGManager
from src.config.settings import get_settings

def setup_test_env():
    """Sets up a clean test environment"""
    test_dir = Path("./test_rag_output")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir

def test_rag_flow():
    print("Starting RAG Manager Test...")
    
    # 1. Setup
    test_data_path = Path(__file__).parent / "data" / "dummy_data.txt"
    if not test_data_path.exists():
        print(f"Error: Test data not found at {test_data_path}")
        return

    persist_dir = setup_test_env()
    
    # 2. Initialize Settings & Manager
    print("\nInitializing RAGManager with Settings...")
    # Ensure we have settings (will load from environment or defaults)
    settings = get_settings()
    # Force no verify for local tests
    settings.ssl_verify = False 
    
    # Disable ChromaDB telemetry to avoid SSL issues
    os.environ["ANONYMIZED_TELEMETRY"] = "False"
    # Disable HuggingFace SSL verify to allow model download
    os.environ["HF_HUB_DISABLE_SSL_VERIFY"] = "1"
    
    print(f"   Model: {settings.model}")
    print(f"   Base URL: {settings.base_url}")
    
    rag = RAGManager(persist_dir=str(persist_dir), settings=settings)
    
    # 3. Ingest Document
    print("\nIngesting Document...")
    with open(test_data_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    metadata = {"source": "dummy_data.txt", "category": "test"}
    doc_id = rag.add_document("test_collection", content, metadata)
    print(f"   Document ingested with ID: {doc_id}")
    
    # 4. Search
    queries = [
        "What is RAG?",
        "Que es DaveAgent?",
        "DeepSeek Coder capabilities"
    ]
    
    print("\nTesting Search...")
    for q in queries:
        print(f"\n   Query: '{q}'")
        results = rag.search("test_collection", q, top_k=2)
        
        if not results:
            print("   No results found!")
        else:
            for i, res in enumerate(results):
                score = res.get('score', 0)
                content_preview = res['content'][:100].replace('\n', ' ')
                source = res.get('retrieval_source', 'unknown')
                print(f"     {i+1}. [{score:.4f}] ({source}) {content_preview}...")

    print("\nTest Completed.")

if __name__ == "__main__":
    test_rag_flow()
