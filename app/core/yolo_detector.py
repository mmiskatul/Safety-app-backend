import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Any, Tuple
import json
from pathlib import Path
from app.core.config import settings

class YOLODetector:
    def __init__(self):
        self.model = self._load_model()
        self.classes = settings.DETECTION_CLASSES
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD
        
    def _load_model(self):
        """Load YOLO v11 model"""
        try:
            model = YOLO(settings.YOLO_MODEL_PATH)
            print(f"✅ YOLO model loaded from {settings.YOLO_MODEL_PATH}")
            return model
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            # Load a pretrained model as fallback
            model = YOLO('yolov11n.pt')
            print("⚠️  Loaded fallback YOLOv11 model")
            return model
    
    def detect_from_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """Detect PPE violations from image bytes"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Run detection
            results = self.model(image, conf=self.confidence_threshold)
            
            detections = []
            violations = []
            savings_estimate = 0
            
            # OSHA fine estimates (example values)
            fine_estimates = {
                "helmet": 15000,
                "gloves": 7000,
                "vest": 10000,
                "glasses": 8000,
                "harness": 20000,
                "machinery_proximity": 25000,
                "fall_risk": 30000,
                "phone_usage": 5000,
                "low_visibility": 12000
            }
            
            if results[0].boxes is not None:
                for box in results[0].boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    bbox = box.xyxy[0].tolist()
                    
                    class_name = self.classes[class_id] if class_id < len(self.classes) else f"class_{class_id}"
                    
                    detection = {
                        "class": class_name,
                        "confidence": round(confidence, 3),
                        "bbox": [round(coord, 2) for coord in bbox],
                        "center_x": round((bbox[0] + bbox[2]) / 2, 2),
                        "center_y": round((bbox[1] + bbox[3]) / 2, 2),
                        "width": round(bbox[2] - bbox[0], 2),
                        "height": round(bbox[3] - bbox[1], 2)
                    }
                    detections.append(detection)
                    
                    # Check if it's a violation (missing PPE or hazard detected)
                    if class_name in ["machinery_proximity", "fall_risk", "phone_usage", "low_visibility"]:
                        violations.append(class_name)
                        savings_estimate += fine_estimates.get(class_name, 10000)
            
            return {
                "detections": detections,
                "violations": violations,
                "violations_count": len(violations),
                "savings_estimate": savings_estimate,
                "has_violations": len(violations) > 0,
                "image_shape": image.shape[:2]
            }
            
        except Exception as e:
            print(f"❌ Detection error: {e}")
            return {
                "detections": [],
                "violations": [],
                "violations_count": 0,
                "savings_estimate": 0,
                "has_violations": False,
                "error": str(e)
            }
    
    def process_live_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Process live frame for real-time detection"""
        results = self.model(frame, conf=self.confidence_threshold)
        
        detections = []
        violations = []
        
        if results[0].boxes is not None:
            for box in results[0].boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()
                
                # Draw bounding box
                x1, y1, x2, y2 = map(int, bbox)
                class_name = self.classes[class_id] if class_id < len(self.classes) else f"class_{class_id}"
                
                # Color coding: Green for PPE, Red for violations
                color = (0, 255, 0) if class_name not in ["machinery_proximity", "fall_risk", "phone_usage", "low_visibility"] else (0, 0, 255)
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"{class_name}: {confidence:.2f}"
                cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                detections.append({
                    "class": class_name,
                    "confidence": round(confidence, 3),
                    "bbox": bbox
                })
                
                if color == (0, 0, 255):
                    violations.append(class_name)
        
        return frame, {
            "detections": detections,
            "violations": violations,
            "has_violations": len(violations) > 0
        }