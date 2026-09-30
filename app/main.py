"""Main runner for all property scrapers with concurrent execution."""
import logging
import os
import threading
import time
from datetime import datetime
from typing import Dict, Any

from config import Config
from funda import FundaScraper
from jaap import JaapScraper
from pararius import ParariusScraper
from health import start_health_server


def setup_logging(log_dir: str) -> logging.Logger:
    """Setup logging configuration."""
    os.makedirs(log_dir, exist_ok=True)
    
    # Create formatters
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = logging.FileHandler(os.path.join(log_dir, 'scraper.log'))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


class ScraperWorker:
    """Worker class for running individual scrapers in separate threads."""
    
    def __init__(self, scraper_class, config: Config, name: str, sleep_interval: int):
        self.scraper_class = scraper_class
        self.config = config
        self.name = name
        self.sleep_interval = sleep_interval
        self.logger = logging.getLogger(f'{name}_worker')
        self.running = False
        self.thread = None
        self.stats = {
            'runs': 0,
            'errors': 0,
            'last_run': None,
            'last_error': None
        }
    
    def start(self):
        """Start the scraper worker thread."""
        if self.running:
            self.logger.warning(f"{self.name} worker is already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, name=f"{self.name}_thread")
        self.thread.daemon = True
        self.thread.start()
        self.logger.info(f"Started {self.name} scraper worker")
    
    def stop(self):
        """Stop the scraper worker thread."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.logger.info(f"Stopping {self.name} scraper worker...")
            self.thread.join(timeout=30)
    
    def _run_loop(self):
        """Main loop for the scraper worker."""
        self.logger.info(f"{self.name} scraper worker started with {self.sleep_interval}s interval")
        
        while self.running:
            try:
                self.logger.info(f"Running {self.name} scraper")
                start_time = time.time()
                
                # Create scraper instance and run
                scraper_logger = logging.getLogger(f'{self.name}_scraper')
                scraper = self.scraper_class(self.config, scraper_logger)
                scraper.scrape()
                
                # Update stats
                self.stats['runs'] += 1
                self.stats['last_run'] = datetime.now()
                
                duration = time.time() - start_time
                self.logger.info(f"{self.name} scraper completed in {duration:.2f}s, "
                               f"sleeping for {self.sleep_interval}s")
                
                # Sleep with interruption check
                self._interruptible_sleep(self.sleep_interval)
                
            except Exception as e:
                self.stats['errors'] += 1
                self.stats['last_error'] = str(e)
                self.logger.error(f"Error in {self.name} scraper: {e}")
                
                # Sleep shorter on error before retrying
                self._interruptible_sleep(min(60, self.sleep_interval // 10))
        
        self.logger.info(f"{self.name} scraper worker stopped")
    
    def _interruptible_sleep(self, duration: int):
        """Sleep that can be interrupted by stopping the worker."""
        end_time = time.time() + duration
        while self.running and time.time() < end_time:
            time.sleep(1)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the worker."""
        return {
            'name': self.name,
            'running': self.running,
            'alive': self.thread.is_alive() if self.thread else False,
            'stats': self.stats.copy()
        }


class ScraperManager:
    """Manager class for coordinating multiple scraper workers."""
    
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.workers = {}
        self.running = False
        
        # Initialize workers
        self.workers['funda'] = ScraperWorker(
            FundaScraper, config, 'funda', config.sleep_intervals['funda']
        )
        self.workers['pararius'] = ScraperWorker(
            ParariusScraper, config, 'pararius', config.sleep_intervals['pararius']
        )
        self.workers['jaap'] = ScraperWorker(
            JaapScraper, config, 'jaap', config.sleep_intervals['jaap']
        )
    
    def start_all(self):
        """Start all scraper workers."""
        self.running = True
        self.logger.info("Starting all scraper workers...")
        
        for name, worker in self.workers.items():
            try:
                worker.start()
            except Exception as e:
                self.logger.error(f"Failed to start {name} worker: {e}")
        
        self.logger.info("All scraper workers started")
    
    def stop_all(self):
        """Stop all scraper workers."""
        self.running = False
        self.logger.info("Stopping all scraper workers...")
        
        for name, worker in self.workers.items():
            try:
                worker.stop()
            except Exception as e:
                self.logger.error(f"Error stopping {name} worker: {e}")
        
        self.logger.info("All scraper workers stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all workers."""
        return {
            'manager_running': self.running,
            'workers': {name: worker.get_status() for name, worker in self.workers.items()}
        }
    
    def monitor_workers(self):
        """Monitor worker health and restart if needed."""
        while self.running:
            try:
                for name, worker in self.workers.items():
                    if not worker.thread or not worker.thread.is_alive():
                        if worker.running:
                            self.logger.warning(f"{name} worker thread died, restarting...")
                            worker.start()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in worker monitoring: {e}")
                time.sleep(60)


def main():
    """Main function to run all scrapers concurrently."""
    config = Config()
    logger = setup_logging(config.log_dir)
    
    logger.info("Starting concurrent property scraper service")
    logger.info(f"Configuration: Location={config.scraper_config.location}, "
                f"Distance={config.scraper_config.distance}km, "
                f"Max Price=€{config.scraper_config.max_price}")
    
    # Create scraper manager
    manager = ScraperManager(config, logger)
    
    # Start health check server with manager reference
    health_server = start_health_server(manager)
    logger.info("Health check server started on port 8000 with enhanced status endpoints")
    
    try:
        manager.start_all()
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=manager.monitor_workers, name="monitor_thread")
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Log status periodically
        while manager.running:
            time.sleep(300)  # Log status every 5 minutes
            status = manager.get_status()
            logger.info("Scraper Status Summary:")
            for worker_name, worker_status in status['workers'].items():
                stats = worker_status['stats']
                logger.info(f"  {worker_name}: runs={stats['runs']}, errors={stats['errors']}, "
                           f"running={worker_status['running']}, alive={worker_status['alive']}")
    
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
    finally:
        manager.stop_all()
        logger.info("Scraper service stopped")


if __name__ == "__main__":
    main()