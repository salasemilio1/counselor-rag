import os
import json
import pickle
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging
import numpy as np
from datetime import datetime

# Vector database imports
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logging.warning("ChromaDB not available. Install with: pip install chromadb")

# Embedding imports
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("SentenceTransformers not available. Install with: pip install sentence-transformers")

from document_loader import DocumentLoader, DocumentChunk
from llm_wrapper import LLMWrapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGEngine:
    """Main RAG engine for client-specific document retrieval and generation"""
    
    def __init__(
        self,
        data_dir: str = "data",
        embedding_model: str = "all-MiniLM-L6-v2",
        vector_db_path: str = "data/vector_db",
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ):
        self.data_dir = Path(data_dir)
        self.embedding_model_name = embedding_model
        self.vector_db_path = Path(vector_db_path)
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        
        # Initialize components
        self.llm_wrapper = LLMWrapper()
        self.document_loader = DocumentLoader(data_dir, self.llm_wrapper)
        self.embedding_model = None
        self.vector_db = None
        
        # Initialize embedding model and vector database
        self._initialize_embedding_model()
        self._initialize_vector_database()
        
        # Client-specific collections cache
        self.client_collections = {}
    
    def _initialize_embedding_model(self):
        """Initialize the sentence transformer model for embeddings"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("SentenceTransformers required. Install with: pip install sentence-transformers")
        
        try:
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Loaded embedding model: {self.embedding_model_name}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            raise
    
    def _initialize_vector_database(self):
        """Initialize ChromaDB for vector storage"""
        if not CHROMA_AVAILABLE:
            logger.warning("ChromaDB not available, using in-memory fallback")
            self.vector_db = InMemoryVectorDB()
            return
        
        try:
            # Create vector DB directory
            self.vector_db_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB client
            self.chroma_client = chromadb.PersistentClient(
                path=str(self.vector_db_path),
                settings=Settings(anonymized_telemetry=False)
            )
            
            logger.info(f"Initialized ChromaDB at {self.vector_db_path}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {e}")
            logger.info("Falling back to in-memory vector storage")
            self.vector_db = InMemoryVectorDB()
    
    def _get_client_collection(self, client_id: str):
        """Get or create a ChromaDB collection for a specific client"""
        if not CHROMA_AVAILABLE:
            return self.vector_db
        
        collection_name = f"client_{client_id}"
        
        if collection_name not in self.client_collections:
            try:
                # Try to get existing collection
                collection = self.chroma_client.get_collection(collection_name)
            except Exception:
                # Create new collection if it doesn't exist
                collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"client_id": client_id}
                )
            
            self.client_collections[collection_name] = collection
        
        return self.client_collections[collection_name]
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a text"""
        try:
            embedding = self.embedding_model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return []
    
    def ingest_client_documents(self, client_id: str, force_reprocess: bool = False) -> bool:
        """Ingest all documents for a specific client into vector database"""
        try:
            logger.info(f"Starting ingestion for client: {client_id}")

            # Process documents using document loader
            chunks = self.document_loader.process_client_documents(client_id, force_reprocess)

            if not chunks:
                logger.warning(f"No chunks to process for client {client_id}")
                return False

            # Get client collection
            collection = self._get_client_collection(client_id)

            # Prepare data for batch insertion
            chunk_ids = []
            embeddings = []
            documents = []
            metadatas = []

            for chunk in chunks:
                # Generate embedding
                if chunk.embedding is None:
                    embedding = self.embed_text(chunk.content)
                if not embedding:
                    continue

                chunk_ids.append(chunk.chunk_id)
                embeddings.append(embedding)
                documents.append(chunk.content)
                metadatas.append(chunk.metadata)

            # DEBUG: Dump processed chunks and metadata to local JSON for inspection
            import json
            with open(f"debug_{client_id}_chunks.json", "w", encoding="utf-8") as debug_file:
                json.dump([
                    {
                        "chunk_id": chunk_ids[i],
                        "content": documents[i][:200],
                        "metadata": metadatas[i]
                    }
                    for i in range(len(chunk_ids))
                ], debug_file, indent=2)

            if CHROMA_AVAILABLE:
                # Check if documents already exist and remove them
                existing_ids = set()
                try:
                    existing_data = collection.get()
                    existing_ids = set(existing_data['ids'])
                except Exception:
                    pass

                # Remove existing documents if reprocessing
                if force_reprocess and existing_ids:
                    ids_to_delete = [id for id in chunk_ids if id in existing_ids]
                    if ids_to_delete:
                        collection.delete(ids=ids_to_delete)

                # Filter out existing documents if not reprocessing
                if not force_reprocess:
                    new_data = []
                    for i, chunk_id in enumerate(chunk_ids):
                        if chunk_id not in existing_ids:
                            new_data.append((chunk_id, embeddings[i], documents[i], metadatas[i]))

                    if new_data:
                        chunk_ids, embeddings, documents, metadatas = zip(*new_data)
                    else:
                        logger.info(f"All documents for client {client_id} already exist in vector DB")
                        return True

                # Ensure Chroma-compatible metadata values
                for meta in metadatas:
                    for key, value in meta.items():
                        if isinstance(value, list):
                            meta[key] = ", ".join(str(v) for v in value)

                # Add documents to collection
                collection.add(
                    ids=chunk_ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
            else:
                # Use in-memory fallback
                for i, chunk_id in enumerate(chunk_ids):
                    self.vector_db.add(
                        client_id=client_id,
                        chunk_id=chunk_id,
                        embedding=embeddings[i],
                        content=documents[i],
                        metadata=metadatas[i]
                    )

            logger.info(f"Successfully ingested {len(chunk_ids)} chunks for client {client_id}")
            return True

        except Exception as e:
            logger.error(f"Error ingesting documents for client {client_id}: {e}")
            return False
    
    def retrieve_relevant_chunks(
        self,
        client_id: str,
        query: str,
        meeting_id: str = None,
        top_k: int = None
    ) -> List[Dict]:
        """Retrieve relevant chunks for a query from client's documents"""
        try:
            if top_k is None:
                top_k = self.top_k
            
            # Generate query embedding
            query_embedding = self.embed_text(query)
            if not query_embedding:
                return []
            
            # Get client collection
            collection = self._get_client_collection(client_id)
            
            if CHROMA_AVAILABLE:
                # Prepare where clause for meeting filtering
                where_clause = None
                if meeting_id:
                    where_clause = {"meeting_id": meeting_id}
                
                # Query the collection
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where_clause
                )
                
                # Format results
                relevant_chunks = []
                if results['documents'] and results['documents'][0]:
                    for i in range(len(results['documents'][0])):
                        chunk = {
                            'content': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i],
                            'distance': results['distances'][0][i] if results['distances'] else 0,
                            'id': results['ids'][0][i]
                        }
                        relevant_chunks.append(chunk)
                
            else:
                # Use in-memory fallback
                relevant_chunks = self.vector_db.query(
                    client_id=client_id,
                    query_embedding=query_embedding,
                    meeting_id=meeting_id,
                    top_k=top_k
                )
            
            # Filter by similarity threshold
            filtered_chunks = [
                chunk for chunk in relevant_chunks
                if chunk.get('distance', 0) <= (1 - self.similarity_threshold)
            ]
            
            logger.info(f"Retrieved {len(filtered_chunks)} relevant chunks for query")
            return filtered_chunks
            
        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []
    
    def generate_response(self, client_id: str, query: str, meeting_id: str = None) -> Dict:
        """Generate response using RAG pipeline"""
        try:
            # Retrieve relevant chunks
            relevant_chunks = self.retrieve_relevant_chunks(client_id, query, meeting_id)
            
            if not relevant_chunks:
                return {
                    'answer': f"I don't have any relevant information about {query} for this client.",
                    'sources': [],
                    'confidence': 0.0
                }
            
            # Prepare context from retrieved chunks
            context_parts = []
            sources = []
            
            for chunk in relevant_chunks:
                context_parts.append(chunk['content'])
                sources.append({
                    'meeting_id': chunk['metadata'].get('meeting_id', 'unknown'),
                    'date': chunk['metadata'].get('date', 'unknown'),
                    'chunk_id': chunk['id']
                })
            
            context = "\n\n".join(context_parts)
            
            # Generate response using LLM
            prompt = self._create_rag_prompt(query, context, client_id)
            response = self.llm_wrapper.generate_response(prompt)
            
            # Calculate confidence based on chunk similarities
            avg_similarity = np.mean([1 - chunk.get('distance', 1) for chunk in relevant_chunks])
            
            return {
                'answer': response,
                'sources': sources,
                'confidence': float(avg_similarity),
                'chunks_used': len(relevant_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'answer': "I encountered an error while processing your query.",
                'sources': [],
                'confidence': 0.0
            }
    
    def _create_rag_prompt(self, query: str, context: str, client_id: str) -> str:
        """Create a prompt for the LLM using retrieved context"""
        prompt = f"""You are a helpful assistant for a counselor. You have access to meeting notes for client {client_id}.

Based on the following meeting notes, please answer the counselor's question. Be specific and reference relevant details from the notes. If you can't find the answer in the provided context, say so clearly.

Meeting Notes Context:
{context}

Counselor's Question: {query}

Please provide a helpful and accurate response based only on the information in the meeting notes above."""

        return prompt
    
    def get_client_summary(self, client_id: str) -> Dict:
        """Get summary information about a client's documents"""
        try:
            meetings = self.document_loader.get_client_meetings(client_id)
            
            if CHROMA_AVAILABLE:
                collection = self._get_client_collection(client_id)
                try:
                    count_result = collection.count()
                    total_chunks = count_result
                except Exception:
                    total_chunks = 0
            else:
                total_chunks = self.vector_db.get_client_chunk_count(client_id)
            
            return {
                'client_id': client_id,
                'total_meetings': len(meetings),
                'total_chunks': total_chunks,
                'meetings': meetings
            }
            
        except Exception as e:
            logger.error(f"Error getting client summary: {e}")
            return {'client_id': client_id, 'error': str(e)}


class InMemoryVectorDB:
    """Fallback in-memory vector database when ChromaDB is not available"""
    
    def __init__(self):
        self.data = {}  # client_id -> list of chunks
    
    def add(self, client_id: str, chunk_id: str, embedding: List[float], content: str, metadata: Dict):
        """Add a chunk to the database"""
        if client_id not in self.data:
            self.data[client_id] = []
        
        chunk_data = {
            'id': chunk_id,
            'embedding': np.array(embedding),
            'content': content,
            'metadata': metadata
        }
        
        # Remove existing chunk with same ID
        self.data[client_id] = [c for c in self.data[client_id] if c['id'] != chunk_id]
        self.data[client_id].append(chunk_data)
    
    def query(self, client_id: str, query_embedding: List[float], meeting_id: str = None, top_k: int = 5) -> List[Dict]:
        """Query the database for similar chunks"""
        if client_id not in self.data:
            return []
        
        query_vec = np.array(query_embedding)
        results = []
        
        for chunk in self.data[client_id]:
            # Filter by meeting ID if specified
            if meeting_id and chunk['metadata'].get('meeting_id') != meeting_id:
                continue
            
            # Calculate cosine similarity
            chunk_vec = chunk['embedding']
            similarity = np.dot(query_vec, chunk_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec))
            distance = 1 - similarity
            
            results.append({
                'content': chunk['content'],
                'metadata': chunk['metadata'],
                'distance': distance,
                'id': chunk['id']
            })
        
        # Sort by distance and return top_k
        results.sort(key=lambda x: x['distance'])
        return results[:top_k]
    
    def get_client_chunk_count(self, client_id: str) -> int:
        """Get number of chunks for a client"""
        return len(self.data.get(client_id, []))

