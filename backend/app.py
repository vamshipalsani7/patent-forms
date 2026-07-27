from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "Patent Forms Backend Running"
    }

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "message": "PDF received successfully"
    }