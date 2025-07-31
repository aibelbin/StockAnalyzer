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
GROQ_API_KEY = config.get("GROQ_API_KEY", default="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", cast=str)
GROQ_API_URL = config.get("GROQ_API_URL", default="https://api.groq.com/openai/v1", cast=str)
GROQ_MODEL = config.get("GROQ_MODEL", default="llama3-70b-8192", cast=str)
GROQ_TIMEOUT = config.get("GROQ_TIMEOUT", default=60, cast=int)
