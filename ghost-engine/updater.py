import requests
import os
import sys
import logging
from version import VERSION

# Configure logging
logger = logging.getLogger("GhostUpdater")

GITHUB_REPO = "vickyiitp/vicky-ghost-agent"  # Replace with your actual repo if different

def check_for_updates():
    print(f"[*] Checking for Stealth Patches on GitHub for {GITHUB_REPO}...")
    try:
        # Step 1: Query the GitHub API for the latest release
        # Note: This requires the repo to be public or a token to be provided for private repos
        response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest", timeout=5)
        
        if response.status_code == 200:
            latest_release = response.json()
            remote_version = latest_release.get('tag_name', '0.0.0').lstrip('v')

            # Step 2: Compare Local vs Remote
            if remote_version != VERSION:
                print(f"[!] New Version Detected: {remote_version} (Current: {VERSION}). Downloading update...")
                
                # Step 3: Use git to pull the latest changes
                # Assumes git is installed and configured in the environment
                exit_code = os.system("git pull origin main")
                
                if exit_code == 0:
                    print("[SUCCESS] Update Applied. Restarting Ghost Engine...")
                    # Step 4: Hot-reload
                    # Restart the current process with the same arguments
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                else:
                     print("[!] Git pull failed. Please check your git configuration.")
            else:
                print(f"[+] Vicky-Ghost-Agent is up to date (v{VERSION}).")
        elif response.status_code == 404:
             print("[*] No releases found in repository. Skipping update check.")
        else:
             print(f"[!] update check skipped (GitHub API Status: {response.status_code})")
            
    except Exception as e:
        print(f"[!] Update Check Failed: {e}. Proceeding with local version.")

if __name__ == "__main__":
    check_for_updates()
