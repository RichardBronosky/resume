#!/usr/bin/env python3
"""Serve build/ with temporary layout diagnostics, privately via Tailscale Serve.

Use tools.sh review start. Diagnostics are off unless explicitly enabled.
No generated files are edited.
"""

import argparse
import json
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT / 'build'), **kwargs)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def diagnostics_enabled(self):
        try:
            return bool(json.loads(self.server.config_path.read_text()).get('diagnostics'))
        except (OSError, ValueError, AttributeError):
            return False

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/__review/health':
            content = json.dumps({'owner': self.server.owner_token,
                                  'diagnostics': self.diagnostics_enabled()}).encode()
            mime = 'application/json'
        elif path == '/__review/diagnostics.js' and self.diagnostics_enabled():
            content = (ROOT / 'tools/review-diagnostics.js').read_bytes()
            mime = 'application/javascript'
        elif path == '/bruno.bronosky.resume.html':
            content = (ROOT / 'build/bruno.bronosky.resume.html').read_bytes()
            if self.diagnostics_enabled():
                content = content.replace(b'</body>', b'<script src="/__review/diagnostics.js" defer></script></body>')
            mime = 'text/html; charset=utf-8'
        else:
            return super().do_GET()
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        if self.path != '/__review/report' or not self.diagnostics_enabled():
            return self.send_error(404)
        # Browser-origin reports must come from this review server.
        origin = self.headers.get('Origin')
        if origin and urlsplit(origin).netloc != self.headers.get('Host'):
            return self.send_error(403)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 262144:
                return self.send_error(413)
            report = json.loads(self.rfile.read(length))
            if not isinstance(report, dict):
                raise ValueError('Expected object')
        except (ValueError, UnicodeDecodeError):
            return self.send_error(400)
        report['received'] = datetime.now(timezone.utc).isoformat()
        with self.server.report_path.open('a') as stream:
            stream.write(json.dumps(report) + '\n')
        print(json.dumps({key: report.get(key) for key in
                          ('session', 'reason', 'innerWidth', 'visualViewport', 'root')}), flush=True)
        self.send_response(204)
        self.send_header('Content-Length', '0')
        self.end_headers()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--reports', type=Path, default=Path('/tmp/resume-review-reports.jsonl'))
    parser.add_argument('--config', type=Path)
    parser.add_argument('--owner-token', default='standalone')
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.report_path = args.reports
    server.config_path = args.config
    server.owner_token = args.owner_token
    print(f'Review server: http://127.0.0.1:{args.port}/bruno.bronosky.resume.html', flush=True)
    print(f'Diagnostics: {args.reports}', flush=True)
    server.serve_forever()
