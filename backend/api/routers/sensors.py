from fastapi import APIRouter, HTTPException

from ..models import SensorsRequest
from ...sensors import manager as sensor_manager

router = APIRouter(prefix="/sensors", tags=["sensors"])

@router.post("/read")
def api_sensors(req: SensorsRequest):
    try:
        # Override manager defaults with request specifics before snapshot
        sensor_manager.main_array.addr = req.addr
        sensor_manager.main_array.gain = req.gain
        sensor_manager.main_array.do_pin = req.do_pin
        
        return sensor_manager.main_array.snapshot(
            samples=req.samples,
            interval=req.interval,
            avg=req.avg,
            invert_do=req.invert_do
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
