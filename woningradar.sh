#!/bin/bash

# Woningradar operator CLI.
# Usage: ./woningradar.sh [command]

set -e

ACTION="${1:-run}"
SCRIPT_NAME="$(basename "$0")"
IMAGE_NAME="woningradar:latest"
SCRAPER_SERVICE="funda-scraper"

# Prefer the Compose v2 plugin, fall back to the standalone v1 binary.
if docker compose version > /dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose > /dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    echo "ERROR: neither 'docker compose' nor 'docker-compose' is available." >&2
    exit 1
fi

case "$ACTION" in
    "build")
        echo "Building Docker image..."
        docker build -t "$IMAGE_NAME" .
        echo "Build completed successfully!"
        ;;

    "run")
        echo "Starting Woningradar..."
        # kanboard-init runs automatically here: compose waits for Kanboard to
        # become healthy, bootstraps the board, and only then starts the scraper.
        $COMPOSE up -d
        echo "Started! Check logs with: $SCRIPT_NAME logs"
        echo "Health check available at: http://localhost:8000/health"
        echo "Kanboard available at:     http://localhost:8080"
        echo ""
        echo "Board setup ran automatically. Re-run it by hand with: $SCRIPT_NAME setup"
        ;;

    "stop")
        echo "Stopping Woningradar..."
        $COMPOSE down
        echo "Stopped!"
        ;;

    "logs")
        echo "Showing logs (press Ctrl+C to exit)..."
        $COMPOSE logs -f
        ;;

    "test")
        echo "Running tests..."
        # pytest is configured in pyproject.toml (pythonpath/testpaths = app),
        # so a bare pytest from the repository root picks up the suite.
        if command -v python3 > /dev/null 2>&1; then
            PY=python3
        else
            PY=python
        fi
        $PY -m pytest
        echo "Tests completed!"
        ;;

    "lint")
        echo "Running ruff..."
        if command -v python3 > /dev/null 2>&1; then
            PY=python3
        else
            PY=python
        fi
        $PY -m ruff check .
        echo "Lint completed!"
        ;;

    "shell")
        echo "Opening shell in container..."
        $COMPOSE exec "$SCRAPER_SERVICE" /bin/bash
        ;;

    "health")
        echo "Checking basic health status..."
        curl -f http://localhost:8000/health || echo "Health check failed"
        ;;

    "workers")
        echo "Checking worker statistics..."
        curl -s http://localhost:8000/workers | python3 -m json.tool || echo "Worker stats unavailable"
        ;;

    "detailed-status")
        echo "Checking detailed system status..."
        curl -s http://localhost:8000/status | python3 -m json.tool || echo "Detailed status unavailable"
        ;;

    "kanboard")
        echo "Opening Kanboard in browser..."
        echo "Kanboard URL: http://localhost:8080"
        echo "Default credentials: admin/admin"
        if command -v open &> /dev/null; then
            open http://localhost:8080
        elif command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:8080
        else
            echo "Please open http://localhost:8080 in your browser"
        fi
        ;;

    "kanboard-logs")
        echo "Showing Kanboard logs..."
        $COMPOSE logs -f kanboard
        ;;

    "setup")
        echo "Setting up the Kanboard project and board columns..."
        # Run inside the compose network so the default http://kanboard resolves.
        $COMPOSE run --rm --no-deps kanboard-init
        ;;

    "status")
        echo "Checking service status..."
        $COMPOSE ps
        echo ""
        echo "Health checks:"
        echo "- Scraper: $(curl -s http://localhost:8000/health 2>/dev/null | grep -q 'healthy' && echo 'OK' || echo 'FAILED')"
        echo "- Kanboard: $(curl -s http://localhost:8080 2>/dev/null | grep -q 'Kanboard' && echo 'OK' || echo 'FAILED')"
        echo ""
        echo "Worker Summary:"
        curl -s http://localhost:8000/workers 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for name, worker in data.get('workers', {}).items():
        status = 'RUNNING' if worker['running'] and worker['alive'] else 'STOPPED'
        print(f'  {name}: {status} (runs: {worker[\"total_runs\"]}, errors: {worker[\"total_errors\"]}, error_rate: {worker[\"error_rate\"]}%)')
except Exception:
    print('  Worker details unavailable')
"
        ;;

    *)
        echo "Usage: $SCRIPT_NAME [command]"
        echo ""
        echo "Commands:"
        echo "  build           - Build the Docker image"
        echo "  run             - Start Kanboard and the scraper (runs board setup first)"
        echo "  stop            - Stop all services"
        echo "  logs            - Show logs"
        echo "  test            - Run the unit tests"
        echo "  lint            - Run ruff over the code base"
        echo "  shell           - Open a shell in the running scraper container"
        echo "  health          - Check basic scraper health"
        echo "  workers         - Show individual worker statistics"
        echo "  detailed-status - Show complete system status"
        echo "  kanboard        - Open Kanboard in the browser"
        echo "  kanboard-logs   - Show Kanboard logs"
        echo "  setup           - Re-run the Kanboard project/column setup by hand"
        echo "  status          - Show status of all services with worker summary"
        exit 1
        ;;
esac
