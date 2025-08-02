#!/usr/bin/env python3
"""
Persistent StockAnalyzer Server
===============================
This script runs the StockAnalyzer server continuously and prevents the laptop from sleeping.
It includes auto-restart capabilities and robust error handling.
"""

import os
import sys
import time
import signal
import subprocess
import threading
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./persistent_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PersistentServer:
    def __init__(self):
        self.server_process = None
        self.feeder_process = None
        self.csv_process = None
        self.running = True
        self.restart_count = 0
        self.max_restarts = 100  # Allow many restarts for 24/7 operation
        
        # Setup virtual environment
        self.setup_virtual_env()
        
        # Prevent laptop sleep
        self.caffeine_process = None
        self.prevent_sleep()
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
        self.running = False
        self.cleanup()
    
    def setup_virtual_env(self):
        """Setup and activate virtual environment"""
        self.venv_path = None
        self.python_executable = sys.executable
        
        # Check for existing virtual environments
        possible_venv_paths = [
            './venv',
            './env', 
            './stockanalyzer_env',
            os.path.expanduser('~/venv/stockanalyzer'),
            os.path.expanduser('~/.virtualenvs/stockanalyzer')
        ]
        
        for venv_path in possible_venv_paths:
            if os.path.exists(venv_path):
                python_path = os.path.join(venv_path, 'bin', 'python')
                if os.path.exists(python_path):
                    self.venv_path = venv_path
                    self.python_executable = python_path
                    logger.info(f"Found virtual environment: {venv_path}")
                    break
        
        if not self.venv_path:
            # Create a new virtual environment
            logger.info("Creating new virtual environment...")
            try:
                subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
                self.venv_path = './venv'
                self.python_executable = './venv/bin/python'
                logger.info("Created virtual environment: ./venv")
                
                # Install requirements
                self.install_requirements()
                
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create virtual environment: {e}")
                logger.info("Continuing with system Python...")
                self.python_executable = sys.executable
        else:
            # Verify packages are installed
            self.verify_packages()
    
    def install_requirements(self):
        """Install required packages in virtual environment"""
        try:
            logger.info("Installing required packages...")
            pip_path = os.path.join(self.venv_path, 'bin', 'pip')
            
            # Essential packages for the StockAnalyzer
            packages = [
                'fastapi',
                'uvicorn',
                'requests',
                'pdf2image',
                'pillow', 
                'opencv-python',
                'pytesseract',
                'python-multipart',
                'aiofiles'
            ]
            
            for package in packages:
                logger.info(f"Installing {package}...")
                result = subprocess.run([pip_path, 'install', package], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    logger.warning(f"Failed to install {package}: {result.stderr}")
                    
            logger.info("Package installation completed")
            
        except Exception as e:
            logger.error(f"Error installing packages: {e}")
    
    def verify_packages(self):
        """Verify required packages are available"""
        try:
            result = subprocess.run([
                self.python_executable, '-c', 
                'import fastapi, uvicorn, requests, pdf2image, PIL, cv2, pytesseract; print("All packages available")'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("All required packages are available")
            else:
                logger.warning("Some packages may be missing, attempting to install...")
                self.install_requirements()
                
        except Exception as e:
            logger.error(f"Error verifying packages: {e}")
        
    def prevent_sleep(self):
        """Prevent laptop from sleeping using various methods"""
        try:
            # Method 1: Try caffeine (if installed)
            try:
                self.caffeine_process = subprocess.Popen(
                    ['caffeine'], 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL
                )
                logger.info("Started caffeine to prevent sleep")
                return
            except FileNotFoundError:
                pass
            
            # Method 2: Try systemd-inhibit (most Linux systems)
            try:
                self.caffeine_process = subprocess.Popen([
                    'systemd-inhibit', 
                    '--what=sleep:idle', 
                    '--who=StockAnalyzer',
                    '--why=Running 24/7 stock analysis',
                    'sleep', 'infinity'
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info("Started systemd-inhibit to prevent sleep")
                return
            except FileNotFoundError:
                pass
                
            # Method 3: Disable power management (requires sudo - will fail gracefully)
            try:
                subprocess.run([
                    'sudo', 'systemctl', 'mask', 'sleep.target', 
                    'suspend.target', 'hibernate.target', 'hybrid-sleep.target'
                ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info("Attempted to disable power management via systemctl")
            except:
                pass
                
            logger.warning("Could not prevent sleep automatically. Please disable sleep manually or install caffeine")
            
        except Exception as e:
            logger.warning(f"Error preventing sleep: {e}")
    
    def start_server(self):
        """Start the FastAPI server"""
        try:
            logger.info("Starting FastAPI server...")
            self.server_process = subprocess.Popen([
                self.python_executable, 'run_server.py'
            ], cwd=os.getcwd())
            
            # Wait for server to start
            time.sleep(10)
            
            # Check if server is still running
            if self.server_process.poll() is None:
                logger.info("FastAPI server started successfully")
                return True
            else:
                logger.error("FastAPI server failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            return False
    
    def start_feeder(self):
        """Start the PDF feeder"""
        try:
            logger.info("Starting PDF feeder...")
            self.feeder_process = subprocess.Popen([
                self.python_executable, 'server/feeder.py'
            ], cwd=os.getcwd())
            
            time.sleep(5)
            
            if self.feeder_process.poll() is None:
                logger.info("PDF feeder started successfully")
                return True
            else:
                logger.error("PDF feeder failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Error starting feeder: {e}")
            return False
    
    def start_csv_processor(self):
        """Start the CSV processor in monitoring mode"""
        try:
            logger.info("Starting CSV processor...")
            # Create a wrapper script that runs CSV processor periodically
            csv_script = f'''
import time
import subprocess
import sys
import os

while True:
    try:
        print("Running CSV processor cycle...")
        result = subprocess.run(["{self.python_executable}", "server/toCsv.py"], 
                              cwd=os.getcwd(), 
                              capture_output=True, 
                              text=True, 
                              timeout=1800)  # 30 minute timeout
        print("CSV processor cycle completed")
        time.sleep(300)  # Wait 5 minutes between cycles
    except Exception as e:
        print(f"CSV processor error: {{e}}")
        time.sleep(60)  # Wait 1 minute on error
'''
            self.csv_process = subprocess.Popen([
                self.python_executable, '-c', csv_script
            ], cwd=os.getcwd())
            
            time.sleep(5)
            
            if self.csv_process.poll() is None:
                logger.info("CSV processor started successfully")
                return True
            else:
                logger.error("CSV processor failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Error starting CSV processor: {e}")
            return False
    
    def monitor_processes(self):
        """Monitor all processes and restart if needed"""
        while self.running and self.restart_count < self.max_restarts:
            try:
                time.sleep(60)  # Check every minute
                
                restart_needed = False
                
                # Check server
                if self.server_process and self.server_process.poll() is not None:
                    logger.warning("FastAPI server stopped unexpectedly")
                    restart_needed = True
                
                # Check feeder
                if self.feeder_process and self.feeder_process.poll() is not None:
                    logger.warning("PDF feeder stopped unexpectedly")
                    restart_needed = True
                
                # Check CSV processor
                if self.csv_process and self.csv_process.poll() is not None:
                    logger.warning("CSV processor stopped unexpectedly")
                    restart_needed = True
                
                if restart_needed:
                    logger.info("Restarting components...")
                    self.restart_components()
                    
            except Exception as e:
                logger.error(f"Error in monitoring: {e}")
                time.sleep(60)
    
    def restart_components(self):
        """Restart all components"""
        self.restart_count += 1
        logger.info(f"Restart attempt #{self.restart_count}")
        
        # Stop existing processes
        self.stop_processes()
        
        # Wait a bit
        time.sleep(10)
        
        # Start components
        if not self.start_server():
            logger.error("Failed to restart server")
            return False
            
        if not self.start_feeder():
            logger.error("Failed to restart feeder")
            return False
            
        if not self.start_csv_processor():
            logger.error("Failed to restart CSV processor")
            return False
        
        logger.info("All components restarted successfully")
        return True
    
    def stop_processes(self):
        """Stop all running processes"""
        processes = [
            ("Server", self.server_process),
            ("Feeder", self.feeder_process),
            ("CSV Processor", self.csv_process)
        ]
        
        for name, process in processes:
            if process and process.poll() is None:
                try:
                    logger.info(f"Stopping {name}...")
                    process.terminate()
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing {name}...")
                    process.kill()
                except Exception as e:
                    logger.error(f"Error stopping {name}: {e}")
    
    def cleanup(self):
        """Cleanup on shutdown"""
        logger.info("Cleaning up...")
        
        self.stop_processes()
        
        # Stop caffeine/sleep prevention
        if self.caffeine_process and self.caffeine_process.poll() is None:
            try:
                self.caffeine_process.terminate()
                logger.info("Stopped sleep prevention")
            except:
                pass
        
        logger.info("Cleanup completed")
    
    def run(self):
        """Main run loop"""
        logger.info("=" * 60)
        logger.info("STARTING PERSISTENT STOCKANALYZER SERVER")
        logger.info("=" * 60)
        logger.info("This server will run continuously and restart automatically")
        logger.info("Press Ctrl+C to stop gracefully")
        logger.info("=" * 60)
        
        # Start all components
        if not self.start_server():
            logger.error("Failed to start server. Exiting.")
            return False
            
        if not self.start_feeder():
            logger.error("Failed to start feeder. Exiting.")
            return False
            
        if not self.start_csv_processor():
            logger.error("Failed to start CSV processor. Exiting.")
            return False
        
        logger.info("All components started successfully!")
        logger.info("System is now running in persistent mode...")
        
        # Monitor processes
        try:
            self.monitor_processes()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
        finally:
            self.cleanup()
        
        return True

def main():
    # Change to script directory
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    server = PersistentServer()
    success = server.run()
    
    if success:
        logger.info("Server shut down gracefully")
    else:
        logger.error("Server encountered errors")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
