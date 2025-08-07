#!/usr/bin/env python3
"""
Simple HTTP server to serve the games viewer locally.
This avoids CORS issues when loading the JSON file.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

def main():
    # Change to the docs directory (so relative fetch('./games.json') works)
    script_dir = Path(__file__).parent
    docs_dir = script_dir / "docs"
    if not docs_dir.exists():
        print("docs/ directory not found. Please create it and place index.html there.")
        return 1
    os.chdir(docs_dir)
    
    # Choose port
    PORT = 8000
    
    # Try to find an available port
    for port in range(8000, 8010):
        try:
            with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
                PORT = port
                break
        except OSError:
            continue
    else:
        print("Could not find an available port")
        return 1
    
    # Start server
    Handler = http.server.SimpleHTTPRequestHandler
    
    print(f"Starting server at http://localhost:{PORT}")
    print(f"Serving files from: {docs_dir}")
    print("\nYour games viewer will open in your browser...")
    print("Press Ctrl+C to stop the server")
    
    # Open browser (serve index.html in docs/)
    webbrowser.open(f"http://localhost:{PORT}/")
    
    # Start serving
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
