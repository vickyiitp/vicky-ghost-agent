
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not found in .env")
    exit(1)

try:
    client = genai.Client(api_key=api_key)
    print("Listing available models...")
    # The new SDK list_models returns an iterator of Model objects
    # We need to iterate and print their names
    # Note: method might be differnet in new SDK, inspecting dir or trying standard
    
    # Based on newer SDK usage (google-genai)
    for model in client.models.list():
        print(f"Model: {model.name}, Display Name: {model.display_name}")
        
except Exception as e:
    print(f"Error listing models: {e}")
    # Fallback to try old way just in case or print more info
    import traceback
    traceback.print_exc()
