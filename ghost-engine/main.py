import os
import sys
import asyncio
import json
import logging
import uvicorn
import random
import datetime
from urllib.parse import urlparse

# Force ProactorEventLoop on Windows for Playwright
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from playwright.async_api import async_playwright
from ai.service import ai_service
from self_destruct import wipe_evidence
from pdf_generator import create_pdf_report
import shutil

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GhostEngine")

app = FastAPI(title="Vicky-Ghost-Agent Engine")

# Mount Reports Directory for frontend access
if not os.path.exists("reports"):
    os.makedirs("reports")
app.mount("/reports", StaticFiles(directory="reports"), name="reports")

# --- COOKIE VAULT CONFIGURATION ---
COOKIE_VAULT = {
    "x.com": "shadow_vault/x.json",
    "twitter.com": "shadow_vault/x.json",
    "linkedin.com": "shadow_vault/linkedin.json",
    "github.com": "shadow_vault/github.json",
    "reddit.com": "shadow_vault/reddit.json",
    "instagram.com": "shadow_vault/instagram.json"
}

async def get_stealth_context(browser, target_url, base_args):
    """
    Selects the correct identity session based on domain.
    """
    try:
        parsed = urlparse(target_url)
        domain = parsed.netloc.replace("www.", "").lower()
        if "twitter.com" in domain: domain = "x.com"
        
        vault_file = None
        for key, path in COOKIE_VAULT.items():
            if key in domain:
                vault_file = path
                break
        
        # Check specific vault file
        if vault_file and os.path.exists(vault_file):
            await log_event(f"[IDENTITY] 🔓 Loading Stealth Profile: {domain} ({vault_file})")
            return await browser.new_context(storage_state=vault_file, **base_args)
            
        # Fallback to generic cookies.json
        elif os.path.exists("cookies.json"):
            await log_event(f"[IDENTITY] ⚠️ No specific profile for {domain}. Loading generic 'cookies.json'.")
            return await browser.new_context(storage_state="cookies.json", **base_args)
            
        else:
            await log_event(f"[IDENTITY] 👤 Guest Mode (No Auth Found)")
            return await browser.new_context(**base_args)
            
    except Exception as e:
        await log_event(f"[ERROR] Identity Loading Failed: {e}")
        return await browser.new_context(**base_args)

# --- Pydantic Models ---
class ScrapeRequest(BaseModel):
    url: str = Field(..., description="Target URL to scrape")
    command: Optional[str] = Field(None, description="Specific instruction for AI analysis")

class ExportRequest(BaseModel):
    data: Any = Field(..., description="Structured data to export (List or Dict)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Manager for Real-Time Logs
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def log_event(message: str):
    logger.info(message)
    await manager.broadcast(json.dumps({"type": "log", "content": message}))

async def send_data(data: str):
    await manager.broadcast(json.dumps({"type": "data", "content": data}))

@app.get("/")
async def health_check():
    return {"status": "Ghost Engine Online", "model": ai_service.model_id if ai_service.client else "Offline"}

@app.post("/self-destruct")
async def trigger_self_destruct():
    await log_event("[CRITICAL] SELF-DESTRUCT SEQUENCE INITIATED BY USER")
    wipe_evidence()
    return {"status": "System Wiped"}

@app.post("/export-pdf")
async def export_pdf(request: ExportRequest):
    # Expects {"data": [...]}
    data = request.data
    # Normalize data to list if it came as a single object
    if isinstance(data, dict):
        data = [data]
    elif not isinstance(data, list):
        data = [] # Fallback for string or bad types
        
    # We use the persistent latest capture defined in scraping logic
    screenshot_path = "latest_capture.png"
    
    output_filename = f"reports/Ghost_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    if not os.path.exists("reports"):
        os.makedirs("reports")
        
    try:
        current_dir = os.getcwd()
        abs_screenshot = os.path.abspath(screenshot_path)
        
        # Check if screenshot exists before trying to use it
        if not os.path.exists(abs_screenshot):
             await log_event("[WARN] Screenshot missing for report.")
        
        create_pdf_report(data, abs_screenshot, output_filename)
        await log_event(f"[REPORT] generated: {output_filename}")
        
        # Self-Destruct Integration: Wipe raw screenshot after report is secured
        if os.path.exists(screenshot_path):
             os.remove(screenshot_path)
             await log_event("[CLEANUP] Raw evidence (screenshot) incinerated.")
             
        return {"status": "Exported", "path": output_filename}
    except Exception as e:
        await log_event(f"[ERROR] PDF Generation Failed: {e}")
        return {"error": str(e)}

@app.get("/warmer-status")
async def get_warmer_status():
    try:
        status_file = "warmer_status.json"
        if os.path.exists(status_file):
            with open(status_file, "r") as f:
                return json.load(f)
        return {"status": "OFFLINE", "last_heartbeat": "N/A"}
    except Exception as e:
        return {"status": "ERROR", "detail": str(e)}

@app.post("/execute")
async def start_scrape(request: ScrapeRequest):
    url = request.url
    instruction = request.command or ""
    
    if not url:
        return {"error": "URL required"}
    
    request_id = os.urandom(4).hex()
    session_dir = f"./temp_session_{request_id}"
    screenshot_path = f"{session_dir}/capture.png"
    
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)

    await log_event(f"[INIT] Ghost Session {request_id} Started")
    await log_event(f"[TARGET] {url}")
    if instruction:
        await log_event(f"[COMMAND] {instruction}")

    browser = None
    try:
        async with async_playwright() as p:
            await log_event("[ENGINE] Launching Chromium (Headless)...")
            
            # Browser Launch
            browser = await p.chromium.launch(headless=True)
            
            # Context Setup with Session Injection
            context_args = {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "viewport": {"width": 1920, "height": 1080}
            }
            
            # Use Dynamic Identity Switching
            context = await get_stealth_context(browser, url, context_args)

            page = await context.new_page()

            # Navigation
            await log_event("[NETWORK] Navigating to Target...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Special Handling for X.com / Twitter
            if "x.com" in url or "twitter.com" in url:
                await log_event("[BEHAVIOR] Activating Stealth Mode for X.com...")
                
                # 1. Wait for the actual results to hydrate (2026 Selector)
                await log_event("[*] Waiting for X.com search results to hydrate...")
                try:
                    await page.wait_for_selector("article[data-testid='tweet']", timeout=30000)
                except Exception as e:
                    await log_event(f"[WARN] Tweet selector not matching: {e}")

                # 2. Infinite Scroll with Temporal Intelligence
                target_dates = ["Feb 8", "Feb 9"]
                found_target_date = False
                scroll_attempts = 0
                max_scrolls = 15 # Safety limit

                await log_event(f"[*] Engaging Temporal Search for: {target_dates}")

                while not found_target_date and scroll_attempts < max_scrolls:
                    # Scroll down like a human (randomized)
                    scroll_step = random.randint(700, 1200)
                    await page.mouse.wheel(0, scroll_step)
                    scroll_attempts += 1
                    
                    # Behavioral Pause: Let the UI hydrate
                    pause_time = random.uniform(2.5, 4.5)
                    await log_event(f"[SCROLL] Step {scroll_attempts}/{max_scrolls} - Loading historical tweets...")
                    await asyncio.sleep(pause_time)
                    
                    # 4. TEMPORAL INTELLIGENCE: Check the page for target dates
                    # We grab inner text to check for dates. 
                    # note: inner_text is costly on large pages, but safe for text search.
                    try:
                        page_content = await page.inner_text("body")
                        if any(date in page_content for date in target_dates):
                            await log_event(f"[+] TEMPORAL MATCH: Found {target_dates} data. Locking target.")
                            found_target_date = True
                        else:
                            await log_event(f"[*] Scanning for dates... (Attempt {scroll_attempts})")
                    except Exception as e:
                         # Use content() as fallback if inner_text fails
                         await log_event(f"[WARN] Text check failed, using raw HTML check: {e}")
                         content = await page.content()
                         if any(date in content for date in target_dates):
                            found_target_date = True
                            
            else:
                # 4th Layer: Simulated Human Pause for generic sites
                sleep_time = random.uniform(5, 10)
                await log_event(f"[BEHAVIOR] Simulating Human Reading Pattern ({sleep_time:.1f}s)...")
                await asyncio.sleep(sleep_time)
            
            # Local Pre-Filter
            page_text = await page.inner_text("body")
            keywords = ["freelance", "hiring", "job", "opportunity", "ai agent", "ai tool", "developer"]
            if not any(k in page_text.lower() for k in keywords) and instruction == "":
                await log_event("[FILTER] No relevant keywords found. Skipping AI analysis to save quota.")
                await browser.close()
                return {"status": "Skipped", "reason": "No keywords matched"}

            # Vision Capture
            await log_event("[VISION] Capturing Screenshot...")
            await page.screenshot(path=screenshot_path, full_page=True)
            
            # AI Processing
            await log_event(f"[INTELLIGENCE] Transmitting to {ai_service.model_id}...")
            
            # Construct Prompt (Dynamic Master Prompt with Visual Verification)
            task_instruction = instruction if instruction else "Extract the main content, any visible data tables, and key entities."
            
            if "x.com" in url or "twitter.com" in url:
                 # "Hacker-Intelligence" Master Prompt
                 base_prompt = f"""
    You are the Vision Intelligence Core of the Vicky-Ghost-Agent.
    
    USER COMMAND: {task_instruction}
    
    MISSION:
    1. Scan the provided image for the specific keywords mentioned in the command.
    2. VERIFY: Do you see posts dated 'Feb 8' or 'Feb 9'? If not, return [].
    3. EXTRACTION: If verified, extract 'Username', 'Text', 'Date', and 'Link'.
    4. FORMAT: Return ONLY a valid JSON Array. No conversational text.
    
    STRICT FILTER: If a post is an ad or irrelevant to '{task_instruction}', ignore it completely.
    """
            else:
                base_prompt = f"""
You are the Logic Engine for the Vicky-Ghost-Agent. I am providing raw scraped data (visual screenshot).

Your Task: {task_instruction}

Execution Rules:
1. Extraction: Only pull data that directly satisfies the 'Task' above.
2. Fields: Focus on [Username, Content, Timestamp, Source Link] if applicable.
3. Format: Return a VALID JSON Array of objects. No markdown formatting around the JSON.
4. Strictness: No conversational text. If no matches exist, return [].
5. Noise Reduction: Completely ignore ads, 'Who to follow' sidebars, and UI buttons.

Output Example:
[
  {{"field1": "value", "field2": "value"}}
]
"""
            analysis = await ai_service.analyze_image(
                image_path=screenshot_path,
                prompt=base_prompt,
                log_callback=log_event
            )
            
            final_data = []
            if "analysis" in analysis:
                await send_data(analysis["analysis"])
                final_data = analysis["current_data"] if "current_data" in analysis else analysis["analysis"]
                await log_event("[SUCCESS] Intelligence Acquired.")
            else:
                await log_event(f"[ERROR] AI Analysis Failed: {analysis.get('error')}")
                final_data = [{"error": analysis.get('error')}]

            # Auto-Generate Report
            report_filename = f"Ghost_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            report_path = os.path.join("reports", report_filename)
            
            # Use absolute paths for PDF generation to be safe
            abs_ss_path = os.path.abspath(screenshot_path)
            if os.path.exists(abs_ss_path):
                 create_pdf_report(final_data, abs_ss_path, report_path)
                 await log_event(f"[REPORT] Generated: {report_filename}")
            
            if browser:
                await browser.close()
            
            return {
                "status": "Mission Complete",
                "data": final_data,
                "report": report_filename,
                "report_url": f"http://localhost:8000/reports/{report_filename}"
            }

    except Exception as e:
        await log_event(f"[FATAL] {str(e)}")
        if browser:
             await browser.close()
        return {"error": str(e)}
    
    finally:
        # Preserve screenshot for PDF export before cleaning up session dir
        try:
            if os.path.exists(screenshot_path):
                shutil.copy(screenshot_path, "latest_capture.png")
        except Exception as e:
             logger.error(f"Failed to preserve screenshot: {e}")

        # Cleanup specific session files locally
        # Full system wipe only triggers on specific button press
        if os.path.exists(session_dir):
            # Allow file handles to close
            await asyncio.sleep(0.5)
            try:
                shutil.rmtree(session_dir)
            except Exception as e:
                logger.error(f"Cleanup Failed: {e}")
            
            
if __name__ == "__main__":
    # Disable reload to prevent Windows EventLoop issues with Playwright
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
