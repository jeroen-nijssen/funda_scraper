"""Enhanced health check server with worker status."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


class HealthHandler(BaseHTTPRequestHandler):
    """Enhanced health check handler with worker status."""

    def do_GET(self):
        if self.path == '/health':
            self._handle_health()
        elif self.path == '/status':
            self._handle_status()
        elif self.path == '/workers':
            self._handle_workers()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')

    def _handle_health(self):
        """Basic health check endpoint."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        health_data = {
            "status": "healthy",
            "service": "funda_scraper",
            "timestamp": self._get_timestamp()
        }

        # Add worker status if manager is available
        if hasattr(self.server, 'scraper_manager') and self.server.scraper_manager:
            try:
                manager_status = self.server.scraper_manager.get_status()
                health_data["workers_running"] = manager_status["manager_running"]
                health_data["active_workers"] = sum(
                    1 for worker in manager_status["workers"].values()
                    if worker["running"] and worker["alive"]
                )
                health_data["total_workers"] = len(manager_status["workers"])
            except Exception:
                health_data["workers_status"] = "unavailable"

        self.wfile.write(json.dumps(health_data).encode())

    def _handle_status(self):
        """Detailed status endpoint."""
        if not hasattr(self.server, 'scraper_manager') or not self.server.scraper_manager:
            self.send_response(503)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "Scraper manager not available"}')
            return

        try:
            status = self.server.scraper_manager.get_status()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # Add timestamp
            status["timestamp"] = self._get_timestamp()

            self.wfile.write(json.dumps(status, default=str).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _handle_workers(self):
        """Worker-specific status endpoint."""
        if not hasattr(self.server, 'scraper_manager') or not self.server.scraper_manager:
            self.send_response(503)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "Scraper manager not available"}')
            return

        try:
            status = self.server.scraper_manager.get_status()
            worker_summary = {}

            for name, worker_status in status["workers"].items():
                stats = worker_status["stats"]
                worker_summary[name] = {
                    "running": worker_status["running"],
                    "alive": worker_status["alive"],
                    "total_runs": stats["runs"],
                    "total_errors": stats["errors"],
                    "last_run": str(stats["last_run"]) if stats["last_run"] else None,
                    "last_error": stats["last_error"],
                    "error_rate": round(stats["errors"] / max(stats["runs"], 1) * 100, 2)
                }

            response_data = {
                "timestamp": self._get_timestamp(),
                "workers": worker_summary
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _get_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def log_message(self, format, *args):
        # Suppress default logging
        pass


def start_health_server(scraper_manager: Any | None = None):
    """Start enhanced health check server in background thread."""
    # Binding to all interfaces is intentional: this runs inside a Docker
    # container and must be reachable from the container's HEALTHCHECK and
    # from docker-compose, not just from localhost inside the container.
    server = HTTPServer(('0.0.0.0', 8000), HealthHandler)  # nosec B104

    # Attach scraper manager for status reporting
    if scraper_manager:
        server.scraper_manager = scraper_manager

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server
