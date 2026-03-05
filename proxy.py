#!/usr/bin/env python3
"""
WingIt — Anthropic API Proxy
Forwards requests from localhost to api.anthropic.com, bypassing browser CORS.
Runs on port 3001. Start automatically via launch.sh.
"""

import http.server
import urllib.request
import urllib.error
import json
import sys

PORT = 3001
ANTHROPIC_API = "https://api.anthropic.com"

class ProxyHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"  [proxy] {self.address_string()} — {fmt % args}", flush=True)

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers",
            "Content-Type, x-api-key, anthropic-version, anthropic-beta, "
            "anthropic-dangerous-direct-browser-access")

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        """Forward POST to Anthropic and stream response back."""
        # Read request body
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)

        # Parse body to extract and remove the api key
        try:
            payload = json.loads(body)
        except Exception:
            self.send_response(400)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"invalid JSON body"}')
            return

        api_key = payload.pop("__api_key", None)
        if not api_key:
            # Fall back to header
            api_key = self.headers.get("x-api-key", "")

        forwarded_body = json.dumps(payload).encode()

        # Build upstream request
        target_url = ANTHROPIC_API + self.path
        req = urllib.request.Request(
            target_url,
            data=forwarded_body,
            method="POST"
        )
        req.add_header("Content-Type", "application/json")
        req.add_header("x-api-key", api_key)
        req.add_header("anthropic-version",
            payload.get("anthropic_version", "2023-06-01"))
        req.add_header("anthropic-beta",
            self.headers.get("anthropic-beta", "mcp-client-2025-04-04"))

        try:
            with urllib.request.urlopen(req) as resp:
                resp_body = resp.read()
                self.send_response(resp.status)
                self.send_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            resp_body = e.read()
            self.send_response(e.code)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(resp_body)
        except Exception as e:
            self.send_response(502)
            self.send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

if __name__ == "__main__":
    server = http.server.HTTPServer(("127.0.0.1", PORT), ProxyHandler)
    print(f"  [proxy] Anthropic proxy listening on http://127.0.0.1:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  [proxy] Stopped.", flush=True)
        sys.exit(0)
