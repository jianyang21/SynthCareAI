"""
Main Entry Point for LLaMA 3 8B Medical RAG System
Optimized for RTX 5060 Ti with enhanced medical capabilities
"""

import argparse
import sys
import torch
import time
from pathlib import Path

from config_8b import get_config, validate_config, get_8b_device_info, optimize_gpu_for_8b
from medical_rag_gpu import GPUMedicalRAGSystem
from llama_8b_integration import Llama8BIntegration


def print_header():
    print()
    print("🦙" + "=" * 68 + "🦙")
    print("🔥 LLaMA 3 8B MEDICAL RAG SYSTEM")
    print("🎮 RTX 5060 Ti 16GB + Ryzen 7 5700X Optimized")
    print("🏥 Near GPT-4 Quality Medical AI Assistant")
    print("🦙" + "=" * 68 + "🦙")
    print()


def display_status():
    # Show GPU hardware info
    if torch.cuda.is_available():
        dev_name = torch.cuda.get_device_name(0)
        dev_mem = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
        print(f"🎮 Device: {dev_name} ({dev_mem:.1f} GB)")
        print(f"CUDA Version: {torch.version.cuda}")
        print("Status: ✅ Ready for acceleration")
    else:
        print("⚠️ CUDA not available; running on CPU")
    print()

    # Show LLaMA Model availability
    llama = Llama8BIntegration()
    if llama.available and llama.model_available:
        print(f"LLaMA Model: {llama.model_name} available")
    else:
        print("LLaMA Model NOT available, start the Ollama server and download model")


def main():
    parser = argparse.ArgumentParser(
        description="LLaMA 3 8B Medical RAG System",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Usage Examples:
--index                  Index documents for retrieval
--query "text"           Ask a question
--interactive            Launch interactive mode
--benchmark              Run performance benchmark
--test                  Run system tests
--status                Show system status
"""
    )
    parser.add_argument("--index", action="store_true")
    parser.add_argument("--query", type=str)
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--benchmark", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--cpu-only", action="store_true")

    args = parser.parse_args()

    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    try:
        print_header()
        display_status()

        # Load config
        config = get_config()
        if args.cpu_only:
            config["gpu"]["enable_gpu"] = False
            config["system"]["device"] = "cpu"

        validate_config()
        optimize_gpu_for_8b()

        rag_system = GPUMedicalRAGSystem(config)

        if args.index:
            print("Indexing documents...")
            if not rag_system.index_documents():
                print("Indexing failed")
                sys.exit(1)

        if args.query:
            if not rag_system.indexed:
                print("You must index documents before querying")
                sys.exit(1)
            response = rag_system.query(args.query)
            print(response.get("answer", "No answer found"))

        if args.interactive:
            if not rag_system.indexed:
                print("Indexing documents before starting interactive mode...")
                if not rag_system.index_documents():
                    print("Indexing failed")
                    sys.exit(1)
            rag_system.run_interactive()

        if args.benchmark:
            rag_system.run_benchmark()

        if args.test:
            rag_system.run_tests()

        if args.status:
            rag_system.print_status()

        if not any([args.index, args.query, args.interactive, args.benchmark, args.test, args.status]):
            parser.print_help()

    except KeyboardInterrupt:
        print("\nInterrupted by user, exiting...")
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
