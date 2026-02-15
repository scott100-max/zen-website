#!/usr/bin/env python3
"""Serves the review page AND receives live pick data. Single server, no CORS issues."""
import json, os, sys, mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from urllib.parse import unquote

SAVE_DIR = None
VAULT_ROOT = None

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = unquote(self.path.lstrip('/'))
        if path == '' or path == 'review':
            path = 'unified-review.html'

        # API: get more candidates for a chunk
        # /more?chunk=5&skip=3&count=3
        if path.startswith('more'):
            self._serve_more()
            return

        filepath = os.path.join(VAULT_ROOT, path)
        if not os.path.isfile(filepath):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')
            return

        mime, _ = mimetypes.guess_type(filepath)
        if mime is None:
            mime = 'application/octet-stream'

        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.end_headers()
        with open(filepath, 'rb') as f:
            self.wfile.write(f.read())

    def _serve_more(self):
        """Return next N candidates for a chunk from the auto-pick log."""
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        chunk = int(qs.get('chunk', [0])[0])
        skip = int(qs.get('skip', [3])[0])
        count = int(qs.get('count', [3])[0])

        log_path = os.path.join(SAVE_DIR, 'auto-pick-log.json')
        if not os.path.exists(log_path):
            self.send_response(404)
            self.end_headers()
            return

        with open(log_path) as f:
            logs = json.load(f)

        entry = None
        for e in logs:
            if e['chunk'] == chunk:
                entry = e
                break

        if not entry:
            self.send_response(404)
            self.end_headers()
            return

        remaining = entry.get('remaining', [])
        batch = remaining[skip:skip + count]

        options = []
        for cand in batch:
            ver = cand['version']
            q = round(cand.get('quality_score', 0) or 0, 3)
            dur = round(cand.get('duration', 0) or 0, 1)
            src = f"c{chunk:02d}/c{chunk:02d}_v{ver:02d}.wav"
            options.append({'ver': ver, 'q': q, 'dur': dur, 'src': src})

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'chunk': chunk,
            'skip': skip,
            'total_remaining': len(remaining),
            'options': options
        }).encode())

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except:
            self.send_response(400)
            self.end_headers()
            return

        # Save to disk
        path = os.path.join(SAVE_DIR, 'live-picks.json')
        data['saved_at'] = datetime.utcnow().isoformat() + 'Z'
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"  Saved: {len(data.get('picks', []))} picks, {data.get('reviewed', 0)} reviewed → {path}")

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, format, *args):
        pass  # quiet

if __name__ == '__main__':
    session = sys.argv[1] if len(sys.argv) > 1 else '91-the-body-scan'
    SAVE_DIR = os.path.join('content/audio-free/vault', session)
    VAULT_ROOT = os.path.join('content/audio-free/vault', session)
    os.makedirs(SAVE_DIR, exist_ok=True)
    port = 9191
    print(f"Review server for {session}")
    print(f"  Serving: http://localhost:{port}/review")
    print(f"  Saving to: {SAVE_DIR}/live-picks.json")
    print()
    HTTPServer(('localhost', port), Handler).serve_forever()
