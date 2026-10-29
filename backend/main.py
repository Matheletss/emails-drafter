"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.database import init_db
from app.routes import contacts, schedule, gmail, logs
from app import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the FastAPI application."""
    # Startup
    init_db()
    # Create uploads directory if it doesn't exist
    os.makedirs(os.getenv("UPLOAD_DIR", "./uploads"), exist_ok=True)
    # Recover any stuck jobs
    scheduler.resume_pending_on_startup()
    yield
    # Shutdown
    scheduler.get_scheduler().shutdown(wait=False)


app = FastAPI(title="Gmail Drafting Agent API", lifespan=lifespan)

# Allow CORS for the Vite React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(contacts.router)
app.include_router(schedule.router)
app.include_router(gmail.router)
app.include_router(logs.router)


@app.get("/")
def read_root():
    return {"message": "Gmail Drafting Agent API is running"}
