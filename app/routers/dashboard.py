from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.core.security import get_current_user
from app.services.firebase_service import FirebaseService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
firebase = FirebaseService()

@router.get("/compliance-rate")
async def get_compliance_rate(
    timeframe: str = "week",  # day, week, month
    current_user: dict = Depends(get_current_user)
):
    """Get PPE compliance rate"""
    if current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    stats = await firebase.get_compliance_stats(timeframe)
    
    # Calculate compliance rate
    total_detections = stats.get("total_detections", 1)
    safe_detections = stats.get("safe_detections", 0)
    compliance_rate = (safe_detections / total_detections) * 100
    
    return {
        "compliance_rate": round(compliance_rate, 2),
        "total_detections": total_detections,
        "violations": stats.get("violations", 0),
        "timeframe": timeframe,
        "date_range": stats.get("date_range")
    }

@router.get("/weekly-alerts")
async def get_weekly_alerts(current_user: dict = Depends(get_current_user)):
    """Get weekly alerts summary"""
    if current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    alerts = await firebase.get_weekly_alerts()
    
    return {
        "weekly_alerts": alerts.get("alerts", []),
        "total_alerts": alerts.get("total", 0),
        "top_violations": alerts.get("top_violations", []),
        "week_start": alerts.get("week_start")
    }

@router.get("/non-compliance-list")
async def get_non_compliance_list(current_user: dict = Depends(get_current_user)):
    """Get current non-compliance list"""
    if current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    non_compliant = await firebase.get_current_non_compliance()
    
    return {
        "non_compliant_users": non_compliant.get("users", []),
        "total": non_compliant.get("total", 0),
        "last_updated": datetime.utcnow()
    }

@router.get("/estimated-savings")
async def get_estimated_savings(current_user: dict = Depends(get_current_user)):
    """Get estimated savings from prevented violations"""
    if current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    savings = await firebase.get_estimated_savings()
    
    return {
        "total_savings": savings.get("total", 0),
        "breakdown": savings.get("breakdown", {}),
        "timeframe": "all_time",
        "currency": "USD"
    }

@router.get("/trend-charts")
async def get_trend_charts(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get trend data for charts"""
    if current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    trends = await firebase.get_trend_data(days)
    
    return {
        "daily_violations": trends.get("daily_violations", []),
        "compliance_trend": trends.get("compliance_trend", []),
        "high_risk_days": trends.get("high_risk_days", []),
        "date_range": trends.get("date_range")
    }

@router.get("/real-time-updates")
async def get_real_time_updates(current_user: dict = Depends(get_current_user)):
    """Get real-time dashboard updates"""
    if current_user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    updates = await firebase.get_real_time_updates()
    
    return {
        "active_users": updates.get("active_users", 0),
        "live_sessions": updates.get("live_sessions", 0),
        "recent_violations": updates.get("recent_violations", []),
        "last_updated": datetime.utcnow()
    }