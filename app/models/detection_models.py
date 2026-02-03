from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DetectionMode(str, Enum):
    PREVENTION = "prevention"
    INCIDENT = "incident"

class ViolationType(str, Enum):
    NO_HELMET = "no_helmet"
    NO_GLOVES = "no_gloves"
    NO_VEST = "no_vest"
    NO_GLASSES = "no_glasses"
    NO_HARNESS = "no_harness"
    MACHINERY_PROXIMITY = "machinery_proximity"
    FALL_RISK = "fall_risk"
    PHONE_USAGE = "phone_usage"
    LOW_VISIBILITY = "low_visibility"

class DetectionRequest(BaseModel):
    image_base64: Optional[str] = None
    mode: DetectionMode = DetectionMode.PREVENTION
    location: Optional[str] = None
    user_id: str
    timestamp: Optional[datetime] = None

class DetectionResponse(BaseModel):
    detection_id: str
    user_id: str
    mode: DetectionMode
    violations: List[ViolationType]
    violations_count: int
    detections: List[Dict[str, Any]]
    savings_estimate: float
    image_url: Optional[str] = None
    location: Optional[str] = None
    timestamp: datetime
    has_violations: bool

class IncidentReport(BaseModel):
    incident_id: str
    user_id: str
    image_url: str
    description: str
    injury_type: Optional[str] = None
    severity: str = "minor"  # minor, moderate, severe
    location: Optional[str] = None
    reported_at: datetime
    status: str = "reported"  # reported, reviewed, resolved
    yolo_detections: Optional[List[Dict[str, Any]]] = None

class LiveDetectionStream(BaseModel):
    stream_id: str
    user_id: str
    session_start: datetime
    violations_detected: int = 0
    risks_avoided: int = 0
    is_active: bool = True