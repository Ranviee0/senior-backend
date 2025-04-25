# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db import create_db_and_tables
from fastapi.staticfiles import StaticFiles
import app.routers.bulk as bulk
import app.routers.admin as admin
import app.routers.predict as predict
 
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
app.include_router(admin.router, prefix="/admin")
app.include_router(predict.router, prefix="/predict")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
