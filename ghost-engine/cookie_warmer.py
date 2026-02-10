import asyncio
import json
import datetime
import os
import random
from playwright.async_api import async_playwright

# Configuration
COOKIE_FILE = "cookies.json"
WARMER_STATUS_FILE = "warmer_status.json"
TARGET_SITES = ["https://x.com", "https://linkedin.com", "https://instagram.com"] 
# (You can comment out sites you don't have cookies for yet)

def update_status(status_msg):
    """Updates the status file for the frontend to read."""
    status_data = {
        "status": status_msg,
        "last_heartbeat": str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        "active_sites": TARGET_SITES
    }
    with open(WARMER_STATUS_FILE, "w") as f:
        json.dump(status_data, f)
    print(f"[WARMER] Status updated: {status_msg}")

async def warm_session(url):
    """Visits a site using stored cookies to keep the session alive."""
    print(f"[WARMER] Warming session for: {url}")
    
    if not os.path.exists(COOKIE_FILE):
        print("[WARMER] No cookies.json found. Skipping.")
        return False

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            # Create context with storage state (cookies)
            context = await browser.new_context(storage_state=COOKIE_FILE)
            page = await context.new_page()
            
            # Go to site
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(5, 10)) # Human-like dwell time
            
            # Simple interaction (scroll)
            await page.mouse.wheel(0, 500)
            await asyncio.sleep(2)
            
            title = await page.title()
            print(f"[WARMER] Successfully visited {url} | Title: {title}")
            return True
        except Exception as e:
            print(f"[WARMER] Error warming {url}: {e}")
            return False
        finally:
            await browser.close()

async def main_loop():
    """Continuous loop to warm cookies periodically."""
    print("[WARMER] Shadow Cookie Warmer Initiated...")
    
    while True:
        update_status("ACTIVE") # Green light
        
        # Warm one random site from the list per cycle to be stealthy
        target = random.choice(TARGET_SITES)
        await warm_session(target)
        
        update_status("IDLE") # Amber/Waiting
        
        # Random sleep between 5 to 15 minutes (shortened for demo)
        sleep_time = random.uniform(60, 180) 
        print(f"[WARMER] Sleeping for {int(sleep_time)} seconds...")
        await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        update_status("OFFLINE")
        print("[WARMER] Stopped.")