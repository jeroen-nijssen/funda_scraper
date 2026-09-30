#!/bin/bash

# Script to build and run the improved funda scraper
# Usage: ./copy_funda_scraper_files.sh [action]
# Actions: build, run, stop, logs, test

set -e

ACTION="${1:-run}"
CONTAINER_NAME="funda_scraper_roermond"
IMAGE_NAME="funda_scraper:latest"

case "$ACTION" in
    "build")
        echo "Building Docker image..."
        docker build -t "$IMAGE_NAME" .
        echo "Build completed successfully!"
        ;;
    
    "run")
        echo "Starting funda scraper with docker-compose..."
        docker-compose up -d
        echo "Scraper started! Check logs with: $0 logs"
        echo "Health check available at: http://localhost:8000/health"
        echo "Kanboard available at: http://localhost:8080"
        echo ""
        echo "Run '$0 setup' to initialize Kanboard with proper project structure"
        ;;
    
    "stop")
        echo "Stopping funda scraper..."
        docker-compose down
        echo "Scraper stopped!"
        ;;
    
    "logs")
        echo "Showing logs (press Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
    
    "test")
        echo "Running tests..."
        docker build -t "$IMAGE_NAME" .
        docker run --rm "$IMAGE_NAME" python -m pytest test_scrapers.py -v
        echo "Tests completed!"
        ;;
    
    "shell")
        echo "Opening shell in container..."
        docker-compose exec funda-scraper /bin/bash
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
        docker-compose logs -f kanboard
        ;;
    
    "setup")
        echo "Setting up Kanboard with proper project structure..."
        python3 setup_kanboard.py
        ;;
    
    "status")
        echo "Checking service status..."
        docker-compose ps
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
except:
    print('  Worker details unavailable')
"
        ;;
    
    *)
        echo "Usage: $0 [build|run|stop|logs|test|shell|health|workers|detailed-status|kanboard|kanboard-logs|setup|status]"
        echo ""
        echo "Commands:"
        echo "  build           - Build the Docker image"
        echo "  run             - Start the scraper service and Kanboard"
        echo "  stop            - Stop the scraper service and Kanboard"
        echo "  logs            - Show scraper logs"
        echo "  test            - Run unit tests"
        echo "  shell           - Open shell in running container"
        echo "  health          - Check basic scraper health"
        echo "  workers         - Show individual worker statistics"
        echo "  detailed-status - Show complete system status"
        echo "  kanboard        - Open Kanboard in browser"
        echo "  kanboard-logs   - Show Kanboard logs"
        echo "  setup           - Initialize Kanboard with proper project structure"
        echo "  status          - Show status of all services with worker summary"
        exit 1
        ;;
esac