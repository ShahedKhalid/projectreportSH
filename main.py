from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
import uuid
import re

# Supabase credentials
SUPABASE_URL = "https://scwoojtzgzqcchwcjmiq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjd29vanR6Z3pxY2Nod2NqbWlxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTAzMzk0MzEsImV4cCI6MjA2NTkxNTQzMX0.-GjPVhpHEasWquzKVobrgLvHMJ9So_Wxus4x_MtMvtY"

# App setup
app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to clean file names
def sanitize_filename(name):
    # Remove any non-ASCII or unsafe characters
    return re.sub(r'[^\w\-.]', '', name)

@app.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile = File(...)):
    try:
        # Generate clean filename
        ext = os.path.splitext(file.filename)[1]
        clean_name = sanitize_filename(os.path.splitext(file.filename)[0])
        filename = f"{uuid.uuid4()}_{clean_name}{ext}"
        local_path = os.path.join("uploads", filename)

        # Save file locally
        with open(local_path, "wb") as buffer:
            buffer.write(await file.read())

        # Read file content
        with open(local_path, "rb") as f:
            file_data = f.read()

        # Upload to Supabase Storage
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/octet-stream"
        }

        upload_url = f"{SUPABASE_URL}/storage/v1/object/documents/{filename}"
        async with httpx.AsyncClient() as client:
            response = await client.post(upload_url, headers=headers, content=file_data)

        os.remove(local_path)

        if response.status_code in [200, 201]:
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/documents/{filename}"
            return templates.TemplateResponse("index.html", {
                "request": request,
                "message": "File uploaded successfully!",
                "success": True,
                "url": public_url
            })
        else:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "message": f"Upload failed: {response.text}",
                "success": False
            })

    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "message": "Error: " + str(e),
            "success": False
        })
