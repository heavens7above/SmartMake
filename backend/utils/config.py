import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_KEY = os.getenv("API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Model configuration
    MODEL_NAME = "google/gemini-2.0-flash-lite-001"

config = Config()
