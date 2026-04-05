from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY")
    SERVICE_PROVIDER = os.getenv("SERVICE_PROVIDER")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None)
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", None)

settings = Settings()