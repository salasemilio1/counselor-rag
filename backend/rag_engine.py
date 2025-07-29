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
        """Retrieve relevant chunks for a query from client's documents with improved ranking"""
    
        def _extract_query_entities(query_text: str) -> List[str]:
            """Extract key entities and terms from query for enhanced matching"""
            import re

            # Common counseling-related keywords that should boost relevance
            counseling_keywords = [
                'anxiety', 'depression', 'stress', 'therapy', 'session', 'progress',
                'goals', 'challenge', 'struggle', 'improvement', 'breakthrough',
                'relationship', 'family', 'work', 'career', 'emotional', 'feelings',
                'coping', 'strategies', 'techniques', 'homework', 'assignment'
            ]

            query_lower = query_text.lower()
            entities = []

            # Extract quoted phrases
            quoted_phrases = re.findall(r'"([^"]*)"', query_text)
            entities.extend(quoted_phrases)

            # Extract capitalized words (potential names, places)
            capitalized = re.findall(r'\b[A-Z][a-z]+\b', query_text)
            entities.extend(capitalized)

            # Extract counseling keywords present in query
            for keyword in counseling_keywords:
                if keyword in query_lower:
                    entities.append(keyword)

            # Extract meaningful words (longer than 3 chars, not common stop words)
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'was', 'were', 'is', 'are', 'what', 'when', 'where', 'how', 'why', 'did', 'does', 'will', 'would', 'could', 'should'}
            words = re.findall(r'\b\w{4,}\b', query_lower)
            meaningful_words = [w for w in words if w not in stop_words]
            entities.extend(meaningful_words)

            return list(set(entities))  # Remove duplicates

        def _rerank_chunks_with_keyword_matching(chunks: List[Dict], query_entities: List[str]) -> List[Dict]:
            """Re-rank chunks based on keyword matching and metadata relevance"""
            for chunk in chunks:
                content_lower = chunk['content'].lower()
                metadata = chunk.get('metadata', {})

                # Base score from vector similarity (convert distance to similarity)
                vector_similarity = 1 - chunk.get('distance', 1)

                # Keyword matching score
                keyword_matches = sum(1 for entity in query_entities if entity.lower() in content_lower)
                keyword_score = min(keyword_matches / max(len(query_entities), 1), 1.0)

                # Metadata relevance boost
                metadata_boost = 0

                # Boost recent meetings
                if 'date' in metadata:
                    try:
                        from datetime import datetime, timedelta
                        meeting_date = datetime.strptime(metadata['date'], '%Y-%m-%d')
                        days_ago = (datetime.now() - meeting_date).days
                        if days_ago <= 7:
                            metadata_boost += 0.15  # Recent meeting boost
                        elif days_ago <= 30:
                            metadata_boost += 0.10
                        elif days_ago <= 90:
                            metadata_boost += 0.05
                    except:
                        pass
                    
                # Boost chunks from specific meetings if relevant
                if 'title' in metadata and any(term in metadata['title'].lower() for term in ['breakthrough', 'crisis', 'important', 'significant']):
                    metadata_boost += 0.1

                # Composite score: weighted combination
                composite_score = (
                    0.6 * vector_similarity +      # Vector similarity weight
                    0.3 * keyword_score +          # Keyword matching weight  
                    0.1 * metadata_boost           # Metadata relevance weight
                )

                chunk['composite_score'] = composite_score
                chunk['keyword_matches'] = keyword_matches
                chunk['vector_similarity'] = vector_similarity

            # Sort by composite score (descending)
            chunks.sort(key=lambda x: x['composite_score'], reverse=True)
            return chunks

        def _apply_diversity_filtering(chunks: List[Dict], max_chunks_per_meeting: int = 3) -> List[Dict]:
            """Apply diversity filtering to avoid over-representation from single meetings"""
            if not chunks:
                return chunks

            meeting_counts = {}
            filtered_chunks = []

            for chunk in chunks:
                meeting_id_from_chunk = chunk.get('metadata', {}).get('meeting_id', 'unknown')
                current_count = meeting_counts.get(meeting_id_from_chunk, 0)

                if current_count < max_chunks_per_meeting:
                    filtered_chunks.append(chunk)
                    meeting_counts[meeting_id_from_chunk] = current_count + 1

            return filtered_chunks

        def _apply_dynamic_threshold(chunks: List[Dict], min_chunks: int = 2) -> List[Dict]:
            """Apply dynamic similarity threshold based on query results quality"""
            if not chunks:
                return chunks

            # Calculate score statistics
            scores = [chunk['composite_score'] for chunk in chunks]
            if not scores:
                return chunks

            mean_score = sum(scores) / len(scores)
            max_score = max(scores)

            # Dynamic threshold: more lenient if top results are poor, stricter if good
            if max_score > 0.8:
                # High quality results available, be more selective
                threshold = max(0.6, mean_score)
            elif max_score > 0.6:
                # Medium quality results, moderate threshold
                threshold = max(0.4, mean_score * 0.8)
            else:
                # Lower quality results, be more lenient
                threshold = max(0.3, mean_score * 0.6)

            # Apply threshold but ensure minimum chunks
            filtered = [chunk for chunk in chunks if chunk['composite_score'] >= threshold]

            # If too few chunks pass threshold, take top min_chunks anyway
            if len(filtered) < min_chunks and len(chunks) >= min_chunks:
                filtered = chunks[:min_chunks]

            return filtered

        try:
            if top_k is None:
                top_k = self.top_k

            # Expand initial retrieval to allow for better re-ranking
            initial_top_k = min(top_k * 3, 20)  # Get more candidates for re-ranking

            # Generate query embedding
            query_embedding = self.embed_text(query)
            if not query_embedding:
                return []

            # Extract query entities for enhanced matching
            query_entities = _extract_query_entities(query)
            logger.info(f"Extracted query entities: {query_entities}")

            # Get client collection
            collection = self._get_client_collection(client_id)

            if CHROMA_AVAILABLE:
                # Prepare where clause for meeting filtering
                where_clause = None
                if meeting_id:
                    where_clause = {"meeting_id": meeting_id}

                # Query the collection with expanded results
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=initial_top_k,
                    where=where_clause
                )

                # Format raw results
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

                logger.info(f"Retrieved {len(relevant_chunks)} raw chunks for query before re-ranking.")

            else:
                # Use in-memory fallback
                relevant_chunks = self.vector_db.query(
                    client_id=client_id,
                    query_embedding=query_embedding,
                    meeting_id=meeting_id,
                    top_k=initial_top_k
                )
                logger.info(f"Retrieved {len(relevant_chunks)} raw chunks for query before re-ranking (in-memory fallback).")

            if not relevant_chunks:
                return []

            # Apply enhanced re-ranking
            reranked_chunks = _rerank_chunks_with_keyword_matching(relevant_chunks, query_entities)
            logger.info(f"Re-ranked chunks by composite scoring")

            # Apply diversity filtering to avoid over-representation
            diverse_chunks = _apply_diversity_filtering(reranked_chunks, max_chunks_per_meeting=2)
            logger.info(f"Applied diversity filtering: {len(diverse_chunks)} chunks after diversity filtering")

            # Apply dynamic threshold
            final_chunks = _apply_dynamic_threshold(diverse_chunks, min_chunks=2)

            # Limit to requested top_k
            final_chunks = final_chunks[:top_k]

            # Log final results with scores
            logger.info(f"Final result: {len(final_chunks)} chunks after all filtering and ranking")
            for i, chunk in enumerate(final_chunks[:3]):  # Log top 3 for debugging
                logger.info(f"Chunk {i+1}: composite_score={chunk.get('composite_score', 0):.3f}, "
                           f"vector_sim={chunk.get('vector_similarity', 0):.3f}, "
                           f"keyword_matches={chunk.get('keyword_matches', 0)}")

            return final_chunks

        except Exception as e:
            logger.error(f"Error retrieving chunks: {e}")
            return []
    
    def generate_response(self, client_id: str, query: str, meeting_id: str = None) -> Dict:
        """Generate a RAG-based response to a counselor query."""
        try:
            # Step 1: Retrieve chunks
            relevant_chunks = self.retrieve_relevant_chunks(client_id, query, meeting_id)

            if not relevant_chunks:
                return {
                    'answer': f"I don't have any relevant information about '{query}' for this client.",
                    'sources': [],
                    'confidence': 0.0,
                    'chunks_used': 0
                }

            # Step 2: Construct context and prompt
            context = "\n\n".join(chunk['content'] for chunk in relevant_chunks)
            sources = [
                {
                    'meeting_id': chunk['metadata'].get('meeting_id', 'unknown'),
                    'date': chunk['metadata'].get('date', 'unknown'),
                    'chunk_id': chunk['id']
                } for chunk in relevant_chunks
            ]

            client_name = client_id.capitalize()
            prompt = self.llm_wrapper.build_structured_prompt(query, context, client_name)
            response = self.llm_wrapper.generate_text(prompt)

            # Step 4: Score
            avg_similarity = np.mean([
                max(0.0, min(1.0, 1 - chunk.get('distance', 1)))
                for chunk in relevant_chunks
            ])

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
                'confidence': 0.0,
                'chunks_used': 0
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

