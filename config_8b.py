"""
Medical RAG System Configuration - GPU Optimized for LLaMA 3 8B
Optimized for Ryzen 7 5700X + RTX 5060 Ti 16GB with LLaMA 3 8B model
"""

import os
import torch
from pathlib import Path
from typing import Dict, Any

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# CUDA Detection and Configuration
CUDA_AVAILABLE = torch.cuda.is_available()
GPU_NAME = torch.cuda.get_device_name(0) if CUDA_AVAILABLE else "No GPU"
GPU_MEMORY = torch.cuda.get_device_properties(0).total_memory / (1024**3) if CUDA_AVAILABLE else 0

print(f"🔥 CUDA Available: {CUDA_AVAILABLE}")
if CUDA_AVAILABLE:
    print(f"🎮 GPU: {GPU_NAME}")
    print(f"💾 GPU Memory: {GPU_MEMORY:.1f} GB")

# LLaMA/Ollama configuration - Optimized for LLaMA 3 8B
OLLAMA_CONFIG = {
    "model_name": "llama3:8b",  # Your existing LLaMA 3 8B model
    "base_url": "http://localhost:11434",
    "timeout": 120,  # Increased for 8B model
    "max_tokens": 2048,  # Increased for better medical answers
    "temperature": 0.1,  # Low for medical accuracy
    "top_p": 0.9,
    "repeat_penalty": 1.1,
    "gpu_acceleration": True,
    "gpu_memory_fraction": 0.7,  # 8B model needs more memory
    "context_length": 4096  # Increased context for medical guidelines
}

# Embedding model configuration - GPU accelerated
EMBEDDING_CONFIG = {
    "model_name": "BAAI/bge-large-en-v1.5",  # Large model for GPU
    "device": "cuda" if CUDA_AVAILABLE else "cpu",
    "batch_size": 64 if CUDA_AVAILABLE else 32,  # Larger batches with GPU
    "max_seq_length": 512,
    "normalize_embeddings": True,
    "gpu_memory_fraction": 0.4  # Reserve more memory for LLaMA 8B
}

# Vector database configuration
QDRANT_CONFIG = {
    "collection_name": "medical_guidelines",
    "vector_size": 1024,  # BAAI/bge-large-en-v1.5 dimension
    "distance": "Cosine",
    "use_local_qdrant": False,
    "qdrant_url": "http://localhost:6333",
    "gpu_acceleration": CUDA_AVAILABLE
}

# Document processing configuration - Enhanced for 8B model
DOCUMENT_CONFIG = {
    "chunk_strategy": "page_level",
    "max_chunk_size": 2000,  # Larger chunks for 8B model's longer context
    "chunk_overlap": 200,
    "min_chunk_size": 100,
    "use_content_hashing": True,
    "parallel_processing": True,
    "max_workers": 8  # Ryzen 7 5700X has 8 cores
}

# Retrieval configuration - Optimized for 8B model
RETRIEVAL_CONFIG = {
    "dense_top_k": 60,  # More candidates for 8B model
    "sparse_top_k": 60,
    "final_top_k": 15,  # More context for better 8B answers
    "rrf_k": 60,
    "use_reranking": True,
    "rerank_top_k": 25,  # More reranking with 8B power
    "gpu_reranking": CUDA_AVAILABLE
}

# BM25 configuration
BM25_CONFIG = {
    "k1": 1.5,
    "b": 0.75,
    "epsilon": 0.25
}

# System optimization for Ryzen 7 5700X + RTX 5060 Ti + LLaMA 3 8B
SYSTEM_CONFIG = {
    "gpu_acceleration": CUDA_AVAILABLE,
    "device": "cuda" if CUDA_AVAILABLE else "cpu",
    "gpu_memory_optimization": True,
    "max_memory_usage": "12GB" if CUDA_AVAILABLE else "16GB",
    "batch_processing": True,
    "low_memory_mode": False,  # Disable with 16GB VRAM
    "torch_threads": 16,  # Ryzen 7 5700X - 16 threads
    "mixed_precision": True,  # FP16 for faster inference
    "cuda_memory_fraction": 0.85,  # Reserve memory for 8B model
    "multiprocessing": True,
    "llama_8b_optimization": True  # Special flag for 8B model
}

# PyTorch CUDA optimization for 8B model
if CUDA_AVAILABLE:
    torch.backends.cudnn.benchmark = True
    torch.backends.cudnn.deterministic = False
    os.environ['CUDA_LAUNCH_BLOCKING'] = '0'
    # Enable TensorFloat-32 for faster computation
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": LOGS_DIR / "medical_rag_8b.log",
    "max_bytes": 20971520,  # 20MB for 8B model logs
    "backup_count": 5
}

# Enhanced medical domain configuration for 8B model
MEDICAL_CONFIG = {
    "domain_keywords": [
        "hypertension", "blood pressure", "cardiovascular", "treatment",
        "diagnosis", "medication", "patient", "clinical", "therapy",
        "symptoms", "systolic", "diastolic", "mmHg", "guidelines",
        "antihypertensive", "ACE inhibitor", "beta blocker", "diuretic",
        "calcium channel blocker", "angiotensin receptor blocker",
        "thiazide", "loop diuretic", "aldosterone antagonist"
    ],
    "medical_entities": [
        "drug", "dosage", "side effects", "contraindications",
        "interactions", "monitoring", "follow-up", "adverse reactions",
        "pharmacokinetics", "pharmacodynamics", "bioavailability"
    ],
    "enhanced_context": True  # Use more context for 8B model
}

# Performance monitoring for 8B model
PERFORMANCE_CONFIG = {
    "track_metrics": True,
    "log_response_times": True,
    "monitor_memory": True,
    "monitor_gpu_usage": CUDA_AVAILABLE,
    "benchmark_retrieval": True,
    "profile_gpu_memory": CUDA_AVAILABLE,
    "track_8b_performance": True,
    "context_window_monitoring": True
}

# Advanced GPU settings for LLaMA 3 8B
GPU_CONFIG = {
    "enable_gpu": CUDA_AVAILABLE,
    "gpu_device_id": 0,
    "mixed_precision": True,
    "gradient_checkpointing": False,
    "flash_attention": True,
    "memory_efficient_attention": True,
    "compile_model": False,
    "llama_8b_memory_management": True,
    "dynamic_batch_sizing": True
}

# LLaMA 3 8B specific optimizations
LLAMA_8B_CONFIG = {
    "model_size": "8B",
    "estimated_vram_usage": "6-8GB",
    "context_window": 8192,  # LLaMA 3 8B context window
    "recommended_max_tokens": 2048,
    "temperature_range": (0.1, 0.3),  # Conservative for medical use
    "top_p_range": (0.8, 0.95),
    "batch_size_limit": 4,  # Conservative for 8B model
    "concurrent_requests": 1,  # Single request for 8B model
    "memory_buffer": "2GB"  # Buffer for system operations
}

def get_config() -> Dict[str, Any]:
    """Get complete configuration dictionary optimized for LLaMA 3 8B"""
    return {
        "ollama": OLLAMA_CONFIG,
        "embedding": EMBEDDING_CONFIG,
        "qdrant": QDRANT_CONFIG,
        "document": DOCUMENT_CONFIG,
        "retrieval": RETRIEVAL_CONFIG,
        "bm25": BM25_CONFIG,
        "system": SYSTEM_CONFIG,
        "logging": LOGGING_CONFIG,
        "medical": MEDICAL_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "gpu": GPU_CONFIG,
        "llama_8b": LLAMA_8B_CONFIG,
        "paths": {
            "project_root": PROJECT_ROOT,
            "data_dir": DATA_DIR,
            "logs_dir": LOGS_DIR
        }
    }

def validate_config():
    """Validate configuration for LLaMA 3 8B setup"""
    config = get_config()
    
    # Check GPU memory for 8B model
    if CUDA_AVAILABLE:
        if GPU_MEMORY < 12.0:
            print(f"⚠️  Warning: LLaMA 3 8B needs 6-8GB VRAM. You have {GPU_MEMORY:.1f}GB.")
            print("   Consider using llama3:3b for better performance.")
        else:
            print(f"✅ GPU Memory ({GPU_MEMORY:.1f}GB) is sufficient for LLaMA 3 8B")
    
    # Check if data directory exists
    if not DATA_DIR.exists():
        raise ValueError(f"Data directory does not exist: {DATA_DIR}")
    
    pdf_files = list(DATA_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"⚠️  Warning: No PDF files found in {DATA_DIR}")
    
    # Validate Ollama configuration
    if not config["ollama"]["base_url"].startswith("http"):
        raise ValueError("Invalid Ollama base URL")
    
    # Check model name
    if config["ollama"]["model_name"] != "llama3:8b":
        print(f"ℹ️  Using model: {config['ollama']['model_name']}")
    
    return True

def optimize_gpu_for_8b():
    """Optimize GPU settings specifically for LLaMA 3 8B"""
    if not CUDA_AVAILABLE:
        return
    
    # Set conservative memory fraction for 8B model
    torch.cuda.set_per_process_memory_fraction(SYSTEM_CONFIG["cuda_memory_fraction"])
    
    # Enable all optimizations
    if hasattr(torch.backends, 'cuda'):
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
    
    # Clear cache
    torch.cuda.empty_cache()
    
    print(f"🔥 GPU optimized for LLaMA 3 8B model")
    print(f"💾 CUDA memory fraction: {SYSTEM_CONFIG['cuda_memory_fraction']}")
    print(f"🎮 Expected VRAM usage: 6-8GB (model) + 4-6GB (embeddings)")

def get_8b_device_info():
    """Get device information optimized for 8B model"""
    info = {
        "cpu_model": "AMD Ryzen 7 5700X",
        "cpu_cores": 8,
        "cpu_threads": 16,
        "cuda_available": CUDA_AVAILABLE,
        "gpu_name": GPU_NAME if CUDA_AVAILABLE else None,
        "gpu_memory_gb": GPU_MEMORY if CUDA_AVAILABLE else None,
        "pytorch_version": torch.__version__,
        "cuda_version": torch.version.cuda if CUDA_AVAILABLE else None,
        "llama_model": "LLaMA 3 8B",
        "model_size": "4.7GB",
        "estimated_performance": "Near GPT-4 quality"
    }
    
    if CUDA_AVAILABLE:
        props = torch.cuda.get_device_properties(0)
        info.update({
            "gpu_compute_capability": f"{props.major}.{props.minor}",
            "gpu_multiprocessors": props.multi_processor_count,
            "llama_8b_compatible": GPU_MEMORY >= 8.0,
            "recommended_setup": "Excellent for LLaMA 3 8B" if GPU_MEMORY >= 12.0 else "Sufficient for LLaMA 3 8B"
        })
    
    return info

if __name__ == "__main__":
    config = get_config()
    validate_config()
    optimize_gpu_for_8b()
    
    print("🦙 LLaMA 3 8B Medical RAG Configuration")
    print("=" * 50)
    
    device_info = get_8b_device_info()
    for key, value in device_info.items():
        print(f"{key}: {value}")
    
    print(f"\n📄 Data directory: {DATA_DIR}")
    print(f"📄 Log directory: {LOGS_DIR}")
    print(f"🦙 LLaMA model: {config['ollama']['model_name']}")
    print(f"🔢 Embedding model: {config['embedding']['model_name']}")
    print(f"⚡ Device: {config['system']['device']}")
    print(f"🎯 Context window: {config['ollama']['context_length']}")
    print(f"📝 Max tokens: {config['ollama']['max_tokens']}")
    print("✅ Configuration optimized for LLaMA 3 8B!")
    
    # Test Ollama connection
    print(f"\n🔗 Testing Ollama connection...")
    import requests
    try:
        response = requests.get(f"{config['ollama']['base_url']}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            llama_8b_found = any("llama3:8b" in model.get("name", "") for model in models)
            print(f"✅ Ollama running: {len(models)} models found")
            print(f"🦙 LLaMA 3 8B available: {'✅' if llama_8b_found else '❌'}")
        else:
            print(f"⚠️  Ollama not responding (HTTP {response.status_code})")
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        print("💡 Start Ollama with: ollama serve")