# backend/api/routers/sis.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from ...sis import snapshot_sis

router = APIRouter(prefix="/sis", tags=["sensors"])

class SISReadRequest(BaseModel):
    port: Optional[str] = None
    slave_id: Optional[int] = None

@router.post("/read")
def read_sis(req: Optional[SISReadRequest] = None):
    """Read data from the Soil Integrated Sensor (SIS)."""
    try:
        if req:
            return snapshot_sis(port=req.port, slave_id=req.slave_id)
        return snapshot_sis()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
