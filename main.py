# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db import create_db_and_tables
from fastapi.staticfiles import StaticFiles
import app.routers.bulk as bulk
import app.routers.setup as setup
import app.routers.predict as predict
import app.routers.upload as upload
import app.routers.lands as lands
import app.routers.landmarks as landmarks

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)  # ✅ Use it here

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bulk.router, prefix="/bulk")
app.include_router(setup.router, prefix="/setup")
app.include_router(predict.router, prefix="/predict")
app.include_router(upload.router, prefix="/upload")
app.include_router(lands.router, prefix="/lands")
app.include_router(landmarks.router, prefix="/landmarks")
app.mount("/uploaded_files", StaticFiles(directory="uploaded_files"), name="uploaded_files")
