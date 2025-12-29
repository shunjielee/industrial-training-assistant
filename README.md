# Industrial Training FIST Chatbot

FastAPI backend with RAG-based PDF chatbot for Industrial Training program.

## Structure

- `server/` - FastAPI backend
- `web/` - Frontend static files
- `data/` - Data storage (PDFs, indexes, users)

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create `.env` file:
   ```env
   GROQ_API_KEY=your_key
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_password
   FROM_EMAIL=your_email@gmail.com
   FROM_NAME=Industrial Training Office
   ```

3. Run server:
   ```bash
   python start_server.py
   ```

