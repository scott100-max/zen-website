#!/usr/bin/env python3
"""Tiny server for chunk test page — receives verdicts via POST, saves to JSON."""
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

RESULTS_FILE = Path(__file__).parent / "chunk-results.json"

class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path in ("/save", "/verdict"):
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            RESULTS_FILE.write_text(json.dumps(body, indent=2))
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(b"ok")
            # Print live to terminal
            n = body.get("chunk")
            v = body.get("verdict")
            note = body.get("note", "")
            print(f"  Chunk {n:2d}: {v}{' — ' + note if note else ''}")
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress GET logs

if __name__ == "__main__":
    print("Chunk test server on http://localhost:8111")
    print("Waiting for verdicts...\n")
    HTTPServer(("", 8111), Handler).serve_forever()
