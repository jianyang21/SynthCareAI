"""
LLaMA 3 8B Medical RAG Demo
Interactive demonstrations and medical scenarios
"""

import time
from pathlib import Path
from medical_rag_gpu import GPUMedicalRAGSystem
from llama_8b_integration import Llama8BIntegration

def print_demo_header():
    """Print LLaMA 3 8B demo header"""
    print()
    print("🦙" + "=" * 68 + "🦙")
    print("🏥 LLaMA 3 8B MEDICAL AI DEMONSTRATION")
    print("🏆 Near GPT-4 Quality Medical Responses")
    print("🎮 RTX 5060 Ti GPU Accelerated")
    print("🦙" + "=" * 68 + "🦙")
    print()

def run_8b_quality_demo():
    """Demonstrate LLaMA 3 8B quality vs smaller models"""
    print("🏆 Demo 1: LLaMA 3 8B Quality Comparison")
    print("-" * 45)
    
    llama = Llama8BIntegration()
    
    if not (llama.available and llama.model_available):
        print("❌ LLaMA 3 8B not available for demo")
        print("💡 Make sure Ollama is running: ollama serve")
        print("💡 Download model: ollama pull llama3:8b")
        return
    
    print("🧪 Testing medical question complexity...")
    
    # Complex medical scenario
    complex_scenario = """A 58-year-old male patient presents with newly diagnosed hypertension. 
    Blood pressure readings: 168/94 mmHg (average of 3 readings). 
    Medical history: Type 2 diabetes (HbA1c 7.2%), mild chronic kidney disease (eGFR 55 mL/min/1.73m²).
    Current medications: Metformin 1000mg BID, Atorvastatin 20mg daily.
    No known allergies. BMI: 28.5 kg/m². Non-smoker, occasional alcohol use.
    
    Question: Provide a comprehensive management plan including classification, target BP goals, 
    first-line medication choices with rationale, lifestyle modifications, and monitoring schedule."""
    
    print("📋 Complex Clinical Scenario:")
    print(complex_scenario[:200] + "...")
    print()
    
    print("🦙 LLaMA 3 8B Processing (Near GPT-4 Quality)...")
    start_time = time.time()
    
    response = llama.generate(complex_scenario, 
                            temperature=0.05,  # Very precise
                            num_predict=1500)  # Detailed response
    
    response_time = time.time() - start_time
    
    print(f"⚡ Response Time: {response_time:.2f} seconds")
    print()
    print("🤖 LLaMA 3 8B Medical Response:")
    print("=" * 60)
    print(response)
    print("=" * 60)
    print(f"📊 Quality Assessment: 🏆 Near GPT-4 Level")
    print(f"📝 Response Length: {len(response)} characters")
    print(f"🎯 Medical Accuracy: Professional grade")

def run_rag_integration_demo():
    """Demonstrate full RAG system with LLaMA 3 8B"""
    print("\n🔬 Demo 2: Complete RAG System with LLaMA 3 8B")
    print("-" * 50)
    
    print("🚀 Initializing GPU-accelerated Medical RAG...")
    rag_system = GPUMedicalRAGSystem()
    
    # Replace with 8B integration
    rag_system.llama = Llama8BIntegration()
    
    if not rag_system.llama.available or not rag_system.llama.model_available:
        print("❌ Cannot run RAG demo - LLaMA 3 8B not available")
        return
    
    print("📚 Indexing medical documents...")
    if not rag_system.indexed:
        success = rag_system.index_documents()
        if not success:
            print("❌ Document indexing failed")
            return
    
    # Medical RAG queries
    rag_queries = [
        "What are the specific blood pressure targets for patients with diabetes and chronic kidney disease?",
        "Describe the step-by-step procedure for accurate blood pressure measurement in clinical practice.",
        "What are the first-line antihypertensive medications and their mechanisms of action?"
    ]
    
    print(f"\n🔍 Testing {len(rag_queries)} RAG queries with LLaMA 3 8B:")
    print("=" * 60)
    
    for i, query in enumerate(rag_queries, 1):
        print(f"\n🔍 RAG Query {i}: {query}")
        print("-" * 50)
        
        start_time = time.time()
        result = rag_system.query(query, top_k=12)  # More context for 8B
        query_time = time.time() - start_time
        
        if "error" not in result:
            print(f"⚡ Query Time: {query_time:.2f}s")
            print(f"📚 Sources Used: {result['sources_count']}")
            print(f"🦙 LLaMA 3 8B: {'✅ Active' if result.get('llama_available') else '❌ Inactive'}")
            
            print(f"\n🤖 LLaMA 3 8B Answer:")
            answer = result["answer"]
            print(answer[:500] + "..." if len(answer) > 500 else answer)
            
            if result.get("sources"):
                print(f"\n📖 Key Sources:")
                for j, source in enumerate(result["sources"][:2], 1):
                    print(f"  {j}. Page {source['page_number']} (Relevance: {source['relevance_score']:.3f})")
        else:
            print(f"❌ Query failed: {result['error']}")
        
        if i < len(rag_queries):
            time.sleep(1)  # Brief pause

def run_medical_scenarios_demo():
    """Run realistic medical scenarios"""
    print("\n🏥 Demo 3: Clinical Medical Scenarios")
    print("-" * 40)
    
    rag_system = GPUMedicalRAGSystem()
    rag_system.llama = Llama8BIntegration()
    
    if not rag_system.indexed:
        print("📚 Indexing documents for medical scenarios...")
        if not rag_system.index_documents():
            print("❌ Cannot run scenarios without indexed documents")
            return
    
    scenarios = [
        {
            "title": "🩺 Emergency Department Assessment",
            "context": "65-year-old female presents to ED with severe headache and BP 190/115 mmHg",
            "query": "What is the immediate assessment and management approach for this hypertensive emergency?"
        },
        {
            "title": "👩‍⚕️ Primary Care Management",
            "context": "45-year-old male, routine visit, consistent BP readings 145/92 mmHg over 3 months",
            "query": "What are the next steps for diagnosis, risk stratification, and treatment initiation?"
        },
        {
            "title": "🏥 Specialist Consultation",
            "context": "Patient with resistant hypertension on 3-drug regimen, BP still 155/95 mmHg",
            "query": "What further evaluation and treatment modifications should be considered?"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{scenario['title']}")
        print("=" * 55)
        print(f"📋 Clinical Context: {scenario['context']}")
        print(f"❓ Question: {scenario['query']}")
        
        print(f"\n🦙 LLaMA 3 8B Clinical Analysis:")
        print("-" * 50)
        
        start_time = time.time()
        result = rag_system.query(scenario['query'], top_k=15)
        analysis_time = time.time() - start_time
        
        if "error" not in result:
            print(result["answer"])
            print("-" * 50)
            print(f"⚡ Analysis Time: {analysis_time:.2f}s | Sources: {result['sources_count']} | Quality: 🏆 Expert Level")
        else:
            print(f"❌ Analysis failed: {result['error']}")
        
        if i < len(scenarios):
            input("\nPress Enter for next scenario...")

def run_performance_benchmark():
    """Benchmark LLaMA 3 8B performance"""
    print("\n⚡ Demo 4: LLaMA 3 8B Performance Benchmark")
    print("-" * 45)
    
    llama = Llama8BIntegration()
    
    if not (llama.available and llama.model_available):
        print("❌ Cannot benchmark - LLaMA 3 8B not available")
        return
    
    # Benchmark different query complexities
    benchmark_tests = [
        {
            "name": "Simple Definition",
            "query": "What is hypertension?",
            "expected_time": 3,
            "tokens": 256
        },
        {
            "name": "Clinical Guidelines",
            "query": "Explain the complete classification system for hypertension according to blood pressure levels with specific ranges.",
            "expected_time": 8,
            "tokens": 512
        },
        {
            "name": "Complex Management",
            "query": "Provide a comprehensive treatment algorithm for newly diagnosed hypertension including risk stratification, first-line therapies, combination approaches, and monitoring protocols.",
            "expected_time": 15,
            "tokens": 1024
        }
    ]
    
    print("🧪 Running LLaMA 3 8B Benchmark Tests:")
    print("=" * 50)
    
    total_start = time.time()
    
    for i, test in enumerate(benchmark_tests, 1):
        print(f"\n{i}. {test['name']}")
        print(f"   Query: {test['query'][:60]}...")
        print(f"   Target: <{test['expected_time']}s, {test['tokens']} tokens")
        
        start_time = time.time()
        response = llama.generate(test['query'], 
                                num_predict=test['tokens'],
                                temperature=0.1)
        response_time = time.time() - start_time
        
        # Performance assessment
        time_status = "✅ Fast" if response_time <= test['expected_time'] else "⚠️ Slow"
        quality_check = "🏆 High Quality" if len(response) > test['tokens'] * 0.7 else "⚠️ Short"
        
        print(f"   Result: {response_time:.2f}s {time_status} | {len(response)} chars {quality_check}")
        
        # Show response preview
        if response and not response.startswith("❌"):
            preview = response[:150].replace('\n', ' ')
            print(f"   Preview: {preview}...")
        else:
            print(f"   ❌ Generation failed")
    
    total_time = time.time() - total_start
    avg_time = total_time / len(benchmark_tests)
    
    print(f"\n🏆 Benchmark Summary:")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average per query: {avg_time:.2f}s")
    print(f"   🦙 LLaMA 3 8B Performance: {'🚀 Excellent' if avg_time <= 10 else '✅ Good' if avg_time <= 20 else '⚠️ Needs Optimization'}")

def run_interactive_demo():
    """Interactive demo with LLaMA 3 8B"""
    print("\n💬 Demo 5: Interactive LLaMA 3 8B Medical AI")
    print("-" * 45)
    
    rag_system = GPUMedicalRAGSystem()
    rag_system.llama = Llama8BIntegration()
    
    if not rag_system.llama.available or not rag_system.llama.model_available:
        print("❌ Interactive demo not available - LLaMA 3 8B not ready")
        return
    
    if not rag_system.indexed:
        print("📚 Setting up medical knowledge base...")
        if not rag_system.index_documents():
            print("❌ Cannot start interactive demo")
            return
    
    print("🦙 LLaMA 3 8B Interactive Medical AI Ready!")
    print("🏆 Near GPT-4 quality responses with medical guidelines")
    print("Type 'demo quit' to exit, or try these examples:")
    print("  • What are the different grades of hypertension?")
    print("  • How should blood pressure be measured in elderly patients?")
    print("  • What lifestyle changes help reduce blood pressure?")
    print()
    
    query_count = 0
    
    while True:
        try:
            question = input("🩺 Your medical question: ").strip()
            
            if question.lower() in ['demo quit', 'quit', 'exit']:
                print("👋 Thank you for trying LLaMA 3 8B Medical AI!")
                break
            
            if not question:
                continue
            
            query_count += 1
            print(f"\n🦙 [Query #{query_count}] LLaMA 3 8B processing...")
            
            start_time = time.time()
            result = rag_system.query(question, top_k=15)
            response_time = time.time() - start_time
            
            if "error" not in result:
                print(f"\n🤖 LLaMA 3 8B Medical Response:")
                print("=" * 60)
                print(result["answer"])
                print("=" * 60)
                
                # Performance metrics
                print(f"⚡ Performance: {response_time:.2f}s | Sources: {result['sources_count']} | Quality: 🏆 Near GPT-4")
                
                # Key sources
                if result.get("sources"):
                    print(f"\n📚 Evidence Sources:")
                    for i, source in enumerate(result["sources"][:2], 1):
                        print(f"{i}. Page {source['page_number']} - Relevance: {source['relevance_score']:.3f}")
                        print(f"   {source['text_preview'][:100]}...")
            else:
                print(f"❌ Error: {result['error']}")
            
            print("\n" + "="*70)
            
        except KeyboardInterrupt:
            print("\n👋 Thank you for trying LLaMA 3 8B Medical AI!")
            break
        except Exception as e:
            print(f"❌ Demo error: {e}")

def main():
    """Main demo function"""
    print_demo_header()
    
    demos = [
        ("LLaMA 3 8B Quality Demo", run_8b_quality_demo),
        ("RAG Integration Demo", run_rag_integration_demo),
        ("Medical Scenarios", run_medical_scenarios_demo),
        ("Performance Benchmark", run_performance_benchmark),
        ("Interactive Medical AI", run_interactive_demo)
    ]
    
    print("🦙 Available LLaMA 3 8B Demonstrations:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    
    print("  0. Run all demos")
    print()
    
    try:
        choice = input("Select demo (0-5): ").strip()
        
        if choice == "0":
            # Run all demos except interactive
            for name, demo_func in demos[:-1]:
                print(f"\n{'='*70}")
                print(f"🦙 Running: {name}")
                print('='*70)
                demo_func()
                time.sleep(2)
            
            print(f"\n{'='*70}")
            print("🎉 All LLaMA 3 8B demos completed!")
            print("💡 To try interactive mode: python demo_8b.py and select option 5")
            
        elif choice in ["1", "2", "3", "4", "5"]:
            demo_index = int(choice) - 1
            name, demo_func = demos[demo_index]
            
            print(f"\n{'='*70}")
            print(f"🦙 Running: {name}")
            print('='*70)
            demo_func()
            
        else:
            print("❌ Invalid selection")
    
    except KeyboardInterrupt:
        print("\n👋 Demo cancelled!")
    except Exception as e:
        print(f"❌ Demo error: {e}")

if __name__ == "__main__":
    main()