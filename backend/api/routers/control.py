from fastapi import APIRouter, HTTPException, Depends

from ..models import ControlCycleRequest
from ...pumps import StepperPump, manager as pump_manager
from ...settings import PUMP_PINS
from ...control import controller

router = APIRouter(prefix="/control", tags=["control"])

def get_valid_pump(pump_name: str) -> StepperPump:
    if pump_name not in PUMP_PINS:
        raise HTTPException(status_code=400, detail=f"Unknown pump '{pump_name}'")
    try:
        return pump_manager.get_pump(pump_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
