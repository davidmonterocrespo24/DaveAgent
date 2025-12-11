import os
import uuid
import logging
import sqlite3
import json
import math
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from collections import defaultdict
import re

# Librerías Core
import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.config import Settings
import openai
from sentence_transformers import SentenceTransformer
import httpx

# Configuration
from src.config.settings import DaveAgentSettings

# Configuración de Logging
# No usar basicConfig para evitar duplicación de logs
# El logger principal de DaveAgent ya está configurado
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

    def split_text(self, text: str) -> List[str]:
        final_chunks = []
        if self._length_function(text) <= self.chunk_size:
            return [text]
        
        # Estrategia recursiva
        self._split_text_recursive(text, self.separators, final_chunks)
        return final_chunks

    def _split_text_recursive(self, text: str, separators: List[str], final_chunks: List[str]):
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
                    final_chunks.append(s) # Caso base extremo
                else:
                    self._split_text_recursive(s, new_separators, final_chunks)
        
        if good_splits:
            merged = self._merge_splits(good_splits, separator)
            final_chunks.extend(merged)

    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
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
                    while total_len > self.chunk_overlap or (total_len + _len > self.chunk_size and total_len > 0):
                        total_len -= (self._length_function(current_doc[0]) + len(separator))
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
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    content TEXT,
                    metadata TEXT
                )
            ''')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error initializing DocStore DB: {e}")
            raise

    def add_documents(self, doc_ids: List[str], contents: List[str], metadatas: List[Dict]):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            data = []
            for i, doc_id in enumerate(doc_ids):
                meta_json = json.dumps(metadatas[i]) if metadatas[i] else "{}"
                data.append((doc_id, contents[i], meta_json))
            
            cursor.executemany('INSERT OR REPLACE INTO documents VALUES (?, ?, ?)', data)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error adding documents to DocStore: {e}")

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT content, metadata FROM documents WHERE id = ?', (doc_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "content": row[0],
                    "metadata": json.loads(row[1])
                }
            return None
        except Exception as e:
            logger.error(f"Error getting document from DocStore: {e}")
            return None
            
    def clear(self):
        """Limpia todos los documentos."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM documents')
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error clearing DocStore: {e}")

# -----------------------------------------------------------------------------
# 3. Hybrid Embedding Function (Compatible con ChromaDB)
# -----------------------------------------------------------------------------
class AdvancedEmbeddingFunction(EmbeddingFunction):
    """
    Maneja embeddings automáticamente.
    Intenta cargar BGE-M3 (local/huggingface), si falla usa OpenAI.
    """
    def __init__(self, settings: DaveAgentSettings, use_gpu: bool = False):
        self.model = None
        
        # Intenta cargar SentenceTransformer (Local - Gratis y Potente)
        try:
            model_name = "BAAI/bge-m3"
            device = "cuda" if use_gpu else "cpu"
            # Usar backend="torch" para evitar descargar múltiples formatos del modelo
            # y preferir safetensors si está disponible
            self.model = SentenceTransformer(
                model_name, 
                device=device,
                backend="torch",
                model_kwargs={"use_safetensors": True}
            )
        except Exception as e:
            logger.error(f"[RAG] Error FATAL: No se pudo cargar modelo local ({e}).")
            raise ValueError(f"Se requieren embeddings locales (BGE-M3). Error: {e}")

    def __call__(self, input: Documents) -> Embeddings:
        if self.model:
            # Normalizar embeddings es crucial para similitud coseno
            embeddings = self.model.encode(input, normalize_embeddings=True)
            return embeddings.tolist()
        return []

# -----------------------------------------------------------------------------
# 4. RAG Manager (Core Class)
# -----------------------------------------------------------------------------
class RAGManager:
    def __init__(self, settings: DaveAgentSettings, persist_dir: Optional[str] = None):
        self.settings = settings
        self.persist_dir = Path(persist_dir) if persist_dir else Path("./rag_data")
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar ChromaDB
        self.client = chromadb.PersistentClient(path=str(self.persist_dir / "vector_db"))
        self.embedding_fn = AdvancedEmbeddingFunction(settings=self.settings)
        
        # Inicializar DocStore (SQLite)
        self.docstore = SQLiteDocStore(str(self.persist_dir / "docstore.db"))
        
        # Splitters para Parent Document Retrieval
        self.parent_splitter = TextSplitter(chunk_size=2000, chunk_overlap=200)
        self.child_splitter = TextSplitter(chunk_size=400, chunk_overlap=50)
        
        # Cliente OpenAI para RAG Fusion (Generación de queries)
        http_client = httpx.Client(verify=self.settings.ssl_verify)
        self.llm_client = openai.Client(
            api_key=self.settings.api_key,
            base_url=self.settings.base_url,
            http_client=http_client
        )

    def _get_collection(self, name: str):
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"} # Optimizado para similitud semántica
        )

    def reset_db(self):
        """
        DANGER: Elimina y recrea la base de datos de vectores y docstore.
        Útil para tests.
        """
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
    def add_document(self, collection_name: str, text: str, metadata: Dict[str, Any] = None, source_id: str = None):
        """
        Divide el documento en 'Padres' grandes y luego en 'Hijos' pequeños.
        Los hijos van al VectorDB, los padres al DocStore.
        """
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
                flat_meta = {k: str(v) if isinstance(v, (list, dict)) else v for k,v in c_meta.items()}
                flat_meta.update({
                    "parent_id": p_id, 
                    "type": "child",
                    "original_source_id": source_id
                })
                child_metas.append(flat_meta)

        # 3. Guardar Padres en SQLite
        if parent_ids:
            self.docstore.add_documents(parent_ids, parent_contents, parent_metas)
            logger.info(f"[Ingest] Guardados {len(parent_ids)} chunks padres en DocStore.")

        # 4. Guardar Hijos en ChromaDB (Vectores)
        if child_ids:
            collection.add(
                ids=child_ids,
                documents=child_contents,
                metadatas=child_metas
            )

        return source_id

    # ---------------------------------------------------------
    # Búsqueda Avanzada: Multi-Query + RRF + Parent Retrieval
    # ---------------------------------------------------------
    def _generate_multi_queries(self, query: str, n=3) -> List[str]:
        """Usa el Modelo Configurado para generar variaciones de la pregunta."""
        try:
            prompt = f"""Eres un experto en búsqueda semántica. Genera {n} versiones diferentes de la siguiente pregunta de usuario para mejorar la recuperación de documentos desde diversas perspectivas.
            Pregunta original: "{query}"
            Responde SOLO con las variaciones, una por línea. No enumeres."""
            
            # Usar el modelo configurado
            model_to_use = self.settings.model
            
            response = self.llm_client.chat.completions.create(
                model=model_to_use, 
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            content = response.choices[0].message.content
            variations = [line.strip() for line in content.split('\n') if line.strip()]
            return [query] + variations[:n] # Incluir siempre la original
        except Exception as e:
            logger.error(f"Error generando multi-queries: {e}")
            return [query]

    def _reciprocal_rank_fusion(self, results_list: List[Dict], k=60):
        """
        Algoritmo RRF para fusionar resultados de múltiples queries.
        Score = 1 / (k + rank)
        """
        fused_scores = defaultdict(float)
        doc_map = {} # Para guardar metadata y contenido y no perderlo

        for results in results_list:
            # Chroma devuelve listas de listas, aplanamos
            if results['ids']:
                ids = results['ids'][0]
                # distances = results['distances'][0] (no lo usamos para RRF puro, usamos el rango)
                
                for rank, doc_id in enumerate(ids):
                    # RRF Formula
                    fused_scores[doc_id] += 1 / (k + rank)
                    
                    # Guardar referencia del documento si no existe
                    if doc_id not in doc_map:
                        idx = ids.index(doc_id)
                        doc_map[doc_id] = {
                            "content": results['documents'][0][idx],
                            "metadata": results['metadatas'][0][idx]
                        }

        # Ordenar por score RRF descendente
        sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
        
        final_results = []
        for doc_id in sorted_ids:
            item = doc_map[doc_id]
            item['id'] = doc_id
            item['score'] = fused_scores[doc_id]
            final_results.append(item)
            
        return final_results

    def search(self, collection_name: str, query: str, top_k: int = 5):
        """
        Flujo RAG Avanzado:
        1. Multi-Query Generation
        2. Vector Search en paralelo
        3. Reciprocal Rank Fusion
        4. Parent Document Lookup (recuperar el contexto completo)
        """
        collection = self._get_collection(collection_name)
        
        # 1. Generar variaciones de la query
        queries = self._generate_multi_queries(query)
        logger.info(f"[Search] Queries generadas: {queries}")

        # 2. Ejecutar búsquedas
        results_list = []
        for q in queries:
            res = collection.query(
                query_texts=[q],
                n_results=top_k * 2 # Traemos más candidatos para fusionar
            )
            results_list.append(res)

        # 3. Fusionar resultados (RRF)
        fused_results = self._reciprocal_rank_fusion(results_list)
        
        # 4. Resolver a Documentos Padres (Parent Retrieval)
        final_output = []
        seen_parents = set()
        
        for item in fused_results:
            if len(final_output) >= top_k:
                break
                
            parent_id = item['metadata'].get('parent_id')
            
            if parent_id and parent_id not in seen_parents:
                # Recuperar el texto completo del padre desde SQLite
                parent_doc = self.docstore.get_document(parent_id)
                if parent_doc:
                    final_output.append({
                        "content": parent_doc['content'], # Contexto rico
                        "metadata": parent_doc['metadata'],
                        "score": item['score'],
                        "retrieval_source": "parent_doc"
                    })
                    seen_parents.add(parent_id)
            elif not parent_id:
                # Si no tiene padre (chunk huerfano), devolvemos el hijo
                final_output.append(item)
                
            # If item has parent but parent doc not found (edge case), ignore or add child. 
            # Current logic ignores if parent_id exists but not found in docstore.

        return final_output

