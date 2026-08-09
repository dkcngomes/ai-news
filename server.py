"""
AI News server — serves the frontend and a JSON API.
Run:  python server.py   (then open http://localhost:8000)

Endpoints:
  GET /            -> index.html
  GET /api/news    -> latest scraped news (news.json)
  GET /api/refresh -> re-run the scraper, return fresh news

Zero dependencies: uses only the Python standard library.
"""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8000"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NEWS_FILE = os.path.join(BASE_DIR, "news.json")

_lock = threading.Lock()


def load_news() -> dict:
    try:
        with open(NEWS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"scraped_at": None, "count": 0, "items": []}


def run_scraper() -> dict:
    import scraper
    items = scraper.scrape()
    payload = {
        "scraped_at": scraper.datetime.now(scraper.timezone.utc).isoformat(),
        "count": len(items),
        "items": items,
    }
    with open(NEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


class Handler(BaseHTTPRequestHandler):
    server_version = "AINews/1.0"

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, code: int, obj) -> None:
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]

        if path in ("/", "/index.html"):
            with open(os.path.join(BASE_DIR, "index.html"), "rb") as f:
                self._send(200, f.read(), "text/html; charset=utf-8")
        elif path == "/api/news":
            self._send_json(200, load_news())
        elif path == "/api/refresh":
            with _lock:  # one refresh at a time
                try:
                    payload = run_scraper()
                    self._send_json(200, payload)
                except Exception as e:
                    self._send_json(500, {"error": str(e)})
        else:
            self._send_json(404, {"error": "not found"})

    def log_message(self, fmt, *args) -> None:
        print(f"[{self.log_date_time_string()}] {self.address_string()} {fmt % args}")


def main() -> None:
    # Make sure we have some data on first run
    if not os.path.exists(NEWS_FILE):
        print("No news.json yet — scraping for the first time...")
        with _lock:
            try:
                run_scraper()
            except Exception as e:
                print(f"Initial scrape failed: {e}")

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"AI News running at  http://{HOST}:{PORT}")
    print(f"  Page:      http://{HOST}:{PORT}/")
    print(f"  API:       http://{HOST}:{PORT}/api/news")
    print(f"  Refresh:   http://{HOST}:{PORT}/api/refresh")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")


if __name__ == "__main__":
    main()
