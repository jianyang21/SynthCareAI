#!/usr/bin/env python3
"""
Quick Start Script for LLaMA 3 8B Medical RAG System
RTX 5060 Ti + Ryzen 7 5700X optimized
"""

import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if basic requirements are met"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check if essential files exist
    required_files = [
        "config_8b.py",
        "main_8b.py", 
        "llama_8b_integration.py",
        "setup_8b.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    
    # Check if data directory exists
    data_dir = Path("data")
    if not data_dir.exists():
        print("📁 Creating data/ directory...")
        data_dir.mkdir(exist_ok=True)
    
    pdf_files = list(data_dir.glob("*.pdf"))
    if not pdf_files:
        print("⚠️  No PDF files in data/ directory")
        print("💡 Add your medical PDF files to the data/ folder")
    else:
        print(f"✅ Found {len(pdf_files)} PDF files")
    
    return True

def run_setup():
    """Run the setup script"""
    print("\n🚀 Running setup script...")
    try:
        result = subprocess.run([sys.executable, "setup_8b.py"], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Setup failed with error code {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False

def main():
    """Main function"""
    print("🦙" + "=" * 50 + "🦙")
    print("🔥 LLaMA 3 8B MEDICAL RAG SYSTEM")
    print("🎮 Quick Start Script")
    print("🦙" + "=" * 50 + "🦙")
    print()
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed")
        print("💡 Make sure all files are present and Python 3.8+ is installed")
        return
    
    print("\n" + "="*60)
    print("🚀 SETUP OPTIONS")
    print("="*60)
    print("1. Run full setup (recommended first time)")
    print("2. Start medical AI system")
    print("3. Test system components")
    print("4. Run demonstrations")
    print("5. Exit")
    print()
    
    try:
        choice = input("Select option (1-5): ").strip()
        
        if choice == "1":
            print("\n🔧 Running full system setup...")
            if run_setup():
                print("\n✅ Setup completed successfully!")
                print("💡 Now you can run: python main_8b.py --index --interactive")
            else:
                print("\n❌ Setup failed. Check error messages above.")
        
        elif choice == "2":
            print("\n🦙 Starting LLaMA 3 8B Medical AI...")
            subprocess.run([sys.executable, "main_8b.py", "--index", "--interactive"])
        
        elif choice == "3":
            print("\n🧪 Testing system components...")
            tests = [
                ("Configuration", "config_8b.py"),
                ("LLaMA 3 8B Integration", "llama_8b_integration.py"),
                ("System Test", "main_8b.py --8b-test")
            ]
            
            for test_name, test_command in tests:
                print(f"\n🔍 Testing {test_name}...")
                try:
                    if "--" in test_command:
                        # Handle command with arguments
                        parts = test_command.split()
                        subprocess.run([sys.executable] + parts, check=True)
                    else:
                        subprocess.run([sys.executable, test_command], check=True)
                    print(f"✅ {test_name} test passed")
                except subprocess.CalledProcessError:
                    print(f"❌ {test_name} test failed")
        
        elif choice == "4":
            print("\n🎭 Running demonstrations...")
            subprocess.run([sys.executable, "demo_8b.py"])
        
        elif choice == "5":
            print("\n👋 Goodbye!")
            return
        
        else:
            print("❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()