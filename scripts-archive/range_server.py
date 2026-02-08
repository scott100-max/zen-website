#!/usr/bin/env python3
"""Simple HTTP server with Range request support for audio seeking"""
import http.server
import os
import re

class RangeHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()

        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return None

        file_size = os.path.getsize(path)
        range_header = self.headers.get('Range')

        if range_header:
            # Parse range header
            match = re.match(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                self.send_response(206)  # Partial content
                self.send_header('Content-Type', self.guess_type(path))
                self.send_header('Content-Length', str(length))
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                f = open(path, 'rb')
                f.seek(start)
                return _RangeFile(f, length)

        # No range request - serve full file
        self.send_response(200)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Length', str(file_size))
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        return open(path, 'rb')

class _RangeFile:
    """Wrapper to read only a portion of a file"""
    def __init__(self, f, length):
        self.f = f
        self.remaining = length

    def read(self, size=-1):
        if self.remaining <= 0:
            return b''
        if size < 0 or size > self.remaining:
            size = self.remaining
        data = self.f.read(size)
        self.remaining -= len(data)
        return data

    def close(self):
        self.f.close()

if __name__ == '__main__':
    import socketserver
    PORT = 8080
    with socketserver.TCPServer(("", PORT), RangeHTTPRequestHandler) as httpd:
        print(f"Range-enabled server at http://localhost:{PORT}")
        httpd.serve_forever()
