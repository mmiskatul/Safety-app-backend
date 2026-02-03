from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
import cv2
import numpy as np
import base64
import uuid
from datetime import datetime
from typing import List
import asyncio

from app.core.yolo_detector import YOLODetector
from app.models.detection_models import (
    DetectionRequest, DetectionResponse, 
    DetectionMode, LiveDetectionStream
)
from app.services.firebase_service import FirebaseService
from app.core.security import get_current_user

router = APIRouter(prefix="/detections", tags=["detections"])
detector = YOLODetector()
firebase = FirebaseService()

# Store active live streams (in production, use Redis)
active_streams = {}

@router.post("/detect", response_model=DetectionResponse)
async def detect_ppe_violation(
    file: UploadFile = File(...),
    mode: DetectionMode = DetectionMode.PREVENTION,
    location: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Process image for PPE violation detection"""
    try:
        # Read image
        image_bytes = await file.read()
        
        # Run detection
        result = detector.detect_from_bytes(image_bytes)
        
        # Generate unique ID
        detection_id = f"det_{uuid.uuid4().hex[:12]}"
        
        # Upload image to Firebase Storage
        image_url = await firebase.upload_image(
            image_bytes, 
            f"detections/{current_user['user_id']}/{detection_id}.jpg"
        )
        
        # Save to Firestore
        detection_data = {
            "detection_id": detection_id,
            "user_id": current_user["user_id"],
            "mode": mode.value,
            "violations": result["violations"],
            "violations_count": result["violations_count"],
            "detections": result["detections"],
            "savings_estimate": result["savings_estimate"],
            "image_url": image_url,
            "location": location,
            "timestamp": datetime.utcnow(),
            "has_violations": result["has_violations"]
        }
        
        await firebase.save_detection(detection_data)
        
        # Update user stats
        await firebase.update_user_stats(
            current_user["user_id"],
            violations_detected=result["violations_count"],
            savings_estimate=result["savings_estimate"]
        )
        
        # Send push notification if violations detected
        if result["has_violations"]:
            violation_msg = f"⚠️ {len(result['violations'])} safety violations detected!"
            await firebase.send_push_notification(
                current_user["user_id"],
                "Safety Alert",
                violation_msg
            )
        
        return DetectionResponse(**detection_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@router.post("/live/start")
async def start_live_detection(
    current_user: dict = Depends(get_current_user)
):
    """Start a live detection session"""
    stream_id = f"stream_{uuid.uuid4().hex[:8]}"
    
    stream_data = LiveDetectionStream(
        stream_id=stream_id,
        user_id=current_user["user_id"],
        session_start=datetime.utcnow()
    )
    
    active_streams[stream_id] = {
        "data": stream_data.dict(),
        "violations": 0,
        "last_frame": None
    }
    
    await firebase.create_live_session(stream_data.dict())
    
    return {"stream_id": stream_id, "message": "Live session started"}

@router.post("/live/frame/{stream_id}")
async def process_live_frame(
    stream_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Process a frame from live stream"""
    if stream_id not in active_streams:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    image_bytes = await file.read()
    nparr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Process frame
    processed_frame, result = detector.process_live_frame(frame)
    
    # Update stream stats
    if result["has_violations"]:
        active_streams[stream_id]["violations"] += 1
        await firebase.update_live_session(
            stream_id,
            violations_detected=active_streams[stream_id]["violations"]
        )
    
    # Convert processed frame to bytes
    _, buffer = cv2.imencode('.jpg', processed_frame)
    frame_bytes = buffer.tobytes()
    
    # Return base64 for mobile display
    frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
    
    return {
        "processed_frame": frame_base64,
        "detections": result["detections"],
        "has_violations": result["has_violations"],
        "current_violations": active_streams[stream_id]["violations"]
    }

@router.post("/live/stop/{stream_id}")
async def stop_live_detection(
    stream_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Stop a live detection session"""
    if stream_id not in active_streams:
        raise HTTPException(status_code=404, detail="Stream not found")
    
    # Calculate risks avoided (example logic)
    risks_avoided = active_streams[stream_id]["violations"] * 2  # Simplified
    
    await firebase.end_live_session(stream_id, risks_avoided)
    
    # Clean up
    del active_streams[stream_id]
    
    return {
        "message": "Live session ended",
        "total_violations": active_streams.get(stream_id, {}).get("violations", 0),
        "risks_avoided": risks_avoided
    }

@router.get("/history/{user_id}")
async def get_detection_history(
    user_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get detection history for a user"""
    # Check if user is authorized
    if current_user["user_id"] != user_id and current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    history = await firebase.get_user_detections(user_id, limit)
    return history