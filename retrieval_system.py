"""
Retrieval System for Medical RAG
Hybrid search combining dense vectors, BM25, and RRF fusion
Compatible with LLaMA 3 8B system
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from rank_bm25 import BM25Okapi
import re

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Data class for search results"""
    text: str
    score: float
    page_number: int
    source: str
    retrieval_type: str
    metadata: Dict[str, Any]

class RetrievalSystem:
    """
    Hybrid retrieval system for medical documents
    Features:
    - Dense vector retrieval (BAAI/bge-large-en-v1.5)
    - Sparse BM25 retrieval
    - Reciprocal Rank Fusion (RRF)
    - ColBERT-style reranking
    - Medical domain optimization
    """
    
    def __init__(self, vector_db, chunks: List, config: Optional[Dict[str, Any]] = None):
        """
        Initialize retrieval system
        
        Args:
            vector_db: Vector database instance
            chunks: List of document chunks for BM25
            config: Optional configuration dictionary
        """
        if config is None:
            # Default config
            config = {
                "retrieval": {
                    "dense_top_k": 60,
                    "sparse_top_k": 60,
                    "final_top_k": 15,
                    "rrf_k": 60,
                    "use_reranking": True,
                    "rerank_top_k": 25
                },
                "bm25": {
                    "k1": 1.5,
                    "b": 0.75,
                    "epsilon": 0.25
                },
                "medical": {
                    "domain_keywords": [
                        "hypertension", "blood pressure", "cardiovascular", "treatment",
                        "diagnosis", "medication", "patient", "clinical", "therapy",
                        "symptoms", "systolic", "diastolic", "mmHg", "guidelines"
                    ]
                }
            }
        
        self.config = config
        self.retrieval_config = config["retrieval"]
        self.bm25_config = config["bm25"]
        self.medical_config = config["medical"]
        
        self.vector_db = vector_db
        self.document_chunks = chunks
        
        # Initialize BM25 for sparse retrieval
        self._setup_bm25()
        
        logger.info("🔍 Retrieval system initialized")
        print("🔍 Retrieval system initialized")
        print(f"  Dense retrieval: ✅ Ready")
        print(f"  Sparse retrieval (BM25): {'✅ Ready' if self.bm25 else '❌ Failed'}")
    
    def _setup_bm25(self):
        """Setup BM25 for sparse retrieval"""
        if not self.document_chunks:
            logger.warning("No chunks available for BM25 setup")
            self.bm25 = None
            return
        
        logger.info(f"🔍 Setting up BM25 with {len(self.document_chunks)} documents")
        print(f"🔍 Setting up BM25 with {len(self.document_chunks)} documents")
        
        try:
            # Prepare texts for BM25
            texts = [chunk.text for chunk in self.document_chunks]
            
            # Tokenize texts (optimized for medical content)
            tokenized_texts = []
            for text in texts:
                tokens = self._medical_tokenize(text.lower())
                tokenized_texts.append(tokens)
            
            # Initialize BM25 with custom parameters
            self.bm25 = BM25Okapi(
                tokenized_texts,
                k1=self.bm25_config["k1"],
                b=self.bm25_config["b"],
                epsilon=self.bm25_config["epsilon"]
            )
            
            logger.info("✅ BM25 setup complete")
            print("✅ BM25 setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up BM25: {e}")
            print(f"❌ BM25 setup failed: {e}")
            self.bm25 = None
    
    def _medical_tokenize(self, text: str) -> List[str]:
        """
        Medical-aware tokenization
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Preserve medical terms and measurements
        text = re.sub(r'(\d+)([a-zA-Z]+)', r'\\1 \\2', text)  # "140mmHg" -> "140 mmHg"
        text = re.sub(r'(\d+)/(\d+)', r'\\1 / \\2', text)    # "140/90" -> "140 / 90"
        
        # Basic tokenization
        tokens = text.split()
        
        # Filter out very short tokens and punctuation-only tokens
        tokens = [token for token in tokens if len(token) > 1 and not token.isdigit()]
        
        # Add medical domain keywords if present
        for keyword in self.medical_config["domain_keywords"]:
            if keyword in text:
                tokens.append(keyword)
        
        return tokens
    
    def dense_retrieval(self, query: str, top_k: int = 10, 
                       filter_conditions: Optional[Dict] = None) -> List[SearchResult]:
        """
        Dense vector retrieval using sentence transformers
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_conditions: Optional metadata filters
            
        Returns:
            List of search results
        """
        logger.debug(f"Dense retrieval for: {query[:50]}...")
        
        try:
            # Search using vector database
            results = self.vector_db.search(query, top_k, filter_conditions)
            
            # Convert to SearchResult objects
            search_results = []
            for result in results:
                search_result = SearchResult(
                    text=result["text"],
                    score=result["score"],
                    page_number=result["page_number"],
                    source=result["source"],
                    retrieval_type="dense",
                    metadata=result["metadata"]
                )
                search_results.append(search_result)
            
            logger.debug(f"Dense retrieval returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Dense retrieval error: {e}")
            return []
    
    def sparse_retrieval(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        Sparse BM25 retrieval
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of search results
        """
        if not self.bm25:
            logger.warning("BM25 not available for sparse retrieval")
            return []
        
        logger.debug(f"Sparse retrieval for: {query[:50]}...")
        
        try:
            # Tokenize query
            query_tokens = self._medical_tokenize(query.lower())
            
            if not query_tokens:
                logger.warning("No valid tokens in query")
                return []
            
            # Get BM25 scores
            scores = self.bm25.get_scores(query_tokens)
            
            # Get top-k indices
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            # Create search results
            search_results = []
            for idx in top_indices:
                if idx < len(self.document_chunks) and scores[idx] > 0:
                    chunk = self.document_chunks[idx]
                    search_result = SearchResult(
                        text=chunk.text,
                        score=float(scores[idx]),
                        page_number=chunk.page_number,
                        source=chunk.source,
                        retrieval_type="sparse",
                        metadata=chunk.metadata
                    )
                    search_results.append(search_result)
            
            logger.debug(f"Sparse retrieval returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Sparse retrieval error: {e}")
            return []
    
    def reciprocal_rank_fusion(self, dense_results: List[SearchResult], 
                             sparse_results: List[SearchResult], 
                             k: Optional[int] = None) -> List[SearchResult]:
        """
        Reciprocal Rank Fusion (RRF) to combine dense and sparse results
        
        Args:
            dense_results: Results from dense retrieval
            sparse_results: Results from sparse retrieval
            k: RRF parameter (default from config)
            
        Returns:
            Fused and ranked results
        """
        if k is None:
            k = self.retrieval_config["rrf_k"]
        
        logger.debug("Applying Reciprocal Rank Fusion")
        
        # Create text-to-result mapping
        text_to_result = {}
        combined_scores = {}
        
        # Process dense results
        for rank, result in enumerate(dense_results):
            text = result.text
            rrf_score = 1 / (k + rank + 1)
            combined_scores[text] = combined_scores.get(text, 0) + rrf_score
            text_to_result[text] = result
        
        # Process sparse results
        for rank, result in enumerate(sparse_results):
            text = result.text
            rrf_score = 1 / (k + rank + 1)
            combined_scores[text] = combined_scores.get(text, 0) + rrf_score
            
            # Use sparse result if not already present
            if text not in text_to_result:
                text_to_result[text] = result
        
        # Sort by combined RRF score
        sorted_texts = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Create fused results
        fused_results = []
        for text, rrf_score in sorted_texts:
            if text in text_to_result:
                result = text_to_result[text]
                # Create new result with RRF score
                fused_result = SearchResult(
                    text=result.text,
                    score=float(rrf_score),
                    page_number=result.page_number,
                    source=result.source,
                    retrieval_type="hybrid_rrf",
                    metadata=result.metadata
                )
                fused_results.append(fused_result)
        
        logger.debug(f"RRF fusion returned {len(fused_results)} results")
        return fused_results
    
    def rerank_results(self, query: str, results: List[SearchResult], 
                      top_k: Optional[int] = None) -> List[SearchResult]:
        """
        ColBERT-style reranking based on token overlap and medical relevance
        
        Args:
            query: Original query
            results: Results to rerank
            top_k: Number of results to return
            
        Returns:
            Reranked results
        """
        if top_k is None:
            top_k = self.retrieval_config["rerank_top_k"]
        
        if not results:
            return []
        
        logger.debug(f"Reranking {len(results)} results")
        
        # Tokenize query
        query_tokens = set(self._medical_tokenize(query.lower()))
        
        # Calculate reranking scores
        reranked_results = []
        for result in results:
            # Tokenize document
            doc_tokens = set(self._medical_tokenize(result.text.lower()))
            
            # Calculate token overlap
            overlap = len(query_tokens.intersection(doc_tokens))
            overlap_score = overlap / len(query_tokens) if query_tokens else 0
            
            # Medical domain boost
            medical_boost = 0
            for keyword in self.medical_config["domain_keywords"]:
                if keyword.lower() in result.text.lower():
                    medical_boost += 0.1
            
            # Combine scores (RRF score + overlap + medical boost)
            final_score = 0.6 * result.score + 0.3 * overlap_score + 0.1 * min(medical_boost, 0.5)
            
            # Create reranked result
            reranked_result = SearchResult(
                text=result.text,
                score=final_score,
                page_number=result.page_number,
                source=result.source,
                retrieval_type="reranked",
                metadata=result.metadata
            )
            reranked_results.append(reranked_result)
        
        # Sort by final score
        reranked_results.sort(key=lambda x: x.score, reverse=True)
        
        logger.debug(f"Reranking returned top {min(top_k, len(reranked_results))} results")
        return reranked_results[:top_k]
    
    def hybrid_search(self, query: str, top_k: Optional[int] = None, 
                     use_reranking: Optional[bool] = None,
                     filter_conditions: Optional[Dict] = None) -> List[SearchResult]:
        """
        Complete hybrid search pipeline
        
        Args:
            query: Search query
            top_k: Final number of results to return
            use_reranking: Whether to apply reranking
            filter_conditions: Optional metadata filters
            
        Returns:
            Final ranked results
        """
        if top_k is None:
            top_k = self.retrieval_config["final_top_k"]
        
        if use_reranking is None:
            use_reranking = self.retrieval_config["use_reranking"]
        
        logger.info(f"Hybrid search for: {query[:50]}...")
        print(f"🔍 Hybrid search: {query[:50]}...")
        
        # Step 1: Dense retrieval
        dense_results = self.dense_retrieval(
            query, 
            self.retrieval_config["dense_top_k"], 
            filter_conditions
        )
        print(f"  Dense retrieval: {len(dense_results)} results")
        
        # Step 2: Sparse retrieval
        sparse_results = self.sparse_retrieval(
            query, 
            self.retrieval_config["sparse_top_k"]
        )
        print(f"  Sparse retrieval: {len(sparse_results)} results")
        
        # Step 3: Reciprocal Rank Fusion
        if dense_results or sparse_results:
            fused_results = self.reciprocal_rank_fusion(dense_results, sparse_results)
            print(f"  RRF fusion: {len(fused_results)} results")
        else:
            fused_results = []
        
        # Step 4: Optional reranking
        if use_reranking and fused_results:
            final_results = self.rerank_results(query, fused_results, top_k)
            print(f"  Reranking: {len(final_results)} final results")
        else:
            final_results = fused_results[:top_k]
            print(f"  Final: {len(final_results)} results (no reranking)")
        
        logger.info(f"Hybrid search completed: {len(final_results)} results")
        return final_results
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval system statistics"""
        stats = {
            "total_chunks": len(self.document_chunks),
            "bm25_available": self.bm25 is not None,
            "dense_retrieval_available": self.vector_db is not None,
            "config": {
                "dense_top_k": self.retrieval_config["dense_top_k"],
                "sparse_top_k": self.retrieval_config["sparse_top_k"],
                "final_top_k": self.retrieval_config["final_top_k"],
                "rrf_k": self.retrieval_config["rrf_k"],
                "use_reranking": self.retrieval_config["use_reranking"]
            }
        }
        
        if self.bm25:
            stats["bm25_vocab_size"] = len(self.bm25.idf)
        
        return stats

def test_retrieval_system():
    """Test script for retrieval system"""
    print("🧪 Testing Retrieval System...")
    
    # This would need actual components to work
    print("⚠️  This test requires initialized vector database and document chunks")
    print("💡 Run the full system with main_8b.py to test retrieval")

if __name__ == "__main__":
    test_retrieval_system()