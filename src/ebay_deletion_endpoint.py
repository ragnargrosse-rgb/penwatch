import hashlib
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


HOST = "127.0.0.1"
PORT = 8765

VERIFICATION_TOKEN = os.environ.get(
    "EBAY_DELETION_VERIFICATION_TOKEN",
    "",
)
ENDPOINT_URL = os.environ.get(
    "EBAY_DELETION_ENDPOINT",
    "",
)


class Handler(BaseHTTPRequestHandler):
    def _json_response(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path != "/ebay/account-deletion":
            self._json_response(404, {"error": "not found"})
            return

        query = parse_qs(parsed.query)
        challenge_code = query.get("challenge_code", [None])[0]

        if not challenge_code:
            self._json_response(
                400,
                {"error": "missing challenge_code"},
            )
            return

        if not VERIFICATION_TOKEN or not ENDPOINT_URL:
            self._json_response(
                500,
                {"error": "endpoint not configured"},
            )
            return

        challenge_response = hashlib.sha256(
            (
                challenge_code
                + VERIFICATION_TOKEN
                + ENDPOINT_URL
            ).encode("utf-8")
        ).hexdigest()

        self._json_response(
            200,
            {"challengeResponse": challenge_response},
        )

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path != "/ebay/account-deletion":
            self._json_response(404, {"error": "not found"})
            return

        try:
            content_length = int(
                self.headers.get("Content-Length", "0")
            )
        except ValueError:
            self._json_response(
                400,
                {"error": "invalid content length"},
            )
            return

        # Read the request body so the HTTP request is consumed,
        # but do not persist or print its contents.
        self.rfile.read(content_length)

        print(
            "Received eBay account-deletion notification",
            flush=True,
        )

        self._json_response(200, {"status": "received"})

    def log_message(self, format: str, *args) -> None:
        print(
            "%s - %s" % (self.address_string(), format % args),
            flush=True,
        )


def main() -> None:
    if not VERIFICATION_TOKEN:
        raise RuntimeError(
            "EBAY_DELETION_VERIFICATION_TOKEN is not configured"
        )

    if not ENDPOINT_URL:
        raise RuntimeError(
            "EBAY_DELETION_ENDPOINT is not configured"
        )

    server = ThreadingHTTPServer(
        (HOST, PORT),
        Handler,
    )

    print(
        f"eBay deletion endpoint listening on "
        f"http://{HOST}:{PORT}",
        flush=True,
    )

    server.serve_forever()


if __name__ == "__main__":
    main()
