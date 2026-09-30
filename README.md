# Funda Scraper - Improved Version

A robust property scraper for Dutch real estate websites (Funda.nl, Jaap.nl, Pararius.nl) with integrated Kanboard for task management.

## Features

- **Multi-site scraping**: Funda, Jaap, and Pararius
- **Integrated Kanboard**: Local Kanboard instance with automatic task creation
- **Robust error handling**: Retry logic, proper logging, graceful failures
- **Configurable**: Environment variables for all settings
- **Health monitoring**: Built-in health check endpoints
- **Testing**: Comprehensive unit tests
- **Docker support**: Complete stack deployment with Docker Compose

## Quick Start

1. **Build and run the complete stack**:
   ```bash
   ./copy_funda_scraper_files.sh build
   ./copy_funda_scraper_files.sh run
   ```

2. **Setup Kanboard with proper project structure**:
   ```bash
   ./copy_funda_scraper_files.sh setup
   ```

3. **Access Kanboard** (http://localhost:8080):
   ```bash
   ./copy_funda_scraper_files.sh kanboard
   ```
   - Default credentials: `admin/admin`
   - Project "Property Listings" will be created automatically

4. **Monitor the scraper**:
   ```bash
   ./copy_funda_scraper_files.sh logs
   ./copy_funda_scraper_files.sh status
   ```

## Configuration

Configure via environment variables in `docker-compose.yml`:

### Search Parameters
- `LOCATION`: Search location (default: `gemeente-amsterdam`)
- `DISTANCE`: Search radius in km (default: `5`)
- `MAX_PRICE`: Maximum price (default: `450000`)
- `MIN_ROOMS`: Minimum rooms (default: `5`)
- `MIN_AREA`: Minimum area in m² (default: `100`)

### Timing
- `FUNDA_SLEEP`: Sleep after Funda scrape in seconds (default: `3600`)
- `PARARIUS_SLEEP`: Sleep after Pararius scrape in seconds (default: `1800`)
- `JAAP_SLEEP`: Sleep after Jaap scrape in seconds (default: `3600`)

### Kanboard Integration
- `KANBAN_URL`: Kanboard API endpoint (default: `http://kanboard/jsonrpc.php`)
- `KANBAN_USERNAME`: Kanboard username (default: `admin`)
- `KANBAN_PASSWORD`: Kanboard password (default: `admin`)
- `KANBAN_PROJECT_ID`: Project ID (default: `1`)
- `KANBAN_OWNER_ID`: Owner ID (default: `1`)
- `KANBAN_CREATOR_ID`: Creator ID (default: `1`)

## Commands

The `copy_funda_scraper_files.sh` script supports these commands:

- `build` - Build the Docker image
- `run` - Start the scraper service and Kanboard
- `stop` - Stop the scraper service and Kanboard
- `logs` - Show scraper logs
- `test` - Run unit tests
- `shell` - Open shell in running container
- `health` - Check scraper health
- `kanboard` - Open Kanboard in browser
- `kanboard-logs` - Show Kanboard logs
- `status` - Show status of all services

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Docker Compose Stack                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────┐              ┌─────────────────────────┐          │
│  │   Concurrent Scraper    │              │       Kanboard          │          │
│  │    (Port: 8000)         │─────────────▶│     (Port: 8080)        │          │
│  │                         │   JSON-RPC   │                         │          │
│  │ ┌─────────────────────┐ │   API Calls  │ ┌─────────────────────┐ │          │
│  │ │  Scraper Manager    │ │              │ │   Web Interface     │ │          │
│  │ │  - Coordinates      │ │              │ │   - Task Management │ │          │
│  │ │  - Monitors         │ │              │ │   - Project Boards  │ │          │
│  │ │  - Restarts         │ │              │ │   - User Interface  │ │          │
│  │ └─────────────────────┘ │              │ └─────────────────────┘ │          │
│  │           │             │              │                         │          │
│  │           ▼             │              │ ┌─────────────────────┐ │          │
│  │ ┌─────────────────────┐ │              │ │   SQLite Database   │ │          │
│  │ │  Worker Threads     │ │              │ │   - Projects        │ │          │
│  │ │                     │ │              │ │   - Tasks           │ │          │
│  │ │ ┌─────────────────┐ │ │              │ │   - Users           │ │          │
│  │ │ │ Funda Worker    │ │ │              │ │   - Configurations  │ │          │
│  │ │ │ Thread (1h)     │ │ │              │ └─────────────────────┘ │          │
│  │ │ └─────────────────┘ │ │              │                         │          │
│  │ │        ║            │ │              │                         │          │
│  │ │ ┌─────────────────┐ │ │              │                         │          │
│  │ │ │ Pararius Worker │ │ │              │                         │          │
│  │ │ │ Thread (30m)    │ │ │              │                         │          │
│  │ │ └─────────────────┘ │ │              │                         │          │
│  │ │        ║            │ │              │                         │          │
│  │ │ ┌─────────────────┐ │ │              │                         │          │
│  │ │ │ Jaap Worker     │ │ │              │                         │          │
│  │ │ │ Thread (1h)     │ │ │              │                         │          │
│  │ │ └─────────────────┘ │ │              │                         │          │
│  │ └─────────────────────┘ │              │                         │          │
│  │           │             │              │                         │          │
│  │           ▼             │              │                         │          │
│  │ ┌─────────────────────┐ │              │                         │          │
│  │ │  Monitor Thread     │ │              │                         │          │
│  │ │  - Health Checks    │ │              │                         │          │
│  │ │  - Auto Restart     │ │              │                         │          │
│  │ │  - Statistics       │ │              │                         │          │
│  │ └─────────────────────┘ │              │                         │          │
│  │           │             │              │                         │          │
│  │           ▼             │              │                         │          │
│  │ ┌─────────────────────┐ │              │                         │          │
│  │ │  Enhanced Health    │ │              │                         │          │
│  │ │  Server             │ │              │                         │          │
│  │ │  - /health          │ │              │                         │          │
│  │ │  - /status          │ │              │                         │          │
│  │ │  - /workers         │ │              │                         │          │
│  │ └─────────────────────┘ │              │                         │          │
│  └─────────────────────────┘              └─────────────────────────┘          │
│                                                                                 │
│  ┌─────────────────────────┐              ┌─────────────────────────┐          │
│  │    Persistent Storage   │              │    Persistent Storage   │          │
│  │    - Application Logs   │              │    - Kanboard Data      │          │
│  │    - Worker Statistics  │              │    - Project Files      │          │
│  │    - Error Tracking     │              │    - User Preferences   │          │
│  └─────────────────────────┘              └─────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                              External Websites
                         ┌─────────────────────────┐
                         │      Funda.nl           │
                         │      Jaap.nl            │
                         │      Pararius.nl        │
                         └─────────────────────────┘
```

### Data Flow

1. **Concurrent Scraping Architecture**:
   ```
   Main Manager → ScraperWorker (Funda)   → HTTP Request → Funda.nl
                ↓                           ↓
                ScraperWorker (Pararius) → HTTP Request → Pararius.nl
                ↓                           ↓
                ScraperWorker (Jaap)    → HTTP Request → Jaap.nl
                ↓
                Monitor Thread (Health Check & Restart)
   ```

2. **Individual Worker Flow**:
   ```
   Worker Thread → Scraper Instance → HTTP Request → Website
                        ↓
   Parse HTML → Extract Listings → Check Kanboard for Duplicates
                        ↓
   Create New Tasks → Kanboard API → SQLite Database
                        ↓
   Update Stats → Log Results → Sleep (Configurable) → Repeat
   ```

3. **Task Management Flow**:
   ```
   New Property Found → Create Kanboard Task → "New Listings" Column
                              ↓
   User Reviews → Move to "Under Review" → Decision Making
                              ↓
   User Decision → "Interested" or "Not Interested" Column
   ```

4. **Health Monitoring Flow**:
   ```
   Health Server → Manager Status → Worker Status → Individual Stats
                        ↓
   HTTP Endpoints → /health, /status, /workers → JSON Response
   ```

### Core Components

- **`config.py`**: Configuration management with environment variables
- **`base_scraper.py`**: Base class with common functionality (HTTP requests, Kanban integration)
- **`funda.py`**: Funda.nl scraper implementation
- **`jaap.py`**: Jaap.nl scraper implementation  
- **`pararius.py`**: Pararius.nl scraper implementation
- **`main.py`**: Main runner that orchestrates all scrapers
- **`health.py`**: Health check HTTP server
- **`test_scrapers.py`**: Comprehensive unit tests

### Service Communication

- **Scraper ↔ Kanboard**: JSON-RPC API calls over HTTP
- **User ↔ Kanboard**: Web interface on port 8080
- **Monitoring ↔ Scraper**: Health check endpoint on port 8000
- **Scrapers ↔ Websites**: HTTP requests with retry logic and random user agents

### Improvements Over Original

1. **Better Structure**: Object-oriented design with inheritance
2. **Error Handling**: Retry logic, timeouts, graceful failures
3. **Logging**: Structured logging to files and console
4. **Configuration**: Environment-based configuration
5. **Testing**: Unit tests with mocking
6. **Health Monitoring**: HTTP health check endpoint
7. **Documentation**: Comprehensive README and code comments
8. **Deployment**: Docker Compose for easy deployment

## Development

### Running Tests
```bash
./copy_funda_scraper_files.sh test
```

### Local Development
```bash
# Install dependencies
pip install -r app/requirements.txt

# Run individual scrapers
cd app
python funda.py
python jaap.py
python pararius.py

# Run all scrapers
python main.py
```

### Debugging
```bash
# Open shell in running container
./copy_funda_scraper_files.sh shell

# Check logs
./copy_funda_scraper_files.sh logs
```

## Monitoring

### Health Endpoints
- **Basic Health Check**: `http://localhost:8000/health` - Simple health status
- **Detailed Status**: `http://localhost:8000/status` - Complete system status with worker details
- **Worker Statistics**: `http://localhost:8000/workers` - Individual worker performance metrics

### Web Interfaces
- **Kanboard Interface**: `http://localhost:8080` (admin/admin) - Task management
- **Logs**: Available in `./logs/` directory - Persistent log files

### Monitoring Commands
- **Overall Status**: `./copy_funda_scraper_files.sh status` - Docker services + health checks
- **Worker Details**: `curl http://localhost:8000/workers` - Individual worker statistics
- **Live Logs**: `./copy_funda_scraper_files.sh logs` - Real-time log streaming

### Health Check Features
- **Automatic Worker Restart**: Failed workers are automatically restarted
- **Performance Metrics**: Track runs, errors, and success rates per worker
- **Concurrent Monitoring**: All scrapers run simultaneously with independent schedules
- **Docker Health Checks**: Built-in container health monitoring

## Troubleshooting

### Common Issues

1. **Network errors**: The scraper includes retry logic for temporary network issues
2. **Rate limiting**: Random user agents and delays help avoid rate limiting
3. **HTML changes**: If scrapers stop working, the site HTML structure may have changed
4. **Kanban errors**: Check your Kanban credentials and API endpoint

### Logs Location
- Container logs: `./logs/scraper.log`
- Docker logs: `docker-compose logs`

## Security Notes

- Kanban credentials are stored in environment variables
- Use proper authentication tokens
- Consider using Docker secrets for production deployments