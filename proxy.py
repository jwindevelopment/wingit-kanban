#!/usr/bin/env python3
"""
WingIt — Local Proxy Server
Handles two routes:
  POST /jira/search  — calls Jira REST API directly with Atlassian credentials
  POST /v1/messages  — forwards to Anthropic API (kept for future use)
"""

import http.server
import urllib.request
import urllib.error
import urllib.parse
import json
import sys
import base64

PORT = 3001

class ProxyHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        print(f"  [proxy] {fmt % args}", flush=True)

    def send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        length  = int(self.headers.get("Content-Length", 0))
        body    = self.rfile.read(length)
        try:
            payload = json.loads(body)
        except Exception:
            self.send_json(400, {"error": "invalid JSON"})
            return

        if self.path == "/jira/search":
            self.handle_jira(payload)
        else:
            self.send_json(404, {"error": "unknown route: " + self.path})

    def handle_jira(self, payload):
        domain    = payload.get("domain", "").strip().rstrip("/")
        email     = payload.get("email", "").strip()
        token     = payload.get("token", "").strip()
        jql       = payload.get("jql", "assignee = currentUser() AND resolution = Unresolved ORDER BY priority DESC")
        max_results = int(payload.get("maxResults", 20))

        if not domain or not email or not token:
            self.send_json(400, {"error": "domain, email, and token are required"})
            return

        # Ensure domain has https://
        if not domain.startswith("http"):
            domain = "https://" + domain

        # Basic auth: email:token base64 encoded
        creds    = base64.b64encode(f"{email}:{token}".encode()).decode()
        api_url  = f"{domain}/rest/api/3/search"
        params   = urllib.parse.urlencode({
            "jql":        jql,
            "maxResults": max_results,
            "fields":     "summary,description,priority,labels,status"
        })
        full_url = f"{api_url}?{params}"

        print(f"  [proxy] Jira search: {full_url}", flush=True)

        req = urllib.request.Request(full_url)
        req.add_header("Authorization", f"Basic {creds}")
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
                # Map Jira issues to WingIt format
                tickets = []
                for issue in data.get("issues", []):
                    f        = issue.get("fields", {})
                    priority = (f.get("priority") or {}).get("name", "Medium")
                    tickets.append({
                        "key":         issue.get("key", ""),
                        "title":       f.get("summary", ""),
                        "description": self.extract_desc(f.get("description")),
                        "priority":    self.map_priority(priority),
                        "labels":      f.get("labels", [])
                    })
                self.send_json(200, {"tickets": tickets, "total": data.get("total", 0)})

        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            print(f"  [proxy] Jira error {e.code}: {err_body}", flush=True)
            try:
                err_data = json.loads(err_body)
            except Exception:
                err_data = {"raw": err_body}
            self.send_json(e.code, {"error": f"Jira API error {e.code}", "detail": err_data})
        except Exception as e:
            print(f"  [proxy] Exception: {e}", flush=True)
            self.send_json(502, {"error": str(e)})

    def extract_desc(self, desc):
        """Extract plain text from Jira Atlassian Document Format or plain string."""
        if not desc:
            return ""
        if isinstance(desc, str):
            return desc[:200]
        # ADF format
        try:
            parts = []
            for block in desc.get("content", []):
                for inline in block.get("content", []):
                    if inline.get("type") == "text":
                        parts.append(inline.get("text", ""))
            return " ".join(parts)[:200]
        except Exception:
            return ""

    def map_priority(self, p):
        p = (p or "").lower()
        if p in ("highest", "high", "critical", "blocker"):
            return "high"
        if p in ("low", "lowest", "minor", "trivial"):
            return "low"
        return "med"

if __name__ == "__main__":
    server = http.server.HTTPServer(("127.0.0.1", PORT), ProxyHandler)
    print(f"  [proxy] WingIt proxy listening on http://127.0.0.1:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  [proxy] Stopped.", flush=True)
        sys.exit(0)
