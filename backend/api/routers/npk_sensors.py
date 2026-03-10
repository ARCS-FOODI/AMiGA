# backend/api/routers/npk_sensors.py
"""
FastAPI router for NPK soil sensor endpoints
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from ..models import NPKSensorsRequest
from ...npk_sensor import manager as npk_manager

router = APIRouter(prefix="/npk-sensors", tags=["npk-sensors"])


@router.post("/read")
def read_npk_sensors(req: NPKSensorsRequest):
    """
    Read all 7 NPK sensor parameters
    
    Returns:
        {
            "timestamp": "ISO format datetime",
            "readings": {
                "ph": float,
                "moisture": float,
                "temperature": float,
                "ec": int,
                "nitrogen": int,
                "phosphorus": int,
                "potassium": int
            },
            "status": "success" or "error",
            "error": "error message if status is error"
        }
    """
    try:
        # Initialize sensor if not already done
        if npk_manager.sensor is None:
            npk_manager.initialize(
                port=req.port,
                slave_id=req.slave_id,
                timeout=req.timeout
            )
        
        # Read all parameters
        readings = npk_manager.read_all()
        
        # Check if any reads were successful
        if all(v is None for v in readings.values()):
            error_msg = npk_manager.sensor.get_last_error() if npk_manager.sensor else "Unknown error"
            raise Exception(error_msg or "Failed to read sensor")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "readings": {
                "ph": round(readings.get('ph'), 2) if readings.get('ph') is not None else None,
                "moisture": round(readings.get('moisture'), 1) if readings.get('moisture') is not None else None,
                "temperature": round(readings.get('temperature'), 1) if readings.get('temperature') is not None else None,
                "ec": int(readings.get('ec')) if readings.get('ec') is not None else None,
                "nitrogen": int(readings.get('nitrogen')) if readings.get('nitrogen') is not None else None,
                "phosphorus": int(readings.get('phosphorus')) if readings.get('phosphorus') is not None else None,
                "potassium": int(readings.get('potassium')) if readings.get('potassium') is not None else None,
            },
            "status": "success",
            "error": None
        }
    
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "readings": None,
            "status": "error",
            "error": str(e)
        }


@router.get("/status")
def get_npk_sensor_status():
    """
    Get NPK sensor connection status
    
    Returns:
        {
            "connected": bool,
            "port": str,
            "slave_id": int,
            "error": str or null
        }
    """
    return npk_manager.get_status()
