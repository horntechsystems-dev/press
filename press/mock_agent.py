import http.server
import json
import os
import subprocess
import base64
import hashlib
import socketserver
import urllib.parse
import hmac
from pathlib import Path

AGENT_DIR = "/home/frappe/agent"
CONFIG_PATH = os.path.join(AGENT_DIR, "config.json")
BENCHES_DIR = "/home/frappe/benches"

with open(CONFIG_PATH) as f:
    config = json.load(f)
ACCESS_TOKEN = config.get("access_token", "")


def verify_auth(headers):
    auth = headers.get("Authorization", "")
    if not auth:
        return False
    try:
        method, token = auth.split(" ", 1)
        if method.lower() == "bearer":
            from passlib.hash import pbkdf2_sha256
            return pbkdf2_sha256.verify(token, ACCESS_TOKEN)
        elif method.lower() == "basic":
            decoded = base64.b64decode(token).decode()
            password = decoded.split(":")[1]
            from passlib.hash import pbkdf2_sha256
            return pbkdf2_sha256.verify(password, ACCESS_TOKEN)
    except Exception:
        pass
    return False


def run_bench_command(args):
    env = os.environ.copy()
    env["PATH"] = f"/home/frappe/frappe-bench/env/bin:{env.get('PATH', '')}"
    result = subprocess.run(
        ["bench"] + args,
        capture_output=True, text=True, timeout=300,
        env=env, cwd="/home/frappe/frappe-bench"
    )
    return {"output": result.stdout, "error": result.stderr, "returncode": result.returncode}


class AgentHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if not verify_auth(self.headers):
            self.send_json({"message": "Unauthenticated"}, 401)
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/agent/ping":
            self.send_json({"message": "pong"})
        elif path == "/agent/server":
            self.send_json(config)
        elif path.startswith("/agent/server/running-benches"):
            self.send_json([])
        else:
            self.send_json({"error": "Not Found"}, 404)

    def do_POST(self):
        if not verify_auth(self.headers):
            self.send_json({"message": "Unauthenticated"}, 401)
            return

        content_len = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_len).decode() if content_len else "{}"
        data = json.loads(body) if body else {}

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/agent/benches":
            name = data.get("name", "bench-001")
            result = run_bench_command(["new", "--no-site", name])
            self.send_json({"name": name, "status": "Success", "result": result})

        elif path.startswith("/agent/benches/") and path.endswith("/sites"):
            parts = path.split("/")
            bench_name = parts[3]
            site_name = data.get("name", "site-001")
            admin_password = data.get("admin_password", "admin")
            result = run_bench_command(["new-site", site_name, bench_name, "--force"])
            self.send_json({"name": site_name, "status": "Success", "result": result})

        elif path == "/agent/proxy/reload":
            self.send_json({"status": "Success"})

        elif path == "/agent/server/status":
            self.send_json({"status": "Active"})

        elif path == "/agent/server/change-bench-directory":
            self.send_json({"status": "Success"})

        elif path == "/agent/server/start-bench-workers":
            self.send_json({"status": "Success"})

        elif path == "/agent/server/stop-bench-workers":
            self.send_json({"status": "Success"})

        elif path == "/agent/server/force-remove-all-benches":
            self.send_json({"status": "Success"})

        elif path == "/agent/server/reload":
            self.send_json({"status": "Success"})

        elif path.startswith("/agent/benches/") and "sites" in path and "database" in path:
            self.send_json({"status": "Success"})

        elif path == "/agent/nfs/add-to-acl":
            self.send_json({"status": "Success"})

        elif path == "/agent/nfs/remove-from-acl":
            self.send_json({"status": "Success"})

        elif path == "/agent/nfs/share-sites":
            self.send_json({"status": "Success"})

        else:
            self.send_json({"status": "Success", "note": "mock"})


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    import ssl

    port = int(os.environ.get("AGENT_PORT", 8443))
    server = ThreadedHTTPServer(("0.0.0.0", port), AgentHandler)

    tls_dir = os.path.join(AGENT_DIR, "tls")
    certfile = os.path.join(tls_dir, "fullchain.pem")
    keyfile = os.path.join(tls_dir, "privkey.pem")

    if os.path.exists(certfile) and os.path.exists(keyfile):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile, keyfile)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        print(f"Mock agent listening on HTTPS port {port}")
    else:
        print(f"Mock agent listening on HTTP port {port}")

    server.serve_forever()
