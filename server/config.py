import os
from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path


load_dotenv()

# Get the project root directory (where this file is located)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PDF_DIR = PROJECT_ROOT / "pdfs"  # Default PDF directory


@dataclass
class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")  # OpenAI API Key
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")  # Google AI API Key  
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "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")  # Groq Cloud API Key
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")  # Default Groq model
    
    # Use environment variable or default to relative path
    # Keep old path as fallback for existing setup
    PDF_FOLDER: str = os.getenv("PDF_FOLDER", r"C:\Users\Asus\Desktop\FYP 2\application\coding\information_data")
    DATA_FOLDER: str = os.getenv("DATA_FOLDER", str(DATA_DIR))
    
    # Teacher PDF management directories
    PDF_CHATBOT_FOLDER: str = os.getenv("PDF_CHATBOT_FOLDER", str(DATA_DIR / "pdf_chatbot"))
    PDF_SUBMISSION_FOLDER: str = os.getenv("PDF_SUBMISSION_FOLDER", str(DATA_DIR / "pdf_submission"))
    PDF_NOTIFICATION_FOLDER: str = os.getenv("PDF_NOTIFICATION_FOLDER", str(DATA_DIR / "pdf_notification"))
    
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEFAULT_LANGUAGE: str = os.getenv("DEFAULT_LANGUAGE", "en")
    
    # Ensure directories exist
    def __post_init__(self):
        # Create PDF directory if it doesn't exist
        Path(self.PDF_FOLDER).mkdir(parents=True, exist_ok=True)
        # Create data directory if it doesn't exist  
        Path(self.DATA_FOLDER).mkdir(parents=True, exist_ok=True)
        # Create teacher PDF directories
        Path(self.PDF_CHATBOT_FOLDER).mkdir(parents=True, exist_ok=True)
        Path(self.PDF_SUBMISSION_FOLDER).mkdir(parents=True, exist_ok=True)
        Path(self.PDF_NOTIFICATION_FOLDER).mkdir(parents=True, exist_ok=True)


settings = Settings()




