from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from .config import settings
from .ingest.indexer import DocumentIndexer
from .qa.retriever import DocumentRetriever
from .qa.llm import LLMClient
from .cv.checker import check_cv
from .teacher.pdf_manager import PDFManager
from .teacher.pdf_metadata import PDFMetadataManager
from .notification.deadline_parser import DeadlineParser
from .notification.student_parser import StudentEmailParser
from .notification.email_sender import EmailSender
from .notification.scheduler import NotificationScheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
TEACHER_ID = "admin"
TEACHER_PASSWORD = "admin123@"

# Global instances
indexer = None
retriever = None
llm_client = None
pdf_manager = None
pdf_metadata_manager = None
notification_scheduler = None

# Simple user storage (for demo - in production use proper database)
USERS_FILE = Path(__file__).parent.parent / "data" / "users.json"
USERS_FILE.parent.mkdir(exist_ok=True)

def load_users():
    """Load users from JSON file"""
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

# Initialize with demo user
def init_users():
    users = load_users()
    if not users:
        users = {
            "1211101529": {
                "password": "123abc@",
                "user_type": "student"
            }
        }
        save_users(users)
    return users

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global indexer, retriever, llm_client, pdf_manager, pdf_metadata_manager, notification_scheduler
    
    logger.info("Starting up Industrial Training Chatbot...")
    
    # Initialize users storage
    init_users()
    
    # Initialize components
    indexer = DocumentIndexer()
    retriever = DocumentRetriever(indexer)
    # Priority: Groq > Google > OpenAI > local
    if settings.GROQ_API_KEY:
        llm_client = LLMClient(use_groq=True)
        logger.info("Using Groq (Llama)")
    elif settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "PUT_YOUR_GOOGLE_API_KEY_HERE":
        llm_client = LLMClient(use_google=True)
        logger.info("Using Google AI (Gemini)")
    else:
        llm_client = LLMClient(use_google=False)
        logger.info("Using OpenAI or local fallback")
    
    # Initialize teacher PDF management
    pdf_manager = PDFManager()
    pdf_metadata_manager = PDFMetadataManager()
    logger.info("Teacher PDF management initialized")
    
    # Initialize notification scheduler
    notification_scheduler = NotificationScheduler()
    notification_scheduler.start()
    logger.info("Notification scheduler initialized and started")
    
    # Index documents on startup - ONLY from teacher uploaded chatbot PDFs
    logger.info(f"Indexing documents from teacher chatbot folder: {settings.PDF_CHATBOT_FOLDER}")
    index_result = indexer.index_directory(settings.PDF_CHATBOT_FOLDER)
    logger.info(f"Indexing complete: {index_result}")
    
    yield
    
    # Shutdown
    if notification_scheduler:
        notification_scheduler.stop()
    logger.info("Shutting down...")


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    language: str


class LoginRequest(BaseModel):
    user_id: str
    password: str


class RegisterRequest(BaseModel):
    user_id: str
    password: str
    user_type: str = "student"  # "student" or "teacher"


class LoginResponse(BaseModel):
    success: bool
    message: str
    user_id: str | None = None
    user_type: str | None = None


app = FastAPI(title="Industrial Training FIST Chatbot", lifespan=lifespan)

# CORS: allow file:// or any dev origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (web frontend) - mount at root after API routes
# Note: This should be added after all API routes are defined
# We'll mount it at the end of the file

#LOGIN LOGIC
@app.post("/api/login", response_model=LoginResponse)
def login(req: LoginRequest):
    user_id = req.user_id.strip()
    password = req.password

    # --- Teacher login (ONLY admin) ---
    if user_id == TEACHER_ID and password == TEACHER_PASSWORD:
        return LoginResponse(
            success=True,
            message="Teacher login successful",
            user_id=user_id,
            user_type="teacher"
        )

    # --- Student login ---
    users = load_users()
    if user_id in users and users[user_id]["password"] == password:
        return LoginResponse(
            success=True,
            message="Student login successful",
            user_id=user_id,
            user_type="student"
        )

    return LoginResponse(
        success=False,
        message="Invalid user ID or password"
    )


# REGISTER (STUDENT ONLY)
@app.post("/api/register", response_model=LoginResponse)
def register(req: RegisterRequest):
    users = load_users()
    user_id = req.user_id.strip()

    if not user_id:
        return LoginResponse(success=False, message="User ID cannot be empty")

    if user_id == TEACHER_ID:
        return LoginResponse(success=False, message="This user ID is reserved")

    if user_id in users:
        return LoginResponse(success=False, message="User ID already exists")

    users[user_id] = {
        "password": req.password,
        "user_type": "student"
    }
    save_users(users)

    return LoginResponse(
        success=True,
        message="Student registration successful",
        user_id=user_id,
        user_type="student"
    )

@app.get("/health")
def health():
    return {
        "status": "ok",
        "pdf_folder": settings.PDF_FOLDER,
        "default_language": settings.DEFAULT_LANGUAGE,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    text = (req.message or "").strip()
    # Force English responses for consistency
    lang = "en"
    
    # Check if we have the RAG components ready
    if not retriever or not llm_client:
        reply = "System is still initializing. Please wait a moment and try again."
        return ChatResponse(reply=reply, language=lang)
    
    # Handle empty messages
    if not text:
        reply = "Hi! I'm your Industrial Training assistant. You can start asking questions anytime."
        return ChatResponse(reply=reply, language=lang)
    
    # Check for farewell keywords
    farewell_map = {
        "en": ["bye", "goodbye", "thank you", "thanks"],
    }
    lowered = text.lower()
    if any(k in lowered for k in farewell_map.get(lang, [])):
        reply = "Thanks for chatting! If you have more questions, just ask anytime."
        return ChatResponse(reply=reply, language=lang)
    
    try:
        # Retrieve relevant chunks - increase k for better coverage
        chunks = retriever.retrieve_relevant_chunks(text, k=8)
        
        if not chunks:
            reply = "I couldn't find that in the Industrial Training documents. Please rephrase or ask another question."
            return ChatResponse(reply=reply, language=lang)
        
        # Format context
        context = retriever.format_context(chunks)
        
        # Generate response using LLM
        llm_result = llm_client.generate_response(text, context, lang)
        reply = llm_result.get('response', 'Sorry, I could not generate a response.')
        
        # If confidence is low, add a clarification
        confidence = llm_result.get('confidence', 0.0)
        if confidence < 0.3:
            reply += " Could you provide more specific details about what you're looking for?"
        
        return ChatResponse(reply=reply, language=lang)
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        reply = "Sorry, I encountered an error while processing your question. Please try again."
        return ChatResponse(reply=reply, language=lang)


def detect_language(text: str) -> str:
    if not text:
        return "en"  # Default to English
    
    # Check for Chinese characters first
    if any('\u4e00' <= ch <= '\u9fff' for ch in text):
        return "zh"
    
    # Check for Malay tokens
    malay_tokens = ["yang", "dan", "atau", "tidak", "sila", "permohonan", "latihan", "industri", "boleh", "adalah", "untuk", "dengan", "dari", "pada", "akan", "telah", "sudah"]
    lowered = text.lower()
    malay_count = sum(1 for tok in malay_tokens if tok in lowered)
    
    # Only use Malay if there are multiple Malay tokens
    if malay_count >= 2:
        return "ms"
    
    # Default to English for everything else
    return "en"


@app.get("/api/status")
def get_status():
    """Get system status and indexing information"""
    if not indexer:
        return {"status": "initializing", "message": "System is starting up..."}
    
    stats = indexer.get_stats()
    return {
        "status": "ready",
        "indexed_documents": stats.get('total_vectors', 0),
        "pdf_folder": settings.PDF_CHATBOT_FOLDER,
        "has_api_key": bool(settings.GROQ_API_KEY or settings.GOOGLE_API_KEY or settings.OPENAI_API_KEY)
    }

@app.post("/api/reindex")
def reindex_documents():
    """Manually trigger document reindexing"""
    if not indexer:
        return {"error": "System not ready"}
    
    try:
        # Reindex only teacher uploaded chatbot PDFs
        result = indexer.index_directory(settings.PDF_CHATBOT_FOLDER)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Reindexing error: {str(e)}")
        return {"error": str(e)}


@app.post("/api/cv-check")
async def cv_check(file: UploadFile = File(...)):
    """CV checker endpoint"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        pdf_content = await file.read()
        result = check_cv(pdf_content)
        return result
    except Exception as e:
        logger.error(f"CV check error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing CV: {str(e)}")


def select_lang(options: dict[str, str], lang: str) -> str:
    return options.get(lang, options.get(settings.DEFAULT_LANGUAGE, next(iter(options.values()))))


# Helper function to check teacher permission
def check_teacher_permission(user_id: str = None) -> bool:
    """Check if user is a teacher"""
    if not user_id:
        return False
    users = load_users()
    return user_id in users and users[user_id].get("user_type") == "teacher"


# Teacher PDF Management API Endpoints
@app.post("/api/teacher/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    pdf_type: str = None,
    user_id: str = None
):
    """Upload a PDF file (teacher only)"""
    # Note: In production, get user_id from session/token
    # For now, we'll accept it as a parameter or header
    
    if not pdf_type or pdf_type not in ["chatbot", "submission", "notification"]:
        raise HTTPException(status_code=400, detail="Invalid pdf_type. Must be: chatbot, submission, or notification")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        pdf_content = await file.read()
        uploaded_by = user_id or "teacher"
        
        result = pdf_manager.upload_pdf(
            file_content=pdf_content,
            filename=file.filename,
            pdf_type=pdf_type,
            uploaded_by=uploaded_by
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Upload failed"))
        
        # Save metadata
        pdf_metadata_manager.add_pdf_metadata(
            filename=result["file_name"],
            pdf_type=pdf_type,
            file_size=result["file_size"],
            uploaded_by=uploaded_by
        )
        
        # If chatbot PDF, trigger reindexing
        if pdf_type == "chatbot":
            logger.info(f"Reindexing chatbot PDF: {result['file_name']}")
            chatbot_dir = pdf_manager.get_directory("chatbot")
            index_result = indexer.index_directory(str(chatbot_dir))
            logger.info(f"Reindexing complete: {index_result}")
        
        return result
        
    except Exception as e:
        logger.error(f"PDF upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading PDF: {str(e)}")


@app.get("/api/teacher/list-pdfs")
def list_pdfs(pdf_type: str):
    """List all PDFs of a specific type (teacher only)"""
    if pdf_type not in ["chatbot", "submission", "notification"]:
        raise HTTPException(status_code=400, detail="Invalid pdf_type. Must be: chatbot, submission, or notification")
    
    try:
        pdf_list = pdf_manager.list_pdfs(pdf_type)
        return {
            "success": True,
            "pdf_type": pdf_type,
            "files": pdf_list,
            "count": len(pdf_list)
        }
    except Exception as e:
        logger.error(f"List PDFs error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing PDFs: {str(e)}")


@app.delete("/api/teacher/delete-pdf")
def delete_pdf(filename: str, pdf_type: str):
    """Delete a PDF file (teacher only)"""
    if pdf_type not in ["chatbot", "submission", "notification"]:
        raise HTTPException(status_code=400, detail="Invalid pdf_type. Must be: chatbot, submission, or notification")
    
    try:
        result = pdf_manager.delete_pdf(filename, pdf_type)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "File not found"))
        
        # Remove metadata
        pdf_metadata_manager.remove_pdf_metadata(filename, pdf_type)
        
        # If chatbot PDF, need to reindex (remove from index)
        if pdf_type == "chatbot":
            logger.info(f"PDF deleted, chatbot index may need manual reindexing")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete PDF error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting PDF: {str(e)}")


@app.get("/api/teacher/pdf-info")
def get_pdf_info(filename: str, pdf_type: str):
    """Get information about a specific PDF (teacher only)"""
    if pdf_type not in ["chatbot", "submission", "notification"]:
        raise HTTPException(status_code=400, detail="Invalid pdf_type. Must be: chatbot, submission, or notification")
    
    try:
        pdf_info = pdf_manager.get_pdf_info(filename, pdf_type)
        if not pdf_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Add metadata if available
        metadata = pdf_metadata_manager.get_pdf_metadata(filename, pdf_type)
        if metadata:
            pdf_info["metadata"] = metadata
        
        return pdf_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get PDF info error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting PDF info: {str(e)}")


# Notification API Endpoints
@app.post("/api/teacher/upload-emails")
async def upload_student_emails(file: UploadFile = File(...)):
    """Upload student email list (CSV or TXT)"""
    try:
        file_content = await file.read()
        student_parser = StudentEmailParser()
        result = student_parser.parse_email_file(file_content, file.filename)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to parse email file"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload emails error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading emails: {str(e)}")


@app.post("/api/teacher/parse-deadline-pdf")
async def parse_deadline_pdf():
    """Parse deadline information from the latest notification PDF"""
    try:
        deadline_parser = DeadlineParser()
        result = deadline_parser.parse_deadline_pdf()
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        # Save deadline info
        if notification_scheduler:
            notification_scheduler.save_deadline_info(result)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parse deadline PDF error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error parsing deadline PDF: {str(e)}")


@app.get("/api/teacher/notification-status")
def get_notification_status():
    """Get notification status and schedule"""
    if not notification_scheduler:
        return {"error": "Notification scheduler not initialized"}
    
    try:
        status = notification_scheduler.get_notification_status()
        return status
    except Exception as e:
        logger.error(f"Get notification status error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting notification status: {str(e)}")


@app.post("/api/teacher/send-notification")
def send_notification_manual(reminder_type: str = "general"):
    """Manually trigger notification sending"""
    if not notification_scheduler:
        raise HTTPException(status_code=500, detail="Notification scheduler not initialized")
    
    try:
        result = notification_scheduler.manual_send_notification(reminder_type)
        return result
    except Exception as e:
        logger.error(f"Manual send notification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending notification: {str(e)}")


@app.get("/api/teacher/notification-history")
def get_notification_history(limit: int = 50):
    """Get notification history"""
    if not notification_scheduler:
        return {"history": []}
    
    try:
        history = notification_scheduler.get_notification_history(limit)
        return {
            "success": True,
            "history": history,
            "count": len(history)
        }
    except Exception as e:
        logger.error(f"Get notification history error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting notification history: {str(e)}")


# Mount static files (web frontend) - must be last
try:
    web_dir = Path(__file__).parent.parent / "web"
    if web_dir.exists():
        app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="static")
        logger.info(f"Serving static files from: {web_dir}")
    else:
        logger.warning(f"Web directory not found: {web_dir}")
except Exception as e:
    logger.warning(f"Could not mount static files: {str(e)}")





