import subprocess
import time
import sys
import os
import signal

def run_process(command, cwd=None, new_console=True):
    """
    Runs a command in a new process.
    On Windows, attempts to spawn a new console window for visibility.
    """
    kwargs = {}
    if cwd:
        kwargs['cwd'] = cwd
    
    if sys.platform == 'win32' and new_console:
        kwargs['creationflags'] = subprocess.CREATE_NEW_CONSOLE
    
    return subprocess.Popen(command, shell=True, **kwargs)

def main():
    print("👻 Vicky-Ghost-Agent System Launching...")
    
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    engine_dir = os.path.join(base_dir, "ghost-engine")
    ui_dir = os.path.join(base_dir, "ghost-ui")
    
    processes = []
    
    try:
        # 1. Start Cookie Monitor
        print("[1/3] Starting Identity/Cookie Monitor...")
        p_monitor = run_process("python monitor.py", cwd=engine_dir)
        processes.append(p_monitor)
        time.sleep(1)
        
        # 2. Start Backend API
        print("[2/3] Starting Ghost Engine Backend (Port 8000)...")
        # Using -u for unbuffered output
        p_backend = run_process("python -u main.py", cwd=engine_dir)
        processes.append(p_backend)
        time.sleep(2)
        
        # 3. Start Frontend UI
        print("[3/3] Starting Mission Control Frontend...")
        p_frontend = run_process("npm run dev", cwd=ui_dir)
        processes.append(p_frontend)
        
        print("\n✅ SYSTEM ONLINE")
        print("   -> Backend: http://localhost:8000")
        print("   -> Frontend: http://localhost:5173 (or 5174)")
        print("Press Ctrl+C to terminate all services.")
        
        # Keep main script alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[!] Shutdown Signal Received. Terminating Agents...")
        for p in processes:
            if sys.platform == 'win32':
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(p.pid)])
            else:
                p.terminate()
        print("System Offline.")

if __name__ == "__main__":
    main()
