
import uvicorn
import os
import sys
import threading
import time
import logging
import signal
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stockanalyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StockAnalyzerOrchestrator:
    def __init__(self):
        self.running = True
        self.threads = []
        self.processes = []
        
        # Configuration
        self.fastapi_host = "0.0.0.0"
        self.fastapi_port = 8000
        self.feeder_interval = 300  # 5 minutes
        self.csv_processor_interval = 600  # 10 minutes
        
        # Create necessary directories
        self.setup_directories()
        
    def setup_directories(self):
        """Create necessary directories (respecting existing file hierarchy)"""
        directories = [
            "./uploaded_pdfs",           # FastAPI uploads
            "./ocr_processed_final",     # OCR results
            # Note: webScraper/corporate_filings_pdfs already exists and is managed by nseindia.py
            # Note: webScraper and server folders already exist with the code files
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            
        logger.info("Directories setup completed (respecting existing hierarchy)")
    
    def run_fastapi_server(self):
        """Run FastAPI server in a separate thread"""
        try:
            logger.info(f"Starting FastAPI server on {self.fastapi_host}:{self.fastapi_port}")
            
            # Import and run the FastAPI app
            from server.fastapi import app
            uvicorn.run(
                app,
                host=self.fastapi_host,
                port=self.fastapi_port,
                log_level="info",
                access_log=False  # Reduce log noise
            )
        except Exception as e:
            logger.error(f"FastAPI server error: {e}")
    
    def run_nse_scraper(self):
        """Run NSE scraper in a separate process"""
        try:
            logger.info("Starting NSE web scraper")
            
            # Change to webScraper directory and run nseindia.py
            scraper_path = os.path.join(current_dir, "webScraper", "nseindia.py")
            
            if not os.path.exists(scraper_path):
                logger.error(f"NSE scraper not found at: {scraper_path}")
                return
                
            # Run the scraper as a subprocess
            process = subprocess.Popen(
                [sys.executable, scraper_path],
                cwd=os.path.join(current_dir, "webScraper"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            self.processes.append(process)
            
            # Monitor the process output
            while self.running:
                if process.poll() is not None:
                    # Process has terminated
                    stdout, stderr = process.communicate()
                    if stdout:
                        logger.info(f"NSE scraper output: {stdout.strip()}")
                    if stderr:
                        logger.error(f"NSE scraper error: {stderr.strip()}")
                    
                    if self.running:  # Restart if we're still supposed to be running
                        logger.info("Restarting NSE scraper in 30 seconds...")
                        time.sleep(30)
                        process = subprocess.Popen(
                            [sys.executable, scraper_path],
                            cwd=os.path.join(current_dir, "webScraper"),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            bufsize=1,
                            universal_newlines=True
                        )
                        self.processes.append(process)
                else:
                    time.sleep(30)  # Check every 30 seconds
                    
        except Exception as e:
            logger.error(f"NSE scraper error: {e}")
    
    def run_feeder(self):
        """Run PDF feeder periodically"""
        try:
            # Wait for FastAPI server to start
            logger.info("Waiting for FastAPI server to start...")
            time.sleep(10)
            
            logger.info(f"Starting PDF feeder (interval: {self.feeder_interval}s)")
            
            while self.running:
                try:
                    # Import and run feeder
                    from server.feeder import process_all_pdfs
                    
                    logger.info("Running PDF feeder...")
                    process_all_pdfs()
                    logger.info("PDF feeder cycle completed")
                    
                except Exception as e:
                    logger.error(f"PDF feeder cycle error: {e}")
                
                # Wait for next cycle
                for _ in range(self.feeder_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except Exception as e:
            logger.error(f"PDF feeder error: {e}")
    
    def run_csv_processor(self):
        """Run CSV processor periodically"""
        try:
            # Wait for system to stabilize
            logger.info("Waiting for system to stabilize...")
            time.sleep(30)
            
            logger.info(f"Starting CSV processor (interval: {self.csv_processor_interval}s)")
            
            while self.running:
                try:
                    # Import and run CSV processor
                    import asyncio
                    from server.toCsv import process_all_files
                    
                    logger.info("Running CSV processor...")
                    asyncio.run(process_all_files())
                    logger.info("CSV processor cycle completed")
                    
                except Exception as e:
                    logger.error(f"CSV processor cycle error: {e}")
                
                # Wait for next cycle
                for _ in range(self.csv_processor_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except Exception as e:
            logger.error(f"CSV processor error: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}. Shutting down...")
        self.shutdown()
    
    def shutdown(self):
        """Shutdown all components gracefully"""
        logger.info("Initiating shutdown...")
        self.running = False
        
        # Terminate processes
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                logger.error(f"Error terminating process: {e}")
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        logger.info("Shutdown completed")
    
    def start(self):
        """Start all components"""
        logger.info("=" * 60)
        logger.info("STOCK ANALYZER SYSTEM STARTUP")
        logger.info("=" * 60)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Start FastAPI server in a thread
            fastapi_thread = threading.Thread(target=self.run_fastapi_server, daemon=True)
            fastapi_thread.start()
            self.threads.append(fastapi_thread)
            
            # Start NSE scraper in a thread (which manages a subprocess)
            scraper_thread = threading.Thread(target=self.run_nse_scraper, daemon=True)
            scraper_thread.start()
            self.threads.append(scraper_thread)
            
            # Start PDF feeder in a thread
            feeder_thread = threading.Thread(target=self.run_feeder, daemon=True)
            feeder_thread.start()
            self.threads.append(feeder_thread)
            
            # Start CSV processor in a thread
            csv_thread = threading.Thread(target=self.run_csv_processor, daemon=True)
            csv_thread.start()
            self.threads.append(csv_thread)
            
            logger.info("All components started successfully!")
            logger.info("System is now running. Press Ctrl+C to stop.")
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Startup error: {e}")
        finally:
            self.shutdown()

if __name__ == "__main__":
    orchestrator = StockAnalyzerOrchestrator()
    orchestrator.start()
