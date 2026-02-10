
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def list_models():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("No API Key found.")
        return

    client = genai.Client(api_key=api_key)
    try:
        print("Listing available models...")
        # v1alpha/beta models listing might defer
        # trying standard client.models.list()
        for m in client.models.list():
            if "generateContent" in m.supported_actions:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")

if __name__ == "__main__":
    list_models()
