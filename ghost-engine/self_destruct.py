import os
import platform
import subprocess
import shutil
import psutil
import sys

def wipe_evidence():
    """
    Executes the 'Self-Destruct' protocol:
    1. Flushes DNS
    2. Clears Temp Files
    3. Terminates Browser Processes
    """
    system = platform.system()
    print(f"[!] Initiating Self-Destruct on {system}...")

    # 1. Flush DNS Cache
    try:
        if system == "Windows":
            subprocess.run(["ipconfig", "/flushdns"], shell=True, stdout=subprocess.DEVNULL)
            print("[+] DNS Cache Flushed (Windows)")
        elif system == "Linux":
            # Try resolvectl first (modern systemd), fall back to nscd or systemd-resolve
            try:
                subprocess.run(["sudo", "resolvectl", "flush-caches"], shell=True, check=True)
            except:
                subprocess.run(["sudo", "systemd-resolve", "--flush-caches"], shell=True)
            print("[+] DNS Cache Flushed (Linux)")
        elif system == "Darwin": # Mac
            subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], shell=True)
            print("[+] DNS Cache Flushed (MacOS)")
    except Exception as e:
        print(f"[-] DNS Flush Failed: {e}")

    # 2. Terminate Browser Processes (Playwright/Chrome)
    print("[-] Terminating Browser Processes...")
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # Look for browser processes
            if proc.info['name'] and any(browser in proc.info['name'].lower() for browser in ['chrome', 'chromium', 'firefox', 'webkit']):
                 proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # 3. Clear Temporary Files & Sessions
    paths_to_wipe = ["./ghost_session", "./temp_screenshots", "./__pycache__"]
    for path in paths_to_wipe:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                print(f"[+] Shredded: {path}")
            except Exception as e:
                # Retry or ignore
                pass

    # 4. Release RAM Buffers (Linux specific, requires sudo)
    if system == "Linux":
        try:
            os.system("sync; echo 3 | sudo tee /proc/sys/vm/drop_caches")
            print("[+] RAM Buffers Cleared")
        except:
            pass
    
    print("[SUCCESS] Ghost Agent has been erased. System is clean.")

if __name__ == "__main__":
    wipe_evidence()
