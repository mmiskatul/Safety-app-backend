from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import Optional
import uuid

from app.core.security import (
    create_access_token, verify_password, 
    get_password_hash, get_current_user
)
from app.services.firebase_service import FirebaseService

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
firebase = FirebaseService()

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """User login with username and password"""
    user = await firebase.get_user_by_username(form_data.username)
    
    if not user or not verify_password(form_data.password, user.get("password_hash")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["user_id"], "role": user.get("role", "user")},
        expires_delta=access_token_expires
    )
    
    # Update last login
    await firebase.update_user_login(user["user_id"])
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user.get("role", "user"),
        "auto_login_token": user.get("auto_login_token")  # For mobile auto-login
    }

@router.post("/register")
async def register_user(
    username: str,
    password: str,
    email: str,
    full_name: str,
    role: str = "user"
):
    """Register new user (superadmin only in production)"""
    # Check if user exists
    existing_user = await firebase.get_user_by_username(username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    
    user_data = {
        "user_id": user_id,
        "username": username,
        "password_hash": get_password_hash(password),
        "email": email,
        "full_name": full_name,
        "role": role,
        "created_at": datetime.utcnow(),
        "last_login": None,
        "auto_login_token": uuid.uuid4().hex,  # For auto-login sessions
        "stats": {
            "total_detections": 0,
            "violations_detected": 0,
            "savings_estimated": 0,
            "risks_avoided": 0
        }
    }
    
    await firebase.create_user(user_data)
    
    return {"message": "User created successfully", "user_id": user_id}

@router.post("/auto-login")
async def auto_login(auto_login_token: str):
    """Auto-login using stored token (for mobile sessions)"""
    user = await firebase.get_user_by_auto_token(auto_login_token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid auto-login token")
    
    # Create new access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["user_id"], "role": user.get("role", "user")},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user["user_id"],
        "username": user["username"]
    }

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (invalidate token on client side)"""
    # In production, you might want to add token to a blacklist
    return {"message": "Logged out successfully"}