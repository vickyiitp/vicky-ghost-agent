import os
import sys
import shutil
import platform
import subprocess
import asyncio
import random
import json
from urllib.parse import urlparse
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
from playwright.async_api import async_playwright
from google import genai
from google.genai import types
from PIL import Image
from fpdf import FPDF
from dotenv import load_dotenv

# Load env if present (for local dev)
load_dotenv()

# --- DYNAMIC COOKIE VAULT ---
# Maps domains to their specific session files
COOKIE_VAULT = {
    "x.com": "shadow_vault/x.json",
    "twitter.com": "shadow_vault/x.json",
    "linkedin.com": "shadow_vault/linkedin.json",
    "github.com": "shadow_vault/github.json",
    "reddit.com": "shadow_vault/reddit.json"
}

async def get_stealth_context(browser, target_url):
    """
    Automatically selects the correct identity (cookies) based on the target URL.
    """
    try:
        # 1. Extract the domain (e.g., 'x.com')
        parsed = urlparse(target_url)
        domain = parsed.netloc.replace("www.", "").lower()
        
        # Handle some common variations if needed
        if "twitter.com" in domain: domain = "x.com"
        
        # 2. Select matching file from Vault, or fallback to generic
        # We search specifically for the domain in our vault keys
        vault_file = None
        for key, path in COOKIE_VAULT.items():
            if key in domain:
                vault_file = path
                break
        
        # 3. Create context
        if vault_file and os.path.exists(vault_file):
            print(f"[*] Identity Confirmed: Loading {domain} session from {vault_file}...")
            # Verify file is valid JSON
            try:
                with open(vault_file, 'r') as f:
                    json.load(f)
                return await browser.new_context(storage_state=vault_file)
            except:
                print(f"[!] Warning: Session file {vault_file} is corrupt. Proceeding as Guest.")
        
        # Fallback to generic cookies.json if it exists and no specific one found
        elif os.path.exists("cookies.json"):
          Use dynamic context selection
        context = await get_stealth_context(browser, url
    except Exception as e:
        print(f"[!] Context Error: {e}")
        return await browser.new_context()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure reports directory exists
os.makedirs("reports", exist_ok=True)
app.mount("/reports", StaticFiles(directory="reports"), name="reports")

# --- STEP 1: RESILIENT AI CONFIG ---
# Try to get keys from env, otherwise fallback to placeholders that must be edited
ENV_KEYS = os.getenv("GEMINI_API_KEYS", "")
API_KEYS = [k.strip() for k in ENV_KEYS.split(",") if k.strip()] 
if not API_KEYS:
     # Fallback for compilation if no env found
     API_KEYS = ["PLACEHOLDER_KEY_1"] 

current_key_index = 0

def get_client():
    global current_key_index
    if not API_KEYS:
        raise ValueError("No API Keys configured")
    
    # Simple rotation
    key = API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(API_KEYS)
    
    return genai.Client(api_key=key)

# --- STEP 2: INFINITE SCROLL & VISION ENGINE ---
async def ghost_scrape(url, target_dates=["Feb 8", "Feb 9"]):
    screenshot_path = "evidence.png"
    
    async with async_playwright() as p:
        # Launch options suitable for bundled exe
        browser = await p.chromium.launch(headless=True)
        
        # Load local cookies if present in same dir
        storage_state = "cookies.json" if os.path.exists("cookies.json") else None
        
        if storage_state:
             context = await browser.new_context(storage_state=storage_state)
        else:
             context = await browser.new_context()
             
        page = await context.new_page()
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Special handling for hydration
            try:
                 await page.wait_for_selector("body", timeout=10000)
            except:
                 pass

            # Infinite scroll until target date is visible
            found = False
            max_scrolls = 15
            for i in range(max_scrolls):
                await page.mouse.wheel(0, 1500)
                await asyncio.sleep(random.uniform(3, 5))
                
                # Check text content
                try:
                    content = await page.content()
                    if any(date in content for date in target_dates):
                        print(f"[+] Found Target Dates: {target_dates}! Capturing...")
                        found = True
                        break
                    print(f"[*] Scrolling deep into archive... {i+1}/{max_scrolls}")
                except:
                    pass
            
            # Additional wait for network idle to ensure images load
            await page.wait_for_load_state("networkidle", timeout=5000)
            await page.screenshot(path=screenshot_path, full_page=False)
        except Exception as e:
            print(f"Scrape Error: {e}")
            return None
        finally:
            await browser.close()
            
    return screenshot_path

# --- STEP 3: SELF-DESTRUCT PROTOCOL ---
def wipe_evidence():
    system = platform.system()
    # Flush DNS to hide site visit logs
    try:
        cmd = "ipconfig /flushdns" if system == "Windows" else "sudo resolvectl flush-caches"
        subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass
        
    # Shred temp files
    for f in ["evidence.png", "ghost_session", "latest_capture.png"]:
        if os.path.exists(f): 
            try:
                if os.path.isdir(f):
                    shutil.rmtree(f)
                else:
                    os.remove(f)
            except:
                pass

# --- REPORT GENERATION ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, 'VICKY-GHOST: INTELLIGENCE REPORT', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(10)

def create_pdf(data_json, image_path, filename="report.pdf"):
    pdf = PDFReport()
    pdf.add_page()
    
    # Page 1: Evidence
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "CAPTURED SOURCE EVIDENCE:", new_x="LMARGIN", new_y="NEXT")
    
    if image_path and os.path.exists(image_path):
        # Ensure image fits within margins
        pdf.image(image_path, x=10, w=190)
    else:
        pdf.cell(0, 10, "Evidence: [Missing or Destroyed]", new_x="LMARGIN", new_y="NEXT")
    
    # Page 2: Structured Intelligence
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(0, 10, "STRUCTURED AI EXTRACTION:", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    try:
        data = json.loads(data_json)
        
        # Use robust table method to prevent layout crashes
        if isinstance(data, list) and len(data) > 0:
            pdf.set_font("Helvetica", size=10)
            
            with pdf.table(borders_layout="SINGLE_TOP_LINE", cell_fill_color=240, cell_fill_mode="ROWS", text_align="LEFT") as table:
                # Add headers based on keys of first object
                keys = list(data[0].keys())
                header_row = table.row()
                for k in keys:
                    header_row.cell(str(k).upper())
                
                # Add Data
                for entry in data:
                    row = table.row()
                    for k in keys:
                        row.cell(str(entry.get(k, "")))
        else:
             pdf.set_font("Helvetica", "I", 12)
             pdf.cell(0, 10, "Raw Intelligence Data:", new_x="LMARGIN", new_y="NEXT")
             pdf.multi_cell(0, 8, str(data))
             
    except Exception as e:
        print(f"PDF Gen Error: {e}")
        pdf.set_font("Courier", size=10)
        pdf.multi_cell(0, 10, str(data_json))
        
    pdf.output(filename)
    return filename

# --- STEP 4: API ENDPOINT ---
class Mission(BaseModel):
    url: str
    command: str

# --- WARMER STATUS ENDPOINT ---
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
async def run_mission(m: Mission):
    print(f"Mission Received: {m.url} | {m.command}")
    
    # 1. Scrape
    ss = await ghost_scrape(m.url)
    if not ss: 
        return {"error": "Target unreachable or dates not found"}
    
    # 2. Vision Analysis
    try:
        client = get_client()
        prompt = f"""
        Analyze this screenshot based on command: '{m.command}'.
        Extract relevant entities (Jobs, News, Dates).
        Return ONLY a JSON Array of objects.
        """
        
        # Read image efficiently
        with open(ss, 'rb') as f:
            image_data = f.read()
            
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, types.Part.from_bytes(data=image_data, mime_type='image/png')]
        )
        cleaned_json = response.text.replace("```json", "").replace("```", "").strip()
        
        # 3. Report
        report_filename = f"Ghost_Report_{random.randint(1000,9999)}.pdf"
        report_path = os.path.join("reports", report_filename)
        create_pdf(cleaned_json, ss, report_path)
        
        # 4. Wipe
        wipe_evidence()
        
        return {
            "status": "Mission Complete", 
            "data": cleaned_json, 
            "report": report_filename,
            "report_url": f"http://localhost:8000/reports/{report_filename}"
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    # Allow running directly
    uvicorn.run(app, host="0.0.0.0", port=8000)
