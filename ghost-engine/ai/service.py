import os
import asyncio
import random
from google import genai
from google.genai import types
from dotenv import load_dotenv
from .key_manager import KeyRotator

load_dotenv()

class AIService:
    def __init__(self):
        self.rotator = KeyRotator()
        self.model_id = "gemini-2.5-flash"
        # Initial check
        if not self.rotator.keys or self.rotator.keys[0] == "PLACEHOLDER_KEY_ADD_IN_ENV":
            print("Warning: No valid GEMINI_API_KEYs found in environment.")

    async def analyze_image(self, image_path: str, prompt: str, log_callback=None):
        """
        Analyzes an image using the rotating key pool.
        log_callback: Optional async function to send logs back to the frontend.
        """
        if not self.rotator.keys:
             return {"error": "AI service not configured (No Keys)"}
        
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Retry mechanism with Key Rotation
            max_retries = len(self.rotator.keys) * 2 # Try each key at least twice if needed
            
            for attempt in range(max_retries):
                current_key = self.rotator.get_current_key()
                key_alias = self.rotator.get_key_name()
                
                # Instantiate client with current key
                client = genai.Client(api_key=current_key)
                
                try:
                    response = client.models.generate_content(
                        model=self.model_id,
                        contents=[prompt, types.Part.from_bytes(data=image_data, mime_type='image/png')],
                        config=types.GenerateContentConfig(
                            safety_settings=[
                                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
                                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
                                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
                                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE")
                            ]
                        )
                    )
                    return {"analysis": response.text}
                    
                except Exception as e:
                    error_str = str(e)
                    is_exhausted = "429" in error_str or "RESOURCE_EXHAUSTED" in error_str
                    
                    if is_exhausted:
                        if log_callback:
                            await log_callback(f"[ALERT] Identity '{key_alias}' Quota Exhausted (429)")
                        
                        # Rotate Key
                        self.rotator.rotate()
                        new_alias = self.rotator.get_key_name()
                        
                        if log_callback:
                            await log_callback(f"[SYSTEM] Rotating to Identity: {new_alias}")
                            await log_callback(f"[RESUME] Data Arranged via Backup Route")
                        
                        # Short jitter before retrying with new key
                        await asyncio.sleep(random.uniform(1, 3)) 
                        continue
                    
                    # If it's another error but we have retries left, maybe try again? 
                    # For now, only rotate on 429.
                    elif attempt < 2: # Simple retry for connection glitches
                         print(f"AI Glitch: {e}. Retrying same key...")
                         await asyncio.sleep(2)
                         continue
                    else:
                         raise e
                        
        except Exception as e:
            print(f"AI Vision Error: {e}")
            return {"error": str(e)}

    async def analyze_content(self, text_content: str, prompt: str):
        if not self.client:
            return {"error": "AI service not configured"}
        
        try:
            # Retry mechanism for 429
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model_id,
                        contents=f"{prompt}\n\nContent:\n{text_content}"
                    )
                    return {"analysis": response.text}
                except Exception as e:
                     if "429" in str(e) and attempt < max_retries - 1:
                        import random
                        wait_time = (2 ** attempt) + random.uniform(5, 10)
                        print(f"Rate limited (429). Retrying in {wait_time:.2f}s...")
                        await asyncio.sleep(wait_time)
                        continue
                     raise e
                     
        except Exception as e:
            print(f"AI Error: {e}")
            return {"error": str(e)}

ai_service = AIService()
