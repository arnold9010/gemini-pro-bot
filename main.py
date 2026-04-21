# main.py
import subprocess
import sys
import time

def start_services():
    """Starts tg.py and site.py as separate subprocesses."""
    print("=== Starting AI Hub Services ===")
    
    # Launch the web interface
    print("[+] Launching site.py (Web UI)...")
    site_process = subprocess.Popen([sys.executable, 'site.py'])
    
    # Launch the Telegram bot
    print("[+] Launching tg.py (Telegram Bot)...")
    tg_process = subprocess.Popen([sys.executable, 'tg.py'])
    
    try:
        # Keep the main script running to monitor the subprocesses
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        # Handle manual exit (Ctrl+C) gracefully to prevent ghost processes
        print("\n[!] Shutting down all services...")
        
        site_process.terminate()
        tg_process.terminate()
        
        site_process.wait()
        tg_process.wait()
        
        print("=== All services stopped successfully ===")

if __name__ == '__main__':
    start_services()