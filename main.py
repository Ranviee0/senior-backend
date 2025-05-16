from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from app.db import create_db_and_tables
import app.routers.setup as setup
import app.routers.predict as predict
import app.routers.upload as upload
import app.routers.lands as lands
import app.routers.landmarks as landmarks
import app.routers.check as check
import os

UPLOAD_DIR = "uploaded_files"

# ✅ Ensure the directory exists BEFORE app.mount is called
os.makedirs(UPLOAD_DIR, exist_ok=True)

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

# ✅ This now works because the directory exists
app.mount(f"/{UPLOAD_DIR}", StaticFiles(directory=UPLOAD_DIR), name="uploaded_files")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://senior-frontend-13sh.vercel.app", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(setup.router, prefix="/setup")
app.include_router(predict.router, prefix="/predict")
app.include_router(upload.router, prefix="/upload")
app.include_router(lands.router, prefix="/lands")
app.include_router(landmarks.router, prefix="/landmarks")
app.include_router(check.router, prefix="/check")
