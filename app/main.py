from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
from datetime import datetime

from app.core.config import settings
from app.routers import auth, detections, incidents, dashboard
from app.services.firebase_service import FirebaseService
from app.core.yolo_detector import YOLODetector

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Safety App Backend...")
    
    # Initialize Firebase
    firebase = FirebaseService()
    await firebase.initialize()
    print("✅ Firebase initialized")
    
    # Initialize YOLO detector
    detector = YOLODetector()
    print("✅ YOLO Detector initialized")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Safety App Backend...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Safety App MVP Backend API with YOLO v11 detection",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(detections.router)
app.include_router(incidents.router)
app.include_router(dashboard.router)

@app.get("/")
async def root():
    return {
        "message": "Safety App MVP API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow(),
        "features": [
            "PPE violation detection",
            "Real-time YOLO v11 AI",
            "Incident reporting",
            "Dashboard analytics",
            "Live streaming"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "api": "running",
            "yolo_detector": "ready",
            "firebase": "connected"
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )