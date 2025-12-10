"""
RAG Manager - Advanced vector database operations with LangChain integration.

This manager provides methods to:
- Create and manage collections
- Add documents/text with Parent Document Retrieval strategy
- Advanced search with RAG Fusion & Multi-Query
- Reciprocal Rank Fusion for better results
- Manage embeddings
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional, Tuple
import uuid
import logging
from pathlib import Path
import os
from collections import defaultdict
from langchain.storage._lc_store import create_kv_docstore
from langchain.storage import LocalFileStore
# LangChain imports
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

# Try new HuggingFaceEmbeddings first, fall back to deprecated version
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceBgeEmbeddings as HuggingFaceEmbeddings

# Local imports

_logger = logging.getLogger(__name__)


class RAGManager:
    """
    Advanced RAG Manager with Parent Document Retrieval and RAG Fusion.

    Features:
    1. Parent Document Retrieval: Splits documents into small chunks for embeddings
       but returns full parent documents for context
    2. RAG Fusion: Generates multiple query variations and uses RRF to rank results
    3. Multi-Query: Improves search by generating multiple perspectives of the query
    """

    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize RAG Manager with advanced retrieval capabilities.

        Args:
            persist_directory: Directory where ChromaDB will store data
        """

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Create docstore directory for parent documents
        self.docstore_directory = self.persist_directory / "docstore"
        self.docstore_directory.mkdir(parents=True, exist_ok=True)

        # Get OpenAI API key from environment (for LLM query generation)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Initialize embeddings with BGE-M3 (multilingual model)
        try:
            model_name = "BAAI/bge-m3"
            model_kwargs = {'device': 'cpu'}
            encode_kwargs = {'normalize_embeddings': True}

            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs=model_kwargs,
                encode_kwargs=encode_kwargs
            )
            _logger.info(f"[RAG] Using BGE-M3 embeddings model: {model_name}")
        except Exception as e:
            _logger.error(f"[RAG] Error loading BGE-M3 model: {e}")
            _logger.warning("[RAG] No embeddings configured!")

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Storage for collections and their configurations
        self.collections = {}
        self.vectorstores = {}  # LangChain Chroma instances
        self.docstores = {}     # FileDocstore for parent documents (persisted to disk as JSON)

        # Text splitters for Parent Document Retrieval
        self.parent_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            add_start_index=True
        )

        self.child_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50,
            add_start_index=True
        )

        # LLM for query generation (RAG Fusion)
        self.llm = ChatOpenAI(
            temperature=0,
            model="gpt-3.5-turbo",
            api_key=self.openai_api_key
        ) if self.openai_api_key else None

        _logger.info(f"[RAG] Initialized Advanced RAG Manager at: {self.persist_directory}")

    def get_or_create_collection(
        self,
        collection_name: str,
        use_langchain: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Get existing collection or create a new one.

        Args:
            collection_name: Name of the collection
            use_langchain: Whether to use LangChain Chroma wrapper
            metadata: Optional metadata for the collection

        Returns:
            ChromaDB collection or LangChain Chroma vectorstore
        """
        try:
            if use_langchain and self.embeddings:
                # Use LangChain Chroma wrapper for advanced features
                if collection_name not in self.vectorstores:
                    vectorstore = Chroma(
                        collection_name=collection_name,
                        embedding_function=self.embeddings,
                        persist_directory=str(self.persist_directory),
                        client=self.client  # Reuse existing client
                    )
                    self.vectorstores[collection_name] = vectorstore

                    # Create persistent docstore for parent documents
                    if collection_name not in self.docstores:
                        # Create a FileDocstore for this collection
                        collection_docstore_path = self.docstore_directory / collection_name
                        collection_docstore_path.mkdir(parents=True, exist_ok=True)

                        fs = LocalFileStore(str(collection_docstore_path))
                        docstore = create_kv_docstore(fs)
                        self.docstores[collection_name] = docstore

                        _logger.info(f"[RAG] Created persistent docstore for '{collection_name}' at {collection_docstore_path}")

                    _logger.info(f"[RAG] LangChain collection '{collection_name}' ready")

                return self.vectorstores[collection_name]
            else:
                # Use standard ChromaDB
                if collection_name in self.collections:
                    return self.collections[collection_name]

                collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata=metadata or {"description": "RAG collection"}
                )
                self.collections[collection_name] = collection
                _logger.info(f"[RAG] Standard collection '{collection_name}' ready")

                return collection

        except Exception as e:
            _logger.error(f"[RAG] Error creating collection: {e}")
            raise

    def add_text_with_parent_retrieval(
        self,
        collection_name: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add text using Parent Document Retrieval strategy.

        Process:
        1. Split text into parent chunks (2000 chars)
        2. Split parent chunks into child chunks (400 chars)
        3. Store child chunks in vectorstore with embeddings
        4. Store parent chunks in docstore for retrieval

        Args:
            collection_name: Name of the collection
            text: Text content to add
            metadata: Optional metadata for the document
            doc_id: Optional parent document ID

        Returns:
            Dictionary with parent and child IDs
        """
        try:
            if not self.embeddings:
                _logger.warning("[RAG] No embeddings configured, falling back to simple add")
                return {"error": "Embeddings not configured"}

            vectorstore = self.get_or_create_collection(collection_name, use_langchain=True)
            docstore = self.docstores[collection_name]

            # Create parent document
            parent_doc = Document(
                page_content=text,
                metadata=metadata or {}
            )

            # Generate parent ID
            if doc_id is None:
                doc_id = str(uuid.uuid4())

            # Split into parent chunks
            parent_chunks = self.parent_splitter.split_documents([parent_doc])

            all_child_ids = []
            parent_ids = []

            for i, parent_chunk in enumerate(parent_chunks):
                # Generate parent chunk ID
                parent_chunk_id = f"{doc_id}_parent_{i}"
                parent_ids.append(parent_chunk_id)

                # Store parent chunk in docstore
                docstore.mset([(parent_chunk_id, parent_chunk)])

                # Split parent into children
                child_chunks = self.child_splitter.split_documents([parent_chunk])

                # Add parent ID to child metadata
                for child in child_chunks:
                    child.metadata["parent_id"] = parent_chunk_id
                    child.metadata["source"] = metadata.get("source", "manual") if metadata else "manual"

                # Add children to vectorstore
                child_ids = vectorstore.add_documents(child_chunks)
                all_child_ids.extend(child_ids)

            _logger.info(
                f"[RAG] Added to '{collection_name}': "
                f"{len(parent_ids)} parent chunks, {len(all_child_ids)} child chunks"
            )

            return {
                "parent_id": doc_id,
                "parent_chunk_ids": parent_ids,
                "child_chunk_ids": all_child_ids,
                "num_parents": len(parent_ids),
                "num_children": len(all_child_ids)
            }

        except Exception as e:
            _logger.error(f"[RAG] Error in parent retrieval add: {e}")
            raise

    def generate_multi_queries(self, query: str, num_queries: int = 3) -> List[str]:
        """
        Generate multiple variations of a query using LLM.

        This is the Multi-Query technique for RAG Fusion.

        Args:
            query: Original user query
            num_queries: Number of query variations to generate

        Returns:
            List of query variations (including original)
        """
        if not self.llm:
            _logger.warning("[RAG] LLM not configured, returning original query only")
            return [query]

        try:
            prompt = ChatPromptTemplate.from_template(
                """You are an AI assistant helping to improve search queries.
                Given the original query, generate {num_queries} different variations that ask the same thing
                but from different perspectives or using different phrasings.

                Original query: {query}

                Generate {num_queries} variations (one per line):"""
            )

            response = self.llm.invoke(
                prompt.format(query=query, num_queries=num_queries)
            )

            # Parse response
            variations = [line.strip() for line in response.content.strip().split('\n') if line.strip()]

            # Ensure we have the original query
            all_queries = [query] + variations[:num_queries]

            _logger.info(f"[RAG] Generated {len(all_queries)} query variations")
            return all_queries

        except Exception as e:
            _logger.error(f"[RAG] Error generating queries: {e}")
            return [query]

    def reciprocal_rank_fusion(
        self,
        search_results_list: List[List[Tuple[Document, float]]],
        k: int = 60
    ) -> List[Tuple[Document, float]]:
        """
        Apply Reciprocal Rank Fusion (RRF) to combine multiple search results.

        RRF formula: score(doc) = sum(1 / (k + rank(doc, query_i)))

        Args:
            search_results_list: List of search results from different queries
            k: Constant for RRF (default: 60)

        Returns:
            Fused and re-ranked results
        """
        # Track scores for each unique document
        doc_scores = defaultdict(float)
        doc_objects = {}  # Store document objects

        for search_results in search_results_list:
            for rank, (doc, _score) in enumerate(search_results, start=1):
                # Use page_content as unique identifier
                doc_id = doc.page_content

                # RRF score (only rank matters, not the original score)
                rrf_score = 1.0 / (k + rank)
                doc_scores[doc_id] += rrf_score

                # Store document object
                if doc_id not in doc_objects:
                    doc_objects[doc_id] = doc

        # Sort by RRF score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Return as list of (Document, score) tuples
        results = [
            (doc_objects[doc_id], score)
            for doc_id, score in sorted_docs
        ]

        _logger.info(f"[RAG] RRF fused {len(search_results_list)} result sets into {len(results)} unique docs")
        return results

    def search_with_rag_fusion(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        num_query_variations: int = 3,
        return_parent: bool = True,
        filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Advanced search using RAG Fusion and Parent Document Retrieval.
        
        Process:
        1. Generate multiple query variations (Multi-Query)
        2. Search with each variation
        3. Apply Reciprocal Rank Fusion to combine results
        4. Return parent documents if enabled
        
        Args:
            collection_name: Name of the collection to search
            query: Search query
            n_results: Number of final results to return
            num_query_variations: Number of query variations to generate
            return_parent: Whether to return parent documents instead of child chunks
            filter: Metadata filter for the search
            
        Returns:
            Dictionary with search results and metadata
        """
        try:
            if collection_name not in self.vectorstores:
                _logger.warning(f"[RAG] Collection '{collection_name}' not found in vectorstores")
                # Fall back to simple search
                return self.search(collection_name, query, n_results)

            vectorstore = self.vectorstores[collection_name]
            docstore = self.docstores.get(collection_name)

            # Step 1: Generate query variations
            queries = self.generate_multi_queries(query, num_query_variations)
            _logger.info(f"[RAG] Searching with {len(queries)} query variations")

            # Step 2: Search with each query variation
            all_search_results = []
            for q in queries:
                results = vectorstore.similarity_search_with_score(q, k=n_results * 2, filter=filter)
                all_search_results.append(results)

            # Step 3: Apply Reciprocal Rank Fusion
            fused_results = self.reciprocal_rank_fusion(all_search_results)

            # Step 4: Get parent documents if requested
            final_results = []
            seen_parents = set()

            for doc, score in fused_results[:n_results * 3]:  # Get more to account for duplicates
                if return_parent and docstore:
                    # Try to get parent document
                    parent_id = doc.metadata.get("parent_id")
                    if parent_id and parent_id not in seen_parents:
                        parent_doc = docstore.mget([parent_id])[0] if parent_id else None
                        if parent_doc:
                            # Parent document found
                            final_results.append({
                                "document": parent_doc.page_content,
                                "metadata": parent_doc.metadata,
                                "score": float(score),
                                "parent_id": parent_id,
                                "retrieval_type": "parent"
                            })
                            seen_parents.add(parent_id)
                        else:
                            # Parent not found in docstore, fall back to child chunk
                            final_results.append({
                                "document": doc.page_content,
                                "metadata": doc.metadata,
                                "score": float(score),
                                "retrieval_type": "child (parent unavailable)"
                            })
                    elif not parent_id:
                        # No parent_id in metadata, return child chunk
                        final_results.append({
                            "document": doc.page_content,
                            "metadata": doc.metadata,
                            "score": float(score),
                            "retrieval_type": "child"
                        })
                else:
                    # Return child chunk
                    final_results.append({
                        "document": doc.page_content,
                        "metadata": doc.metadata,
                        "score": float(score),
                        "retrieval_type": "child"
                    })

                # Stop when we have enough results
                if len(final_results) >= n_results:
                    break

            _logger.info(
                f"[RAG] RAG Fusion search returned {len(final_results)} results "
                f"(type: {'parent' if return_parent else 'child'})"
            )

            return {
                "query": query,
                "query_variations": queries,
                "results": final_results,
                "count": len(final_results),
                "fusion_method": "reciprocal_rank_fusion",
                "retrieval_strategy": "parent_document" if return_parent else "child_chunk"
            }

        except Exception as e:
            _logger.error(f"[RAG] Error in RAG Fusion search: {e}")
            raise

    # Keep existing simple methods for backward compatibility
    def add_text(
        self,
        collection_name: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> str:
        """
        Simple text addition (backward compatible).
        Uses parent retrieval if embeddings are available.
        """
        result = self.add_text_with_parent_retrieval(
            collection_name, text, metadata, doc_id
        )
        if isinstance(result, dict) and "parent_id" in result:
            return result["parent_id"]
        return str(uuid.uuid4())

    def search(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Simple search (backward compatible).
        Always tries to use RAG Fusion with LangChain if embeddings are available.
        """
        # Try to load collection with LangChain (this will reuse existing collection)
        if self.embeddings:
            try:
                # Load with LangChain to use the correct embeddings
                vectorstore = self.get_or_create_collection(collection_name, use_langchain=True)

                # Now use RAG Fusion
                return self.search_with_rag_fusion(
                    collection_name,
                    query,
                    n_results=n_results,
                    return_parent=True,
                    filter=where
                )
            except Exception as e:
                _logger.warning(f"[RAG] Failed to use LangChain search: {e}, falling back to standard")

        # Fallback to standard ChromaDB search (without embeddings)
        collection = self.get_or_create_collection(collection_name, use_langchain=False)
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where
        )

        formatted_results = {
            "query": query,
            "documents": results.get("documents", [[]])[0],
            "metadatas": results.get("metadatas", [[]])[0],
            "distances": results.get("distances", [[]])[0],
            "ids": results.get("ids", [[]])[0],
            "count": len(results.get("documents", [[]])[0])
        }

        return formatted_results

    def add_texts(
        self,
        collection_name: str,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add multiple texts to a collection."""
        result_ids = []
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas else None
            doc_id = ids[i] if ids else None
            result_id = self.add_text(collection_name, text, metadata, doc_id)
            result_ids.append(result_id)
        return result_ids

    def delete_document(self, collection_name: str, doc_id: str) -> bool:
        """Delete a document from a collection."""
        try:
            collection = self.get_or_create_collection(collection_name, use_langchain=False)
            collection.delete(ids=[doc_id])
            _logger.info(f"[RAG] Deleted document from '{collection_name}': {doc_id}")
            return True
        except Exception as e:
            _logger.error(f"[RAG] Error deleting document: {e}")
            raise

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection."""
        try:
            collection = self.client.get_collection(name=collection_name)
            count = collection.count()

            # Check if vectorstore exists (load it if not in memory)
            has_vectorstore = False
            if collection_name not in self.vectorstores and self.embeddings:
                # Try to load existing vectorstore
                try:
                    self.get_or_create_collection(collection_name, use_langchain=True)
                    has_vectorstore = True
                except:
                    pass
            else:
                has_vectorstore = collection_name in self.vectorstores

            # Check if docstore exists (check filesystem)
            has_docstore = False
            parent_doc_count = 0

            # Check if docstore directory exists
            collection_docstore_path = self.docstore_directory / collection_name
            if collection_docstore_path.exists():
                has_docstore = True

                # Load docstore if not in memory
                if collection_name not in self.docstores:
                    try:
                        docstore = FileDocstore(str(collection_docstore_path))
                        self.docstores[collection_name] = docstore
                    except:
                        pass

                # Count parent documents
                if collection_name in self.docstores:
                    try:
                        parent_doc_count = len(list(self.docstores[collection_name].yield_keys()))
                    except:
                        parent_doc_count = 0

            stats = {
                "name": collection_name,
                "count": count,
                "metadata": collection.metadata,
                "has_langchain_vectorstore": has_vectorstore,
                "has_docstore": has_docstore
            }

            if has_docstore and parent_doc_count > 0:
                stats["parent_documents"] = parent_doc_count

            return stats
        except Exception as e:
            _logger.error(f"[RAG] Error getting collection stats: {e}")
            raise

    def list_collections(self) -> List[str]:
        """List all available collections."""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            _logger.error(f"[RAG] Error listing collections: {e}")
            raise

    def delete_collection(self, collection_name: str) -> bool:
        """Delete an entire collection."""
        try:
            self.client.delete_collection(name=collection_name)

            if collection_name in self.collections:
                del self.collections[collection_name]
            if collection_name in self.vectorstores:
                del self.vectorstores[collection_name]
            if collection_name in self.docstores:
                del self.docstores[collection_name]

            _logger.info(f"[RAG] Deleted collection: {collection_name}")
            return True
        except Exception as e:
            _logger.error(f"[RAG] Error deleting collection: {e}")
            raise