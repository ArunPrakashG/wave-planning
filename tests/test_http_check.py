import io
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import helpers  # noqa: F401
import http_check


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _reply(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/items":
            self._reply(200, {"items": ["a", "b"]})
        else:
            self._reply(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        received = self.rfile.read(length).decode()
        if self.path == "/cart/items":
            self._reply(201, {"created": True, "received": received})
        else:
            self._reply(404, {"error": "not found"})


class HttpCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def run_cli(self, *args):
        out = io.StringIO()
        code = http_check.main(list(args), stdout=out)
        return code, out.getvalue()

    def test_get_2xx_passes_by_default(self):
        code, out = self.run_cli("GET", f"{self.base}/items")
        self.assertEqual(code, 0)
        self.assertIn("STATUS 200", out)
        self.assertIn("PASS", out)

    def test_expected_status_must_match(self):
        code, out = self.run_cli("POST", f"{self.base}/cart/items", "--json", '{"sku": "x"}', "--expect-status", "201")
        self.assertEqual(code, 0, out)
        self.assertIn("STATUS 201", out)

    def test_wrong_status_fails(self):
        code, out = self.run_cli("GET", f"{self.base}/items", "--expect-status", "201")
        self.assertEqual(code, 1)
        self.assertIn("FAIL status 200, expected 201", out)

    def test_error_status_fails_by_default(self):
        code, out = self.run_cli("GET", f"{self.base}/missing")
        self.assertEqual(code, 1)
        self.assertIn("STATUS 404", out)

    def test_expected_status_can_be_an_error_code(self):
        code, _ = self.run_cli("GET", f"{self.base}/missing", "--expect-status", "404")
        self.assertEqual(code, 0)

    def test_body_substring_checked(self):
        ok, _ = self.run_cli("GET", f"{self.base}/items", "--expect-body", '"a"')
        bad, out = self.run_cli("GET", f"{self.base}/items", "--expect-body", "zzz")
        self.assertEqual(ok, 0)
        self.assertEqual(bad, 1)
        self.assertIn("FAIL body does not contain 'zzz'", out)

    def test_json_body_is_sent(self):
        code, out = self.run_cli("POST", f"{self.base}/cart/items", "--json", '{"sku": "x"}', "--expect-body", "sku")
        self.assertEqual(code, 0, out)

    def test_connection_refused_is_exit_two(self):
        code, out = self.run_cli("GET", "http://127.0.0.1:1/", "--timeout", "2")
        self.assertEqual(code, 2)
        self.assertIn("ERROR network", out)

    def test_remote_hosts_refused_unless_allowed(self):
        code, out = self.run_cli("GET", "http://example.com/")
        self.assertEqual(code, 2)
        self.assertIn("ERROR refused", out)

    def test_non_http_scheme_refused(self):
        code, out = self.run_cli("GET", "file:///etc/passwd")
        self.assertEqual(code, 2)
        self.assertIn("ERROR refused", out)


if __name__ == "__main__":
    unittest.main()
