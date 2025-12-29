#!/usr/bin/env python3
"""
Startup script for the Industrial Training Chatbot server.
Can be used for both local development and cloud deployment.
"""

import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # Get port from environment variable (for cloud platforms) or default to 8000
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    # Change to pdf_chatbot directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Start the server
    uvicorn.run(
        "server.main:app",
        host=host,
        port=port,
        reload=False,  # Set to True for local development
        log_level="info"
    )

