from fastapi import APIRouter, HTTPException, Depends

from ..models import ControlCycleRequest
from ...pumps import StepperPump
from ...control import controller
from .pumps import get_valid_pump

router = APIRouter(prefix="/control", tags=["control"])

@router.post("/cycle-once")
def api_control_cycle(
    req: ControlCycleRequest, 
    pump: StepperPump = Depends(lambda r=Depends(): get_valid_pump(r.pump))
):
    try:
        return controller.evaluate_cycle(
            pump_name=pump.name,
            target_threshold=req.target_threshold,
            vote_k=req.vote_k,
            hz=req.hz,
            irrigate_seconds=req.irrigate_seconds,
            direction=req.direction,
            addr=req.addr,
            gain=req.gain,
            avg=req.avg,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-continuous")
def api_control_run_continuous(
    req: ControlCycleRequest, 
    pump: StepperPump = Depends(lambda r=Depends(): get_valid_pump(r.pump))
):
    # This blocks the process; generally not recommended for a direct API endpoint
    # without running in a background task, but keeping for legacy compatibility.
    controller.run_continuous(
        pump_name=pump.name,
        target_threshold=req.target_threshold,
        vote_k=req.vote_k,
        hz=req.hz,
        irrigate_seconds=req.irrigate_seconds,
        direction=req.direction,
        addr=req.addr,
        gain=req.gain,
        avg=req.avg,
        # Defaulting loop interval to settings for simplicity
    )
    return {"status": "stopped"}
