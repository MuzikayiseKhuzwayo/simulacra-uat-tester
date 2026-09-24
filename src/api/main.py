"""Main FastAPI application for Simulacra UAT Engine."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import router

app = FastAPI(
    title="Simulacra UAT Platform API",
    description="Autonomous synthetic user testing, cognitive telemetry streaming, and UX audits.",
    version="2.5.0",
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount screenshots directory for image serving
screenshots_dir = Path(__file__).resolve().parent.parent.parent / "data" / "screenshots"
screenshots_dir.mkdir(parents=True, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=str(screenshots_dir)), name="screenshots")

# Include API router
app.include_router(router)


@app.get("/")
def root():
    return {
        "service": "Simulacra UAT Platform",
        "status": "ready",
        "docs": "/docs",
        "api": "/api",
    }
