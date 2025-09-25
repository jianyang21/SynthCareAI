"""
LLaMA 3 8B Integration for Medical RAG System
Optimized for RTX 5060 Ti with enhanced medical prompting
"""

import logging
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout
from typing import Optional, Dict, Any
import time
import json

from config_8b import get_config

logger = logging.getLogger(__name__)

class Llama8BIntegration:
    """
    LLaMA 3 8B integration via Ollama
    Optimized for medical applications with enhanced prompting
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLaMA 3 8B integration
        
        Args:
            config: Optional configuration dictionary
        """
        if config is None:
            config = get_config()
        
        self.config = config["ollama"]
        self.llama_8b_config = config["llama_8b"]
        self.medical_config = config["medical"]
        
        self.model_name = self.config["model_name"]  # "llama3:8b"
        self.base_url = self.config["base_url"]
        self.timeout = self.config["timeout"]
        
        # Enhanced generation parameters for 8B model
        self.generation_params = {
            "num_predict": self.config["max_tokens"],
            "temperature": self.config["temperature"],
            "top_p": self.config["top_p"],
            "repeat_penalty": self.config["repeat_penalty"],
            "num_ctx": self.config["context_length"],  # 4096 context
            "num_thread": 16,  # Use all Ryzen 7 5700X threads
            "num_gpu": 1,  # Use GPU acceleration
            "main_gpu": 0,  # Primary GPU
            "low_vram": False,  # We have 16GB VRAM
            "f16_kv": True,  # Use FP16 for key-value cache
            "use_mlock": True,  # Lock model in memory
            "use_mmap": True,  # Memory mapping for efficiency
        }
        
        # Check availability
        self.available = self._check_ollama_availability()
        self.model_available = False
        
        if self.available:
            self.model_available = self._check_model_availability()
            if self.model_available:
                logger.info(f"✅ LLaMA 3 8B available at {self.base_url}")
                print(f"🦙 LLaMA 3 8B available at {self.base_url}")
                print(f"🎮 GPU acceleration: {'✅ Enabled' if self._check_gpu_usage() else '⚠️  CPU Only'}")
            else:
                logger.warning(f"⚠️  Model {self.model_name} not found")
                print(f"❌ Model {self.model_name} not found")
                print("💡 Make sure you have: ollama pull llama3:8b")
        else:
            logger.warning("⚠️  Ollama service not available. Start with: ollama serve")
            print("❌ Ollama service not available. Start with: ollama serve")
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama service is running"""
        try:
            response = requests.get(
                f"{self.base_url}/api/version", 
                timeout=5
            )
            return response.status_code == 200
        except (ConnectionError, RequestException, Timeout):
            return False
    
    def _check_model_availability(self) -> bool:
        """Check if LLaMA 3 8B model is available"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                
                for model in models:
                    model_name = model.get("name", "")
                    if "llama3:8b" in model_name:
                        model_size = model.get("size", 0) / (1024**3)  # Convert to GB
                        logger.info(f"Found LLaMA 3 8B: {model_name} ({model_size:.1f} GB)")
                        print(f"🦙 Found model: {model_name} ({model_size:.1f} GB)")
                        return True
                
                logger.warning(f"LLaMA 3 8B not found in available models")
                print("❌ LLaMA 3 8B not found in available models")
                available_models = [m.get("name", "unknown") for m in models]
                print(f"Available models: {available_models}")
                return False
            else:
                logger.error(f"Failed to get model list: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False
    
    def _check_gpu_usage(self) -> bool:
        """Check if Ollama is using GPU acceleration"""
        try:
            # Test with a small prompt to check GPU usage
            payload = {
                "model": self.model_name,
                "prompt": "Test",
                "stream": False,
                "options": {"num_predict": 1}
            }
            
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            response_time = time.time() - start_time
            
            # GPU should be much faster than CPU for 8B model
            # If response is very fast (< 5s), likely using GPU
            gpu_likely = response_time < 5.0 if response.status_code == 200 else False
            
            if gpu_likely:
                print(f"⚡ Response time: {response_time:.2f}s (GPU acceleration detected)")
            else:
                print(f"⏱️  Response time: {response_time:.2f}s (may be using CPU)")
            
            return gpu_likely
            
        except Exception as e:
            logger.debug(f"GPU check failed: {e}")
            return False
    
    def generate_medical_answer(self, query: str, context: str) -> str:
        """
        Generate comprehensive medical answer using LLaMA 3 8B with enhanced prompting
        
        Args:
            query: Medical question
            context: Retrieved context from medical guidelines
            
        Returns:
            Comprehensive medical answer
        """
        if not self.available or not self.model_available:
            return "❌ LLaMA 3 8B not available. Please start Ollama and ensure the model is loaded."
        
        # Enhanced medical prompt for 8B model
        enhanced_prompt = f"""You are a highly knowledgeable medical AI assistant specializing in clinical guidelines and evidence-based medicine. You have access to authoritative medical documentation and must provide comprehensive, accurate, and professionally structured responses.

## CLINICAL CONTEXT FROM MEDICAL GUIDELINES:
{context}

## MEDICAL QUESTION:
{query}

## RESPONSE INSTRUCTIONS:
- Provide a thorough, evidence-based medical response using ONLY the information from the clinical context
- Structure your answer with clear sections using headers where appropriate
- Include specific details such as measurements, classifications, procedures, and recommendations
- Reference page numbers from the guidelines when citing specific information
- Use precise medical terminology while ensuring clarity
- If the context lacks sufficient information to fully answer the question, clearly state what information is missing
- Do not make assumptions or provide information not supported by the context
- Maintain a professional, clinical tone throughout

## COMPREHENSIVE MEDICAL RESPONSE:
"""
        
        # Use enhanced generation parameters for medical accuracy
        medical_generation_params = {
            **self.generation_params,
            "temperature": 0.05,  # Very low for medical accuracy
            "top_p": 0.85,  # Slightly lower for more focused responses
            "repeat_penalty": 1.15,  # Prevent repetition
            "num_predict": min(2048, self.config["max_tokens"]),  # Full response length
        }
        
        return self._generate_with_retries(enhanced_prompt, medical_generation_params)
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate response using LLaMA 3 8B
        
        Args:
            prompt: Input prompt for generation
            **kwargs: Additional generation parameters
            
        Returns:
            Generated response text
        """
        if not self.available or not self.model_available:
            return f"❌ LLaMA 3 8B not available. Please start Ollama and ensure the model is loaded."
        
        # Merge generation parameters
        generation_params = {**self.generation_params, **kwargs}
        
        return self._generate_with_retries(prompt, generation_params)
    
    def _generate_with_retries(self, prompt: str, generation_params: dict, max_retries: int = 2) -> str:
        """Generate with retry logic for reliability"""
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": generation_params
        }
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                
                response = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout
                )
                
                generation_time = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    generated_text = result.get("response", "No response generated")
                    
                    # Log performance metrics
                    total_tokens = result.get("eval_count", 0) + result.get("prompt_eval_count", 0)
                    if total_tokens > 0:
                        tokens_per_second = total_tokens / generation_time
                        logger.info(f"LLaMA 3 8B: {total_tokens} tokens in {generation_time:.2f}s ({tokens_per_second:.1f} tokens/s)")
                        print(f"🦙 Generated {total_tokens} tokens in {generation_time:.2f}s ({tokens_per_second:.1f} tok/s)")
                    
                    return generated_text
                    
                else:
                    error_msg = f"HTTP Error {response.status_code}: {response.text}"
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed, retrying: {error_msg}")
                        time.sleep(2)  # Brief delay before retry
                        continue
                    else:
                        logger.error(error_msg)
                        return f"❌ Generation failed after {max_retries + 1} attempts: {error_msg}"
                        
            except Timeout:
                timeout_msg = f"Request timeout after {self.timeout}s"
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt + 1} timed out, retrying")
                    time.sleep(3)
                    continue
                else:
                    logger.error(timeout_msg)
                    return f"❌ Generation timeout: {timeout_msg}"
                    
            except Exception as e:
                error_msg = f"Generation error: {str(e)}"
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying: {error_msg}")
                    time.sleep(2)
                    continue
                else:
                    logger.error(error_msg)
                    return f"❌ Generation failed: {error_msg}"
        
        return "❌ All generation attempts failed"
    
    def test_8b_performance(self) -> Dict[str, Any]:
        """Test LLaMA 3 8B performance with medical content"""
        print("🧪 Testing LLaMA 3 8B Performance...")
        
        test_results = {
            "ollama_available": self.available,
            "model_available": self.model_available,
            "base_url": self.base_url,
            "model_name": self.model_name,
            "model_size": "8B parameters (~4.7GB)"
        }
        
        if self.available and self.model_available:
            # Performance test with medical query
            medical_test_prompt = """Based on clinical guidelines, what are the main classifications of hypertension?
            
Context: Hypertension classification includes Normal (<120/80), High-normal (130-139/80-89), Grade 1 (140-159/90-99), Grade 2 (160-179/100-109), and Grade 3 (≥180/110 mmHg).
            
Provide a detailed clinical response:"""
            
            try:
                start_time = time.time()
                response = self.generate(medical_test_prompt, num_predict=512)
                generation_time = time.time() - start_time
                
                test_results.update({
                    "test_generation_success": True,
                    "test_generation_time": generation_time,
                    "test_response_length": len(response),
                    "estimated_tokens_per_second": len(response.split()) * 1.3 / generation_time,  # Rough estimate
                    "test_response_preview": response[:200] + "..." if len(response) > 200 else response,
                    "gpu_acceleration_detected": generation_time < 15.0,  # 8B model should be <15s on GPU
                })
                
                print(f"✅ Test successful!")
                print(f"⚡ Generation time: {generation_time:.2f}s")
                print(f"📝 Response length: {len(response)} characters")
                print(f"🚀 Estimated speed: {test_results['estimated_tokens_per_second']:.1f} tokens/second")
                
            except Exception as e:
                test_results.update({
                    "test_generation_success": False,
                    "test_error": str(e)
                })
                print(f"❌ Test failed: {e}")
        
        return test_results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed information about LLaMA 3 8B model"""
        if not self.available:
            return {"error": "Ollama not available"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": self.model_name},
                timeout=10
            )
            
            if response.status_code == 200:
                model_info = response.json()
                
                # Extract key information
                info = {
                    "model_name": self.model_name,
                    "model_size_gb": model_info.get("size", 0) / (1024**3),
                    "parameters": "8 billion",
                    "architecture": "Transformer (LLaMA 3)",
                    "context_window": self.config["context_length"],
                    "quantization": model_info.get("details", {}).get("quantization_level", "Unknown"),
                    "gpu_optimized": True,
                    "medical_optimized": True
                }
                
                return info
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}

def test_llama_8b_integration():
    """Test script for LLaMA 3 8B integration"""
    print("🦙 Testing LLaMA 3 8B Integration...")
    
    llama = Llama8BIntegration()
    
    # Test connection and performance
    test_results = llama.test_8b_performance()
    print(f"\\n📊 Test Results:")
    for key, value in test_results.items():
        print(f"  {key}: {value}")
    
    # Test medical answer generation
    if test_results.get("test_generation_success"):
        print(f"\\n🏥 Testing medical answer generation...")
        
        medical_context = """
        Hypertension Management Guidelines:
        
        Classification:
        - Normal: < 120/80 mmHg
        - High-normal: 130-139/80-89 mmHg  
        - Grade 1: 140-159/90-99 mmHg
        - Grade 2: 160-179/100-109 mmHg
        - Grade 3: ≥ 180/110 mmHg
        
        Treatment Goals:
        - General population: < 140/90 mmHg
        - Diabetes/CKD: < 130/80 mmHg
        - Elderly (≥65): < 150/90 mmHg
        
        First-line medications:
        - ACE inhibitors
        - Angiotensin receptor blockers (ARBs)  
        - Calcium channel blockers
        - Thiazide diuretics
        """
        
        query = "What are the treatment goals and first-line medications for hypertension management?"
        
        print(f"\\n🔍 Medical Query: {query}")
        print("=" * 60)
        
        start_time = time.time()
        answer = llama.generate_medical_answer(query, medical_context)
        answer_time = time.time() - start_time
        
        print(f"🤖 LLaMA 3 8B Medical Response ({answer_time:.2f}s):")
        print(answer)
        print("=" * 60)
    
    # Get model information
    model_info = llama.get_model_info()
    print(f"\\n🦙 Model Information:")
    for key, value in model_info.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_llama_8b_integration()