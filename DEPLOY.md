# Deploy to Render.com

## Steps

1. Go to https://render.com and sign up/login

2. Click "New" → "Web Service"

3. Connect GitHub:
   - If you have code on GitHub: Connect your repository
   - If not: 
     - Create new repository on GitHub
     - Upload all files from `pdf_chatbot/` folder to GitHub
     - Then connect that repository

4. Settings:
   - **Name**: `industrial-training-chatbot` (or any name)
   - **Environment**: `Python 3`
   - **Root Directory**: `pdf_chatbot` (IMPORTANT: Set this!)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python start_server.py`
   - **Plan**: Free

5. Environment Variables (click "Add Environment Variable"):
   ```
   GROQ_API_KEY = your_groq_api_key
   SMTP_HOST = smtp.gmail.com
   SMTP_PORT = 587
   SMTP_USERNAME = industrial.training2000@gmail.com
   SMTP_PASSWORD = fgsn vvue qylf nbqy
   FROM_EMAIL = industrial.training2000@gmail.com
   FROM_NAME = Industrial Training Office
   ```

6. Click "Create Web Service"

7. Wait 5-10 minutes for deployment

8. You will get a URL like: `https://your-app-name.onrender.com`

9. Share this URL with users

## Important: Root Directory

**You MUST set Root Directory to `pdf_chatbot` in Render settings!**

This tells Render where your `requirements.txt` and `start_server.py` files are located.

## Notes

- Free plan may sleep after inactivity (takes ~30 seconds to wake up)
- First deployment takes longer
- Check logs if deployment fails

## Alternative: Move files to root

If Root Directory option doesn't work:
1. Move all files from `pdf_chatbot/` folder to GitHub repository root
2. Then use Build Command: `pip install -r requirements.txt`
3. Start Command: `python start_server.py`

