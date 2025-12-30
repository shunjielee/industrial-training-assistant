#!/usr/bin/env python3
"""
Startup script for the Industrial Training Chatbot server.
Can be used for both local development and cloud deployment.
"""

import uvicorn
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    # Get port from environment variable (for cloud platforms) or default to 8000
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Change to pdf_chatbot directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Add current directory to Python path
    sys.path.insert(0, str(script_dir))
    
    print(f"Starting server on {host}:{port}", flush=True)
    print(f"Working directory: {os.getcwd()}", flush=True)
    print(f"PORT environment variable: {os.getenv('PORT', 'NOT SET')}", flush=True)
    
    # Test import before starting server
    try:
        print("Testing server import...", flush=True)
        from server.main import app
        print("Server import successful!", flush=True)
    except Exception as e:
        print(f"ERROR: Failed to import server.main: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    try:
        print(f"Starting uvicorn on 0.0.0.0:{port}...", flush=True)
        # Start the server - explicitly bind to 0.0.0.0 and PORT
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        print(f"Error starting server: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)

