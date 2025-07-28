"""
Simple configuration loader that works without external dependencies
"""
import os

class SimpleConfig:
    """Simple configuration class that loads from environment variables with defaults"""
    
    def __init__(self):
        # Try to load from .env file if it exists
        self._load_env_file()
    
    def _load_env_file(self):
        """Load environment variables from .env file if it exists"""
        env_paths = [
            '.env',
            '../.env',
            './tools/.env',
            os.path.join(os.path.dirname(__file__), '.env'),
            os.path.join(os.path.dirname(__file__), '..', '.env')
        ]
        
        for env_path in env_paths:
            if os.path.exists(env_path):
                try:
                    with open(env_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                key, value = line.split('=', 1)
                                os.environ[key.strip()] = value.strip()
                    break
                except Exception:
                    continue
    
    def get(self, key: str, default=None, cast=str):
        """Get configuration value with type casting"""
        value = os.environ.get(key, default)
        if value is None:
            return None
        try:
            return cast(value)
        except (ValueError, TypeError):
            return default

# Global configuration instance
config = SimpleConfig()

# Configuration values
OLLAMA_BASE_URL = config.get("OLLAMA_BASE_URL", default="http://localhost:11434", cast=str)
OLLAMA_MODEL = config.get("OLLAMA_MODEL", default="mistral:7b-instruct-v0.3-fp16", cast=str)
OLLAMA_TIMEOUT = config.get("OLLAMA_TIMEOUT", default=0, cast=int)
