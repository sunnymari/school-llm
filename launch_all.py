#!/usr/bin/env python3
"""
Launch all LLM Assessment interfaces
This script starts all the different interfaces in separate processes.
"""

import subprocess
import time
import os
import sys
import threading
import webbrowser
from pathlib import Path

def run_command(command, name, port=None):
    """Run a command in a subprocess."""
    print(f"🚀 Starting {name}...")
    try:
        if port:
            print(f"   → Will be available at http://localhost:{port}")
        
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        if process.poll() is None:
            print(f"✅ {name} started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ {name} failed to start")
            print(f"   Error: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start {name}: {str(e)}")
        return None

def open_browser(url, delay=5):
    """Open browser after a delay."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
        print(f"🌐 Opened {url} in browser")
    except Exception as e:
        print(f"❌ Failed to open browser: {str(e)}")

def main():
    print("🎓 LLM Assessment Platform Launcher")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("app/main.py").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Check if data is loaded
    if not Path("data/responses.csv").exists():
        print("⚠️  Warning: Data files not found. Please run 'python scripts/load_sample_data.py' first")
    
    if not Path("vector_index.pkl").exists():
        print("⚠️  Warning: Vector index not found. Please run 'python scripts/build_index.py' first")
    
    processes = []
    
    try:
        # Start FastAPI server
        api_process = run_command(
            "uvicorn app.main:app --reload --port 8000",
            "FastAPI Server",
            port=8000
        )
        if api_process:
            processes.append(("FastAPI", api_process))
        
        # Start Streamlit main app
        streamlit_process = run_command(
            "streamlit run streamlit_app/app.py --server.port 8501",
            "Streamlit Dashboard",
            port=8501
        )
        if streamlit_process:
            processes.append(("Streamlit", streamlit_process))
        
        # Start Google Sheets integration
        sheets_process = run_command(
            "streamlit run web_ui/google_sheets_integration.py --server.port 8502",
            "Google Sheets Integration",
            port=8502
        )
        if sheets_process:
            processes.append(("Google Sheets", sheets_process))
        
        # Start LTI integration
        lti_process = run_command(
            "streamlit run lti_integration/lti_app.py --server.port 8503",
            "LTI Canvas Integration",
            port=8503
        )
        if lti_process:
            processes.append(("LTI", lti_process))
        
        if not processes:
            print("❌ No services started successfully")
            sys.exit(1)
        
        print("\n" + "=" * 50)
        print("🎉 All services started successfully!")
        print("\n📋 Available interfaces:")
        print("   🌐 Main Dashboard: http://localhost:8501")
        print("   📊 Google Sheets:  http://localhost:8502")
        print("   🎓 LTI Canvas:     http://localhost:8503")
        print("   🔧 API Docs:       http://localhost:8000/docs")
        print("   📁 Static Files:   http://localhost:8000/static")
        print("\n💡 Press Ctrl+C to stop all services")
        print("=" * 50)
        
        # Open main dashboard in browser
        threading.Thread(target=open_browser, args=("http://localhost:8501", 3)).start()
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
                
                # Check if any process died
                for name, process in processes:
                    if process.poll() is not None:
                        print(f"⚠️  {name} process stopped unexpectedly")
                        
        except KeyboardInterrupt:
            print("\n🛑 Shutting down all services...")
            
    finally:
        # Clean up processes
        for name, process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔨 {name} force stopped")
            except Exception as e:
                print(f"❌ Error stopping {name}: {str(e)}")
        
        print("👋 All services stopped")

if __name__ == "__main__":
    main()
