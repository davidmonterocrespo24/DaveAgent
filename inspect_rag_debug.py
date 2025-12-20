from src.managers.rag_manager import AdvancedEmbeddingFunction
from src.config import get_settings

def test_embed():
    settings = get_settings()
    embed_fn = AdvancedEmbeddingFunction(settings)
    
    print("Initializing...")
    embed_fn._ensure_initialized()
    
    cases = [
        "Normal query",
        "",
        "   ",
        None
    ]
    
    for c in cases:
        print(f"\nTesting input: '{c}'")
        try:
            res = embed_fn.embed_query(text=c)
            # OR via __call__ which Chroma uses
            # res = embed_fn(input=c)
            print(f"Result len: {len(res) if res else 'None/Empty'}")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    test_embed()
