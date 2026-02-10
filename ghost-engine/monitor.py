import time
import json
import sqlite3
import os
import shutil
import platform
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%H:%M:%S')

# Configuration
# Path to your real Chrome/Brave cookie database
if platform.system() == "Windows":
    CHROME_PATH = os.path.expanduser('~') + r"\AppData\Local\Google\Chrome\User Data\Default\Network\Cookies"
elif platform.system() == "Darwin": # MacOS
    CHROME_PATH = os.path.expanduser('~') + r"/Library/Application Support/Google/Chrome/Default/Cookies"
else: # Linux
    CHROME_PATH = os.path.expanduser('~') + r"/.config/google-chrome/Default/Cookies"

# Since this script runs inside ghost-engine, looking for cookies.json in current dir
TARGET_COOKIES = "cookies.json" 

def sync_cookies():
    logging.info(f"[*] Shadow Monitor: Tracking {CHROME_PATH}...")
    logging.info(f"[*] Target Identity: {os.path.abspath(TARGET_COOKIES)}")
    
    while True:
        try:
            if not os.path.exists(CHROME_PATH):
                logging.warning(f"[-] Chrome Cookie DB not found at {CHROME_PATH}")
                time.sleep(60)
                continue

            # Create a temp copy of the locked cookie file
            shutil.copyfile(CHROME_PATH, "temp_cookies")
            
            # Query the database
            conn = sqlite3.connect("temp_cookies")
            cursor = conn.cursor()
            
            # Note: Modern Chrome uses 'encrypted_value'. For this monitor to fully work
            # with encrypted cookies, you would need to decrypt them using OS-specific keys.
            # This implementation fetches the standard fields.
            cursor.execute("SELECT host_key, name, value, path, is_secure, is_httponly, expires_utc FROM cookies")
            
            cookies = []
            for host, name, val, path, secure, httponly, expires in cursor.fetchall():
                cookies.append({
                    "domain": host,
                    "name": name,
                    "value": val, # Note: often empty in modern Chrome without decryption
                    "path": path,
                    "secure": bool(secure),
                    "httpOnly": bool(httponly),
                    "expires": expires / 1000000 # Convert microseconds to seconds
                })
            
            # Update your Ghost Agent's identity
            with open(TARGET_COOKIES, 'w') as f:
                json.dump(cookies, f, indent=2)
            
            conn.close()
            if os.path.exists("temp_cookies"):
                os.remove("temp_cookies")
            
            logging.info(f"[+] Identity Refreshed: {len(cookies)} cookies synced.")
            
        except Exception as e:
            logging.error(f"[-] Sync Error: {e}")
            
        time.sleep(60) # Sync every 60 seconds

if __name__ == "__main__":
    print("[INIT] Shadow Cookie Monitor v1.0")
    sync_cookies()
