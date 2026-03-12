from fastapi import APIRouter, HTTPException

from ..models import SensorsRequest
from ...sensors import manager as sensor_manager

router = APIRouter(prefix="/sensors", tags=["sensors"])

@router.post("/read")
def api_sensors(req: SensorsRequest):
    try:
        # Get the specific array for the requested address
        array = sensor_manager.get_array(
            req.addr, 
            do_pin=req.do_pin, 
            use_digital=req.use_digital
        )
        
        # Update gain runtime setting
        array.gain = req.gain
        if array._ads:
            array._ads.gain = req.gain
        
        return array.snapshot(
            samples=req.samples,
            interval=req.interval,
            avg=req.avg,
            invert_do=req.invert_do
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
