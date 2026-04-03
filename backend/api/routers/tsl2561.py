# backend/api/routers/tsl2561.py
from fastapi import APIRouter, HTTPException
from ...tsl2561 import snapshot_tsl2561

router = APIRouter(prefix="/tsl2561", tags=["sensors"])

@router.get("/read")
def read_tsl2561():
    """Read data from the TSL2561 Luminosity Sensor."""
    try:
        return snapshot_tsl2561()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
