import firebase_admin
from firebase_admin import credentials, firestore, storage
from typing import Optional, Dict, Any, List
import uuid
from datetime import datetime
import asyncio
from app.core.config import settings

class FirebaseService:
    def __init__(self):
        self.app = None
        self.db = None
        self.bucket = None
        
    async def initialize(self):
        """Initialize Firebase connection"""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                self.app = firebase_admin.initialize_app(cred, {
                    'storageBucket': settings.FIREBASE_DATABASE_URL
                })
            
            self.db = firestore.client()
            self.bucket = storage.bucket()
            return True
        except Exception as e:
            print(f"❌ Firebase initialization error: {e}")
            return False
    
    async def upload_image(self, image_bytes: bytes, path: str) -> str:
        """Upload image to Firebase Storage"""
        try:
            blob = self.bucket.blob(path)
            blob.upload_from_string(image_bytes, content_type='image/jpeg')
            
            # Make public and get URL
            blob.make_public()
            return blob.public_url
        except Exception as e:
            print(f"❌ Image upload error: {e}")
            return ""
    
    async def save_detection(self, detection_data: Dict[str, Any]):
        """Save detection to Firestore"""
        try:
            doc_ref = self.db.collection('detections').document(detection_data['detection_id'])
            doc_ref.set(detection_data)
            
            # Also add to user's detection history
            user_detections_ref = self.db.collection('users').document(
                detection_data['user_id']
            ).collection('detections').document(detection_data['detection_id'])
            user_detections_ref.set(detection_data)
            
            return True
        except Exception as e:
            print(f"❌ Save detection error: {e}")
            return False
    
    async def get_user_detections(self, user_id: str, limit: int = 50):
        """Get user's detection history"""
        try:
            detections_ref = self.db.collection('users').document(user_id).collection('detections')
            docs = detections_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit).stream()
            
            detections = []
            for doc in docs:
                detections.append(doc.to_dict())
            
            return detections
        except Exception as e:
            print(f"❌ Get detections error: {e}")
            return []