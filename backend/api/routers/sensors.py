from fastapi import APIRouter, HTTPException

from ..models import SensorsRequest
from ...sensors import manager as sensor_manager

router = APIRouter(prefix="/sensors", tags=["sensors"])

@router.post("/read")
def api_sensors(req: SensorsRequest):
    try:
        return sensor_manager.main_array.snapshot(
            samples=req.samples,
            interval=req.interval,
            avg=req.avg,
            invert_do=req.invert_do,
            addr=req.addr,
            gain=req.gain,
            do_pin=req.do_pin
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
