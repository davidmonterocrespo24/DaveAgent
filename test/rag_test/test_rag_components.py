import json
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
# logging.basicConfig(level=logging.INFO)
# We want to see print output clearly, so we might suppress some logging or keep it to INFO
logger = logging.getLogger(__name__)

def test_rag_components():
    print("================================================================")
    print("DETAILED RAG COMPONENT TEST")
    print("================================================================")

    # 1. Load Settings
    settings = get_settings()
    print(f"[Setup] Settings loaded. Model: {settings.model}")

    # 2. Initialize RAG Manager
    test_db_path = "./rag_data_test_components"
    if os.path.exists(test_db_path):
        shutil.rmtree(test_db_path)

    print("[Setup] Initializing RAGManager with local embeddings (BGE-M3)...")
    try:
        rag = RAGManager(settings=settings, persist_dir=test_db_path)
        print("[Setup] RAG Manager initialized successfully.")
    except Exception as e:
        print(f"[FATAL] Failed to initialize RAG Manager: {e}")
        return

    # 3. Ingest Data
    text_content = """
    Retrieval-Augmented Generation (RAG) is a technique that enhances the accuracy of generative AI.
    It retrieves relevant information from a knowledge base to provide context to the LLM.
    This reduces hallucinations and improves relevance.
    RAG systems typically use vector databases to store and retrieve semantic embeddings.
    """
    collection_name = "test_components"
    print("\n[Setup] Ingesting dummy data...")
    rag.add_document(collection_name, text_content, metadata={"topic": "RAG"})
    print("[Setup] Data ingested.")

    query = "What are the benefits of RAG?"
    print(f"\nQUERY: '{query}'")

    # ----------------------------------------------------------------
    # Step 1: Multi-Query Generation
    # ----------------------------------------------------------------
    print("\n----------------------------------------------------------------")
    print("COMPONENT 1: Multi-Query Generation")
    print("----------------------------------------------------------------")

    queries = rag._generate_multi_queries(query, n=2)
    print(f"Generated {len(queries)} queries:")
    for i, q in enumerate(queries):
        print(f"  {i+1}: {q}")

    if len(queries) > 1:
        print("[Pass] Multi-query generation working.")
    else:
        print("[Warn] Only original query returned (LLM might have failed or n=0).")

    # ----------------------------------------------------------------
    # Step 2: Vector Search (Individual)
    # ----------------------------------------------------------------
    print("\n----------------------------------------------------------------")
    print("COMPONENT 2: Vector Search (Simulated for each query)")
    print("----------------------------------------------------------------")

    collection = rag._get_collection(collection_name)
    results_list = []

    for i, q in enumerate(queries):
        print(f"\nSearching for query {i+1}: '{q}'")
        res = collection.query(query_texts=[q], n_results=2)
        results_list.append(res)

        # Print raw results for this query
        if res['ids']:
            for j, doc_id in enumerate(res['ids'][0]):
                content_snippet = res['documents'][0][j][:50]
                dist = res['distances'][0][j] if res['distances'] else "N/A"
                print(f"  -> Found: {doc_id} (Dist: {dist}) | '{content_snippet}...'")
        else:
            print("  -> No results found.")

    # ----------------------------------------------------------------
    # Step 3: Reciprocal Rank Fusion (RRF)
    # ----------------------------------------------------------------
    print("\n----------------------------------------------------------------")
    print("COMPONENT 3: Reciprocal Rank Fusion (RRF)")
    print("----------------------------------------------------------------")

    fused_results = rag._reciprocal_rank_fusion(results_list)

    print("Top Fused Results (Sorted by RRF Score):")
    for item in fused_results[:3]:
        print(f"  ID: {item['id']} | Score: {item['score']:.4f}")
        print(f"  Metadata: {item['metadata']}")

    if fused_results:
        print("[Pass] RRF merged results successfully.")
    else:
        print("[Fail] RRF produced no results.")

    # ----------------------------------------------------------------
    # Step 4: Parent Document Retrieval
    # ----------------------------------------------------------------
    print("\n----------------------------------------------------------------")
    print("COMPONENT 4: Parent Document Retrieval")
    print("----------------------------------------------------------------")

    final_output = []
    seen_parents = set()
    top_k = 2

    for item in fused_results:
        if len(final_output) >= top_k:
            break

        parent_id = item['metadata'].get('parent_id')
        print(f"Processing Item ID: {item['id']} -> Parent ID: {parent_id}")

        if parent_id and parent_id not in seen_parents:
            parent_doc = rag.docstore.get_document(parent_id)
            if parent_doc:
                print("  [Hit] Found Parent Document in DocStore.")
                print(f"  Parent Content Length: {len(parent_doc['content'])}")
                print(f"  Parent Content Preview: {parent_doc['content'][:60].replace(chr(10), ' ')}...")
                final_output.append(parent_doc)
                seen_parents.add(parent_id)
            else:
                print(f"  [Miss] Parent ID {parent_id} not found in DocStore.")
        elif parent_id in seen_parents:
            print(f"  [Skip] Parent {parent_id} already retrieved.")
        else:
             print("  [Info] No parent ID, using child doc.")

    if final_output:
        print("[Pass] Parent retrieval successful.")
    else:
        print("[Fail] No parent documents retrieved.")

    # Cleanup
    rag.reset_db()
    # shutil.rmtree(test_db_path, ignore_errors=True)
    print("\nTest Complete.")

if __name__ == "__main__":
    test_rag_components()
