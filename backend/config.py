# Configuration
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration"""

    # API Keys
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///tutor.db')

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

    # AI Model settings
    MODEL_PROVIDER = os.getenv('MODEL_PROVIDER', 'groq')  # groq, openai, anthropic
    MODEL_NAME = os.getenv('MODEL_NAME', 'llama-3.3-70b-versatile')
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '1000'))
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))


config = Config()
