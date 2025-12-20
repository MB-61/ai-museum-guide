"""
TalkingHead Avatar Server
Basit HTTP sunucusu - avatari localhost:8080'de calistirir
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """CORS basliklari eklenmis HTTP handler"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # CORS basliklari ekle
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    os.chdir(DIRECTORY)
    
    print("=" * 50)
    print("TalkingHead Avatar Server")
    print("=" * 50)
    print("Klasor: " + DIRECTORY)
    print("Adres: http://localhost:" + str(PORT))
    print("Sayfa: http://localhost:" + str(PORT) + "/test%20avatar.html")
    print("=" * 50)
    print("Durdurmak icin Ctrl+C")
    print("=" * 50)
    
    # Tarayiciyi otomatik ac
    webbrowser.open("http://localhost:" + str(PORT) + "/test%20avatar.html")
    
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nSunucu durduruldu.")
            sys.exit(0)

if __name__ == "__main__":
    main()
