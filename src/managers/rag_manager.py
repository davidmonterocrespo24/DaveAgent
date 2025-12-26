import json
import logging
import sqlite3
import threading
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

import httpx
import openai

# Configuration
from src.config.settings import DaveAgentSettings

# Configuración de Logging
# No usar basicConfig para evitar duplicación de logs con el logger principal de DaveAgent
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# 1. Custom Text Splitter (Reemplazo de LangChain RecursiveCharacterTextSplitter)
# -----------------------------------------------------------------------------
class TextSplitter:
    """
    Implementación nativa de split recursivo para dividir texto inteligentemente
    respetando estructuras gramaticales.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Orden de separadores: Párrafos -> Líneas -> Oraciones -> Palabras -> Caracteres
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> list[str]:
        final_chunks = []
        if self._length_function(text) <= self.chunk_size:
            return [text]

        # Estrategia recursiva
        self._split_text_recursive(text, self.separators, final_chunks)
        return final_chunks

    def _split_text_recursive(self, text: str, separators: list[str], final_chunks: list[str]):
        """Función recursiva interna."""
        final_separator = separators[-1]
        separator = separators[0]

        # Encontrar el separador adecuado
        for s in separators:
            if s == "":
                separator = s
                break
            if s in text:
                separator = s
                break

        # Dividir
        splits = list(text) if separator == "" else text.split(separator)
        new_separators = separators[1:] if len(separators) > 1 else separators

        good_splits = []
        # _separator_len = len(separator)

        for s in splits:
            if self._length_function(s) < self.chunk_size:
                good_splits.append(s)
            else:
                # Si el fragmento es muy grande, procesar lo acumulado y recursar en el grande
                if good_splits:
                    merged = self._merge_splits(good_splits, separator)
                    final_chunks.extend(merged)
                    good_splits = []
                if not new_separators:
                    final_chunks.append(s)  # Caso base extremo
                else:
                    self._split_text_recursive(s, new_separators, final_chunks)

        if good_splits:
            merged = self._merge_splits(good_splits, separator)
            final_chunks.extend(merged)

    def _merge_splits(self, splits: list[str], separator: str) -> list[str]:
        """Une splits pequeños hasta alcanzar el chunk_size con overlap."""
        docs = []
        current_doc = []
        total_len = 0

        for d in splits:
            _len = self._length_function(d)
            if total_len + _len + (len(current_doc) * len(separator)) > self.chunk_size:
                if total_len > 0:
                    doc_text = separator.join(current_doc)
                    docs.append(doc_text)

                    # Lógica de Overlap: Mantener los últimos chunks que quepan
                    while total_len > self.chunk_overlap or (
                        total_len + _len > self.chunk_size and total_len > 0
                    ):
                        total_len -= self._length_function(current_doc[0]) + len(separator)
                        current_doc.pop(0)

            current_doc.append(d)
            total_len += _len

        if current_doc:
            docs.append(separator.join(current_doc))
        return docs

    def _length_function(self, text: str) -> int:
        return len(text)


# -----------------------------------------------------------------------------
# 2. SQLite DocStore (Almacenamiento rápido de documentos padres)
# -----------------------------------------------------------------------------
class SQLiteDocStore:
    """Almacena los documentos 'Padre' completos para recuperación por ID."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    metadata TEXT
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error initializing DocStore DB: {e}")
            raise

    def add_documents(self, doc_ids: list[str], contents: list[str], metadatas: list[dict]):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            data = []
            for i, doc_id in enumerate(doc_ids):
                meta_json = json.dumps(metadatas[i]) if metadatas[i] else "{}"
                data.append((doc_id, contents[i], meta_json))

            cursor.executemany("INSERT OR REPLACE INTO documents VALUES (?, ?, ?)", data)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error adding documents to DocStore: {e}")

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT content, metadata FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return {"content": row[0], "metadata": json.loads(row[1])}
            return None
        except Exception as e:
            logger.error(f"Error getting document from DocStore: {e}")
            return None

    def clear(self):
        """Limpia todos los documentos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents")
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error clearing DocStore: {e}")


# -----------------------------------------------------------------------------
# 3. Hybrid Embedding Function (Compatible con ChromaDB)
# -----------------------------------------------------------------------------
class AdvancedEmbeddingFunction:
    """
    Maneja embeddings automáticamente.
    Intenta cargar BGE-M3 (local/huggingface), si falla usa OpenAI.
    Lazy loading implemented con soporte de threading.
    """

    # Atributo requerido por ChromaDB nuevo API
    supported_spaces = ["l2", "cosine", "ip"]

    def __init__(self, settings: DaveAgentSettings, use_gpu: bool = False):
        self.settings = settings
        self.use_gpu = use_gpu
        self.model = None
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self._initialized = False
        self._init_lock = threading.Lock()

    def _ensure_initialized(self):
        """Lazy load the model only when required."""
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return

            try:
                # Importación Lazy de SentenceTransformer (Heavy import)
                import time

                from sentence_transformers import SentenceTransformer

                device = "cuda" if self.use_gpu else "cpu"
                start_time = time.time()
                logger.info(f"Loading embedding model: {self.model_name} on {device}...")
                self.model = SentenceTransformer(self.model_name, device=device)
                load_time = time.time() - start_time
                logger.info(f"Embedding model loaded successfully in {load_time:.2f} seconds.")
                self._initialized = True
            except Exception as e:
                logger.error(f"Error loading embedding model ({e}).")
                raise ValueError(f"Error loading embedding model ({e}).")

    def name(self) -> str:
        """Return the name of the embedding function (required by ChromaDB)."""
        return self.model_name

    def is_legacy(self) -> bool:
        """Silences ChromaDB deprecation warning (must be a method)."""
        return False

    def embed_query(self, text: str = None, input: str = None) -> list[float]:
        """LangChain compatibility: Embed a single query."""
        self._ensure_initialized()
        # Handle both 'text' (LangChain) and 'input' (Chroma/Generic) args
        content = text if text is not None else input

        if content is None:
            return []

        if not self.model:
            return []

        # encode returns numpy array, convert to list
        # Ensure content is passed as list to encode
        embeddings = self.model.encode([content], normalize_embeddings=True)
        return embeddings[0].tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """LangChain compatibility: Embed a list of documents."""
        self._ensure_initialized()
        if not self.model:
            return []
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def __call__(self, input: Any) -> Any:
        # ChromaDB calls this. Input can be str or list[str]
        self._ensure_initialized()
        if self.model:
            # Handle single string vs list
            if isinstance(input, str):
                return self.embed_query(input=input)
            elif isinstance(input, list):
                return self.embed_documents(input)
        return []


# -----------------------------------------------------------------------------
# 4. RAG Manager (Core Class)
# -----------------------------------------------------------------------------
class RAGManager:
    def __init__(self, settings: DaveAgentSettings, persist_dir: str | None = None):
        self.settings = settings
        self.persist_dir = Path(persist_dir) if persist_dir else Path("./rag_data")
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        # Estado Lazy
        self._client = None
        self._embedding_fn = None
        self._docstore = None
        self._initialized = False
        self._init_lock = threading.Lock()

        # Splitters para Parent Document Retrieval (lightweight)
        self.parent_splitter = TextSplitter(chunk_size=2000, chunk_overlap=200)
        self.child_splitter = TextSplitter(chunk_size=400, chunk_overlap=50)

        # Cliente OpenAI para RAG Fusion (Generación de queries)
        http_client = httpx.Client(verify=self.settings.ssl_verify)
        self.llm_client = openai.Client(
            api_key=self.settings.api_key, base_url=self.settings.base_url, http_client=http_client
        )

    def _ensure_initialized(self):
        """Lazy init for heavy components (ChromaDB, DocStore, Embeddings)."""
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return

            import time

            t0 = time.time()
            logger.info("[RAGManager] Initializing heavy components...")

            # 1. Init Embedding Function (Wrapper only, model loads on first call)
            self._embedding_fn = AdvancedEmbeddingFunction(settings=self.settings)

            # 2. Init ChromaDB (Heavy import)
            import chromadb

            self._client = chromadb.PersistentClient(path=str(self.persist_dir / "vector_db"))

            # 3. Init DocStore (SQLite)
            self._docstore = SQLiteDocStore(str(self.persist_dir / "docstore.db"))

            self._initialized = True
            logger.info(f"[RAGManager] Components initialized in {time.time() - t0:.4f}s")

    def warmup(self):
        """
        Triggers initialization in background.
        Safe to be called from a background thread.
        """
        try:
            logger.info("[RAGManager] Starting background warmup...")
            self._ensure_initialized()
            # Also warmup the embedding model itself to avoid lag on first query
            if self._embedding_fn:
                self._embedding_fn._ensure_initialized()
            logger.info("[RAGManager] Background warmup complete and ready.")
        except Exception as e:
            logger.error(f"[RAGManager] Background warmup failed: {e}")

    @property
    def client(self):
        self._ensure_initialized()
        return self._client

    @property
    def embedding_fn(self):
        self._ensure_initialized()
        return self._embedding_fn

    @property
    def docstore(self):
        self._ensure_initialized()
        return self._docstore

    def _get_collection(self, name: str):
        self._ensure_initialized()
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},  # Optimizado para similitud semántica
        )

    def reset_db(self):
        """
        DANGER: Elimina y recrea la base de datos de vectores y docstore.
        Útil para tests.
        """
        self._ensure_initialized()
        try:
            self.client.reset()
            # Note: chromadb.PersistentClient.reset() might not be enabled by default in new versions
            # or requires ALLOW_RESET=TRUE env var.
            # If it fails, we might need to manually delete collections.
        except Exception as e:
            logger.warning(f"Could not reset ChromaDB via API: {e}")
            # Manual cleanup if needed, but risky while process is running
            # For collections:
            for collection in self.client.list_collections():
                try:
                    self.client.delete_collection(collection.name)
                except:
                    pass

        self.docstore.clear()
        logger.info("[RAG] Database reset completed.")

    # ---------------------------------------------------------
    # Ingesta: Parent Document Retrieval Strategy
    # ---------------------------------------------------------
    def add_document(
        self,
        collection_name: str,
        text: str,
        metadata: dict[str, Any] = None,
        source_id: str = None,
    ):
        """
        Divide el documento en 'Padres' grandes y luego en 'Hijos' pequeños.
        Los hijos van al VectorDB, los padres al DocStore.
        """
        # Ensure init before doing work
        self._ensure_initialized()

        metadata = metadata or {}
        if not source_id:
            source_id = str(uuid.uuid4())

        collection = self._get_collection(collection_name)

        # 1. Crear chunks PADRES
        parent_chunks = self.parent_splitter.split_text(text)

        parent_ids = []
        parent_contents = []
        parent_metas = []

        child_ids = []
        child_contents = []
        child_metas = []

        for i, p_text in enumerate(parent_chunks):
            p_id = f"{source_id}_p_{i}"
            parent_ids.append(p_id)
            parent_contents.append(p_text)

            # Metadata del padre
            p_meta = metadata.copy()
            p_meta.update({"type": "parent", "original_source_id": source_id})
            parent_metas.append(p_meta)

            # 2. Crear chunks HIJOS a partir del padre
            child_chunks = self.child_splitter.split_text(p_text)

            for j, c_text in enumerate(child_chunks):
                c_id = f"{p_id}_c_{j}"
                child_ids.append(c_id)
                child_contents.append(c_text)

                # Metadata del hijo DEBE apuntar al ID del padre
                c_meta = metadata.copy()
                # Chroma requiere tipos primitivos en metadata
                flat_meta = {
                    k: str(v) if isinstance(v, (list, dict)) else v for k, v in c_meta.items()
                }
                flat_meta.update(
                    {"parent_id": p_id, "type": "child", "original_source_id": source_id}
                )
                child_metas.append(flat_meta)

        # 3. Guardar Padres en SQLite
        if parent_ids:
            self.docstore.add_documents(parent_ids, parent_contents, parent_metas)
            logger.info(f"[Ingest] Guardados {len(parent_ids)} chunks padres en DocStore.")

        # 4. Guardar Hijos en ChromaDB (Vectores)
        if child_ids:
            collection.add(ids=child_ids, documents=child_contents, metadatas=child_metas)

        return source_id

    # ---------------------------------------------------------
    # Búsqueda Avanzada: Multi-Query + RRF + Parent Retrieval
    # ---------------------------------------------------------
    def _generate_multi_queries(self, query: str, n=3) -> list[str]:
        """Usa el Modelo Configurado para generar variaciones de la pregunta."""
        try:
            prompt = f"""Eres un experto en búsqueda semántica. Genera {n} versiones diferentes de la siguiente pregunta de usuario para mejorar la recuperación de documentos desde diversas perspectivas.
            Pregunta original: "{query}"
            Responde SOLO con las variaciones, una por línea. No enumeres."""

            # Usar el modelo configurado
            model_to_use = self.settings.model

            response = self.llm_client.chat.completions.create(
                model=model_to_use, messages=[{"role": "user", "content": prompt}], temperature=0.7
            )
            content = response.choices[0].message.content
            variations = [line.strip() for line in content.split("\n") if line.strip()]
            return [query] + variations[:n]  # Incluir siempre la original
        except Exception as e:
            logger.error(f"Error generando multi-queries: {e}")
            return [query]

    def _reciprocal_rank_fusion(self, results_list: list[dict], k=60):
        """
        Algoritmo RRF para fusionar resultados de múltiples queries.
        Score = 1 / (k + rank)
        """
        fused_scores = defaultdict(float)
        doc_map = {}  # Para guardar metadata y contenido y no perderlo

        for results in results_list:
            # Chroma devuelve listas de listas, aplanamos
            # Validar que results contiene datos antes de acceder
            if not results or "ids" not in results:
                continue

            if not results["ids"] or len(results["ids"]) == 0:
                continue

            # Verificar que la primera sublista no esté vacía
            if len(results["ids"][0]) == 0:
                continue

            ids = results["ids"][0]
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]

            # Verificar que tenemos la misma cantidad de documentos y metadatos
            if len(ids) != len(documents) or len(ids) != len(metadatas):
                logger.warning(
                    f"[RRF] Inconsistencia en resultados: {len(ids)} ids, {len(documents)} docs, {len(metadatas)} metas"
                )
                continue

            for rank, doc_id in enumerate(ids):
                # RRF Formula
                fused_scores[doc_id] += 1 / (k + rank)

                # Guardar referencia del documento si no existe
                if doc_id not in doc_map:
                    doc_map[doc_id] = {"content": documents[rank], "metadata": metadatas[rank]}

        # Ordenar por score RRF descendente
        sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)

        final_results = []
        for doc_id in sorted_ids:
            item = doc_map[doc_id]
            item["id"] = doc_id
            item["score"] = fused_scores[doc_id]
            final_results.append(item)

        return final_results

    def search(self, collection_name: str, query: str, top_k: int = 5, min_score: float = 0.3):
        """
        Flujo RAG Avanzado:
        1. Multi-Query Generation
        2. Vector Search en paralelo
        3. Reciprocal Rank Fusion
        4. Parent Document Lookup (recuperar el contexto completo)
        5. Filtrado por umbral de score mínimo

        Args:
            collection_name: Nombre de la colección a buscar
            query: Query del usuario
            top_k: Número máximo de resultados
            min_score: Score mínimo para considerar un resultado relevante (0.0-1.0)
                      Valores recomendados:
                      - 0.0: Sin filtro (devuelve todo)
                      - 0.1-0.3: Muy permisivo (devuelve resultados débilmente relacionados)
                      - 0.4-0.6: Moderado (solo resultados medianamente relevantes)
                      - 0.7+: Estricto (solo resultados muy relevantes)
        """
        # Ensure init
        self._ensure_initialized()

        collection = self._get_collection(collection_name)

        # 1. Generar variaciones de la query
        queries = self._generate_multi_queries(query)
        logger.info(f"[Search] Queries generadas: {queries}")

        # 2. Ejecutar búsquedas
        results_list = []
        for q in queries:
            res = collection.query(
                query_texts=[q],
                n_results=top_k * 2,  # Traemos más candidatos para fusionar
            )
            results_list.append(res)

        # 3. Fusionar resultados (RRF)
        fused_results = self._reciprocal_rank_fusion(results_list)

        # 4. Resolver a Documentos Padres (Parent Retrieval)
        final_output = []
        seen_parents = set()

        for item in fused_results:
            # FILTRO POR UMBRAL DE SCORE
            if item["score"] < min_score:
                continue

            if len(final_output) >= top_k:
                break

            parent_id = item["metadata"].get("parent_id")

            if parent_id and parent_id not in seen_parents:
                # Recuperar el texto completo del padre desde SQLite
                parent_doc = self.docstore.get_document(parent_id)
                if parent_doc:
                    final_output.append(
                        {
                            "content": parent_doc["content"],  # Contexto rico
                            "metadata": parent_doc["metadata"],
                            "score": item["score"],
                            "retrieval_source": "parent_doc",
                        }
                    )
                    seen_parents.add(parent_id)
            elif not parent_id:
                # Si no tiene padre (chunk huerfano), devolvemos el hijo
                final_output.append(item)

            # If item has parent but parent doc not found (edge case), ignore or add child.
            # Current logic ignores if parent_id exists but not found in docstore.

        return final_output
