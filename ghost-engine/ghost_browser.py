import asyncio
import json
import os
from urllib.parse import urlparse
from playwright.async_api import async_playwright

COOKIE_FILE = "cookies.json"
VAULT_DIR = "shadow_vault"
TARGET_DOMAINS = ["x.com", "twitter.com", "linkedin.com", "instagram.com", "github.com", "reddit.com"]

# Ensure vault exists
if not os.path.exists(VAULT_DIR):
    os.makedirs(VAULT_DIR)

async def run_ghost_browser():
    async with async_playwright() as p:
        # Launch headed browser so user can interact
        browser = await p.chromium.launch(headless=False, channel="chrome") # Try using installed Chrome for better stealth
        
        # Load existing cookies if available
        context = None
        if os.path.exists(COOKIE_FILE):
            try:
                # Validate JSON first
                with open(COOKIE_FILE, 'r') as f:
                    json.load(f)
                context = await browser.new_context(storage_state=COOKIE_FILE)
                print(f"[GHOST] Loaded existing session from {COOKIE_FILE}")
            except:
                print(f"[GHOST] Cookie file invalid, starting fresh.")
                context = await browser.new_context()
        else:
            context = await browser.new_context()

        page = await context.new_page()

        # --- AUTO-SAVE LOGIC ---
        async def save_cookies():
            try:
                cookies = await context.storage_state()
                
                # 1. Save to main generic file
                with open(COOKIE_FILE, "w") as f:
                    json.dump(cookies, f, indent=2)
                
                # 2. Smart-Save to Vault based on current Domain
                try:
                    current_url = page.url
                    domain = urlparse(current_url).netloc.replace("www.", "").lower()
                    
                    target_file = None
                    if "x.com" in domain or "twitter.com" in domain:
                        target_file = "x.json"
                    elif "linkedin.com" in domain:
                        target_file = "linkedin.json"
                    elif "github.com" in domain:
                        target_file = "github.json"
                    elif "reddit.com" in domain:
                        target_file = "reddit.json"
                    elif "instagram.com" in domain:
                        target_file = "instagram.json"

                    if target_file:
                        vault_path = os.path.join(VAULT_DIR, target_file)
                        with open(vault_path, "w") as f:
                            json.dump(cookies, f, indent=2)
                        print(f"[VAULT] 🔒 Identity securely backed up to {vault_path}")

                except Exception as ex:
                    print(f"Vault Error: {ex}")
                    
                print(f"[GHOST] 💾 Cookies auto-updated at {asyncio.get_event_loop().time()}")
                
                # Update warmer status if it exists
                if os.path.exists("warmer_status.json"):
                    try:
                        with open("warmer_status.json", "r") as f:
                            status = json.load(f)
                        status["last_cookie_update"] = str(asyncio.get_event_loop().time())
                        with open("warmer_status.json", "w") as f:
                            json.dump(status, f)
                    except:
                        pass
            except Exception as e:
                print(f"Error saving cookies: {e}")

        # Save on every navigation
        page.on("load", lambda _: asyncio.create_task(save_cookies()))
        
        # Also save periodically in case of dynamic SPA changes
        async def periodic_save():
            while True:
                await asyncio.sleep(5)
                await save_cookies()

        asyncio.create_task(periodic_save())
        
        print("\n" + "="*60)
        print("👻 GHOST BROWSER ACTIVE")
        print(f"Use this window to browse: {', '.join(TARGET_DOMAINS)}")
        print("Cookies will be captured AUTOMATICALLY while you browse.")
        print("Close the browser window to stop.")
        print("="*60 + "\n")

        await page.goto("https://x.com") # Start at target
        
        # Keep process alive until browser is closed
        try:
            await page.wait_for_close()
        except:
            pass
        
        # Final save
        await save_cookies()
        print("[GHOST] Browser closed. Session saved.")

if __name__ == "__main__":
    try:
        asyncio.run(run_ghost_browser())
    except KeyboardInterrupt:
        pass
