# backend/api/routers/scd41.py
from fastapi import APIRouter, HTTPException
from ...scd41 import snapshot_scd41

router = APIRouter(prefix="/scd41", tags=["sensors"])

@router.get("/read")
def read_scd41():
    """Read data from the SCD41 CO2 Sensor."""
    try:
        return snapshot_scd41()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
