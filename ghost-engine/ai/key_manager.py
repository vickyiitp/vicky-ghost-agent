import os
from itertools import cycle

class KeyRotator:
    def __init__(self, keys=None):
        """
        Initialize the KeyRotator with a list of API keys.
        If no keys are provided, it attempts to load from environment variables 
        (GEMINI_API_KEY, GEMINI_API_KEY_2, GEMINI_API_KEY_3, etc.)
        """
        if keys:
            self.keys = keys
        else:
            self.keys = self._load_keys_from_env()
        
        self.key_cycle = cycle(self.keys)
        self.current_key = next(self.key_cycle) if self.keys else None
        self.current_key_index = 0

    def _load_keys_from_env(self):
        keys = []
        # Try the main key
        main_key = os.getenv("GEMINI_API_KEY")
        if main_key:
            keys.append(main_key)
        
        # Try finding additional keys (GEMINI_API_KEY_2, _3, etc.)
        # Or look for a comma-separated list in GEMINI_API_KEYS
        multi_keys = os.getenv("GEMINI_API_KEYS")
        if multi_keys:
            keys.extend([k.strip() for k in multi_keys.split(",") if k.strip()])
            
        return keys if keys else ["PLACEHOLDER_KEY_ADD_IN_ENV"]

    def get_current_key(self):
        return self.current_key

    def rotate(self):
        """Rotates to the next key in the pool."""
        if not self.keys:
            return None
        
        self.current_key = next(self.key_cycle)
        self.current_key_index = (self.current_key_index + 1) % len(self.keys)
        # Identify the key by a friendly name (e.g., "Identity: Alpha-One")
        return self.current_key

    def get_key_name(self):
        """Returns a 'cool' alias for the current key index."""
        aliases = ["Alpha-One", "Beta-Two", "Gamma-Three", "Delta-Four", "Omega-Prime"]
        idx = self.current_key_index % len(aliases)
        return aliases[idx]
