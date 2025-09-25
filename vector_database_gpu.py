"""
GPU-Optimized Vector Database Manager for Medical RAG System
Qdrant integration with CUDA acceleration for RTX 5060 Ti
"""

import logging
import numpy as np
import torch
from typing import List, Dict, Any, Optional, Tuple
import uuid
from dataclasses import asdict

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from config_8b import get_config, optimize_gpu_for_8b
from document_processor import DocumentChunk

logger = logging.getLogger(__name__)

class GPUVectorDatabase:
    """
    GPU-optimized vector database manager using Qdrant
    Features:
    - BAAI/bge-large-en-v1.5 embeddings with CUDA acceleration
    - Batch processing optimized for RTX 5060 Ti
    - Mixed precision inference (FP16)
    - GPU memory management
    - Fast embedding generation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize GPU-optimized vector database
        
        Args:
            config: Optional configuration dictionary
        """
        if config is None:
            config = get_config()
        
        self.config = config
        self.qdrant_config = config["qdrant"]
        self.embedding_config = config["embedding"]
        self.system_config = config["system"]
        self.gpu_config = config["gpu"]
        
        # GPU optimization
        self.device = torch.device("cuda" if torch.cuda.is_available() and self.gpu_config["enable_gpu"] else "cpu")
        print(f"🔥 Using device: {self.device}")
        
        if self.device.type == "cuda":
            optimize_gpu_for_8b()
            # Set memory fraction
            if self.embedding_config.get("gpu_memory_fraction"):
                torch.cuda.set_per_process_memory_fraction(self.embedding_config["gpu_memory_fraction"])
        
        # Initialize Qdrant client
        if self.qdrant_config.get("use_local_qdrant", False):
            self.client = QdrantClient(url=self.qdrant_config["qdrant_url"])
            logger.info(f"Connected to local Qdrant at {self.qdrant_config['qdrant_url']}")
            print(f"🔗 Connected to local Qdrant at {self.qdrant_config['qdrant_url']}")
        else:
            self.client = QdrantClient(":memory:")
            logger.info("Using in-memory Qdrant")
            print("🧠 Using in-memory Qdrant")
        
        self.collection_name = self.qdrant_config["collection_name"]
        
        # Initialize embedding model with GPU acceleration
        logger.info(f"Loading GPU-optimized embedding model: {self.embedding_config['model_name']}")
        print(f"🔢 Loading GPU-optimized embedding model: {self.embedding_config['model_name']}")
        
        try:
            self.embedding_model = SentenceTransformer(
                self.embedding_config["model_name"],
                device=str(self.device)
            )
            
            # Enable mixed precision if supported
            if self.device.type == "cuda" and self.gpu_config["mixed_precision"]:
                try:
                    self.embedding_model.half()  # Convert to FP16
                    print("⚡ Enabled mixed precision (FP16) for faster inference")
                    logger.info("Enabled mixed precision (FP16)")
                except Exception as e:
                    print(f"⚠️  Mixed precision not supported: {e}")
                    logger.warning(f"Mixed precision not supported: {e}")
            
            # Get embedding dimension
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            logger.info(f"Embedding dimension: {self.embedding_dim}")
            print(f"📐 Embedding dimension: {self.embedding_dim}")
            
            # Create collection
            self.create_collection()
            
            # Monitor GPU usage
            if self.device.type == "cuda":
                self._log_gpu_memory()
                
        except Exception as e:
            logger.error(f"Error initializing embedding model: {e}")
            print(f"❌ Error initializing embedding model: {e}")
            raise
    
    def _log_gpu_memory(self):
        """Log GPU memory usage"""
        if self.device.type == "cuda":
            memory_allocated = torch.cuda.memory_allocated() / 1024**3
            memory_reserved = torch.cuda.memory_reserved() / 1024**3
            memory_total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            print(f"🎮 GPU Memory - Allocated: {memory_allocated:.2f}GB, Reserved: {memory_reserved:.2f}GB, Total: {memory_total:.1f}GB")
            logger.info(f"GPU memory - Allocated: {memory_allocated:.2f}GB, Reserved: {memory_reserved:.2f}GB")
    
    def create_collection(self):
        """Create Qdrant collection with medical document configuration"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name in collection_names:
                logger.info(f"Collection '{self.collection_name}' already exists")
                print(f"ℹ️  Collection '{self.collection_name}' already exists")
                return
            
            # Create new collection with optimized settings
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            
            logger.info(f"✅ Created collection: {self.collection_name}")
            print(f"✅ Created collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            print(f"❌ Error creating collection: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str], batch_size: Optional[int] = None) -> np.ndarray:
        """
        Generate embeddings with GPU acceleration and optimized batching
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            Numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        if batch_size is None:
            batch_size = self.embedding_config["batch_size"]
        
        # Adjust batch size based on GPU memory and text length
        if self.device.type == "cuda":
            # Estimate memory usage and adjust batch size
            avg_text_length = sum(len(text) for text in texts) / len(texts)
            if avg_text_length > 800:  # Long texts
                batch_size = max(batch_size // 2, 8)
            elif len(texts) > 1000:  # Many texts
                batch_size = min(batch_size * 2, 128)
        
        logger.info(f"Generating embeddings for {len(texts)} texts with batch size {batch_size}")
        print(f"🔢 Generating embeddings for {len(texts)} texts (batch size: {batch_size})")
        
        try:
            # Clear GPU cache before processing
            if self.device.type == "cuda":
                torch.cuda.empty_cache()
                self._log_gpu_memory()
            
            # Generate embeddings with GPU optimization
            embeddings = self.embedding_model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=self.embedding_config["normalize_embeddings"],
                device=str(self.device)
            )
            
            logger.info(f"✅ Generated {embeddings.shape[0]} embeddings on {self.device}")
            print(f"✅ Generated {embeddings.shape[0]} embeddings on {self.device}")
            
            # Log GPU memory after processing
            if self.device.type == "cuda":
                self._log_gpu_memory()
            
            return embeddings
            
        except torch.cuda.OutOfMemoryError as e:
            logger.error(f"GPU out of memory: {e}")
            print(f"❌ GPU out of memory. Trying smaller batch size...")
            
            # Retry with smaller batch size
            smaller_batch = batch_size // 2
            if smaller_batch > 0:
                torch.cuda.empty_cache()
                return self.generate_embeddings(texts, smaller_batch)
            else:
                raise
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            print(f"❌ Error generating embeddings: {e}")
            raise
    
    def index_documents(self, chunks: List[DocumentChunk]) -> bool:
        """
        Index document chunks with GPU-optimized processing
        
        Args:
            chunks: List of document chunks to index
            
        Returns:
            Success status
        """
        if not chunks:
            logger.warning("No chunks to index")
            print("⚠️  No chunks to index")
            return False
        
        logger.info(f"🚀 GPU-accelerated indexing of {len(chunks)} document chunks")
        print(f"🚀 GPU-accelerated indexing of {len(chunks)} document chunks")
        
        try:
            import time
            start_time = time.time()
            
            # Extract texts for embedding
            texts = [chunk.text for chunk in chunks]
            
            # Generate embeddings with GPU acceleration
            print("⚡ Generating embeddings with GPU acceleration...")
            embeddings = self.generate_embeddings(texts)
            
            if embeddings.size == 0:
                logger.error("Failed to generate embeddings")
                return False
            
            embedding_time = time.time() - start_time
            print(f"🔥 Embedding generation completed in {embedding_time:.2f}s")
            
            # Create points for Qdrant
            print("💾 Preparing vectors for database...")
            points = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Create payload with metadata
                payload = {
                    "text": chunk.text,
                    "page_number": chunk.page_number,
                    "source": chunk.source,
                    "chunk_hash": chunk.chunk_hash,
                    "chunk_type": chunk.chunk_type,
                    "word_count": chunk.metadata.get("word_count", 0),
                    "char_count": chunk.metadata.get("char_count", 0),
                    "file_name": chunk.metadata.get("file_name", ""),
                    "medical_entities": chunk.metadata.get("medical_entities", {})
                }
                
                # Create point
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.tolist(),
                    payload=payload
                )
                
                points.append(point)
            
            # Upload points in optimized batches
            batch_size = 200 if self.device.type == "cuda" else 100  # Larger batches with GPU
            total_batches = (len(points) + batch_size - 1) // batch_size
            logger.info(f"Uploading in {total_batches} batches of size {batch_size}")
            
            upload_start = time.time()
            for i in tqdm(range(0, len(points), batch_size), desc="Uploading vectors"):
                batch = points[i:i + batch_size]
                
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
            
            upload_time = time.time() - upload_start
            total_time = time.time() - start_time
            
            logger.info(f"✅ Successfully indexed {len(chunks)} chunks")
            print(f"✅ Successfully indexed {len(chunks)} chunks")
            print(f"⚡ Total time: {total_time:.2f}s (Embedding: {embedding_time:.2f}s, Upload: {upload_time:.2f}s)")
            print(f"🔥 Average speed: {len(chunks)/total_time:.1f} chunks/second")
            
            # Final GPU memory check
            if self.device.type == "cuda":
                self._log_gpu_memory()
                torch.cuda.empty_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            print(f"❌ Error indexing documents: {e}")
            
            # Clean up GPU memory on error
            if self.device.type == "cuda":
                torch.cuda.empty_cache()
            
            return False
    
    def search(self, query: str, top_k: int = 10, filter_conditions: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        GPU-accelerated search for similar documents
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_conditions: Optional metadata filters
            
        Returns:
            List of search results
        """
        try:
            # Generate query embedding with GPU
            query_embedding = self.embedding_model.encode([query], device=str(self.device))[0]
            
            # Prepare search filter if provided
            search_filter = None
            if filter_conditions:
                conditions = []
                for field, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(
                            key=field,
                            match=MatchValue(value=value)
                        )
                    )
                search_filter = Filter(must=conditions)
            
            # Perform search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding.tolist(),
                limit=top_k,
                query_filter=search_filter,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            results = []
            for result in search_results:
                result_dict = {
                    "id": result.id,
                    "score": result.score,
                    "text": result.payload["text"],
                    "page_number": result.payload["page_number"],
                    "source": result.payload["source"],
                    "metadata": {
                        "chunk_hash": result.payload["chunk_hash"],
                        "chunk_type": result.payload["chunk_type"],
                        "word_count": result.payload["word_count"],
                        "char_count": result.payload["char_count"],
                        "file_name": result.payload["file_name"],
                        "medical_entities": result.payload.get("medical_entities", {})
                    }
                }
                results.append(result_dict)
            
            logger.info(f"Found {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error searching: {e}")
            print(f"❌ Search error: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection information"""
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "collection_name": self.collection_name,
                "vectors_count": collection_info.vectors_count or 0,
                "indexed_vectors_count": collection_info.indexed_vectors_count or 0,
                "points_count": collection_info.points_count or 0,
                "status": collection_info.status.name if collection_info.status else "unknown"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_gpu_stats(self) -> Dict[str, Any]:
        """Get GPU statistics and performance metrics"""
        stats = {
            "device": str(self.device),
            "gpu_available": self.device.type == "cuda"
        }
        
        if self.device.type == "cuda":
            props = torch.cuda.get_device_properties(0)
            stats.update({
                "gpu_name": props.name,
                "gpu_memory_total_gb": props.total_memory / 1024**3,
                "gpu_memory_allocated_gb": torch.cuda.memory_allocated() / 1024**3,
                "gpu_memory_reserved_gb": torch.cuda.memory_reserved() / 1024**3,
                "gpu_compute_capability": f"{props.major}.{props.minor}",
                "gpu_multiprocessors": props.multi_processor_count,
                "mixed_precision_enabled": self.gpu_config["mixed_precision"],
                "embedding_batch_size": self.embedding_config["batch_size"]
            })
        
        return stats

def test_gpu_vector_database():
    """Test script for GPU-optimized vector database"""
    print("🧪 Testing GPU-Optimized Vector Database...")
    
    from document_processor import DocumentProcessor
    
    # Initialize components
    vector_db = GPUVectorDatabase()
    doc_processor = DocumentProcessor()
    
    # Show GPU stats
    gpu_stats = vector_db.get_gpu_stats()
    print(f"\\n🎮 GPU Statistics:")
    for key, value in gpu_stats.items():
        print(f"  {key}: {value}")
    
    # Process documents
    chunks = doc_processor.process_directory()
    
    if chunks:
        # Benchmark indexing
        import time
        start_time = time.time()
        
        success = vector_db.index_documents(chunks)
        
        indexing_time = time.time() - start_time
        
        if success:
            print(f"\\n🔥 GPU Indexing Performance:")
            print(f"  Total chunks: {len(chunks)}")
            print(f"  Indexing time: {indexing_time:.2f}s")
            print(f"  Speed: {len(chunks)/indexing_time:.1f} chunks/second")
            
            # Test search performance
            test_queries = [
                "What is hypertension classification?",
                "How to measure blood pressure accurately?",
                "Treatment goals for blood pressure"
            ]
            
            print(f"\\n🔍 GPU Search Performance:")
            for query in test_queries:
                search_start = time.time()
                results = vector_db.search(query, top_k=5)
                search_time = time.time() - search_start
                
                print(f"  Query: '{query[:30]}...'")
                print(f"  Results: {len(results)}, Time: {search_time:.3f}s")
                
                if results:
                    print(f"  Top result score: {results[0]['score']:.4f}")
                print()
            
            # Final GPU stats
            final_stats = vector_db.get_gpu_stats()
            print(f"🎮 Final GPU Memory:")
            if final_stats["gpu_available"]:
                print(f"  Allocated: {final_stats['gpu_memory_allocated_gb']:.2f}GB")
                print(f"  Reserved: {final_stats['gpu_memory_reserved_gb']:.2f}GB")
        else:
            print("❌ Failed to index documents")
    else:
        print("❌ No documents to test with")

if __name__ == "__main__":
    test_gpu_vector_database()