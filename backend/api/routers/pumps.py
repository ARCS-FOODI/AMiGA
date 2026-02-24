from fastapi import APIRouter, HTTPException, Depends
from typing import List

from ..models import (
    PumpSecondsRequest,
    PumpMultiSecondsRequest,
    PumpCalibrateRequest,
    PumpMlRequest,
    PumpCalibrationUpdate,
)
from ...pumps import manager as pump_manager, StepperPump
from ...settings import PUMP_PINS
from ... import config_store

router = APIRouter(prefix="/pump", tags=["pumps"])

# Helper function for dependency injection
def get_pump_from_request(req_obj) -> StepperPump:
    # req_obj is expected to be one of the Pydantic request models that has a 'pump' field
    pump_name = req_obj.pump
    if pump_name not in PUMP_PINS:
        raise HTTPException(status_code=400, detail=f"Unknown pump '{pump_name}'")
    try:
        return pump_manager.get_pump(pump_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-seconds")
def api_run_pump_seconds(req: PumpSecondsRequest):
    pump = get_pump_from_request(req)
    try:
        return pump.run_for_seconds(
            seconds=req.seconds,
            hz=req.hz,
            direction=req.direction,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-multi-seconds")
def api_run_pumps_seconds(req: PumpMultiSecondsRequest):
    for p in req.pumps:
        if p not in PUMP_PINS:
            raise HTTPException(status_code=400, detail=f"Unknown pump '{p}'")
    try:
        return pump_manager.run_multi_seconds(
            pump_names=req.pumps,
            seconds=req.seconds,
            hz=req.hz,
            direction=req.direction,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calibrate-seconds")
def api_calibrate_pump(req: PumpCalibrateRequest):
    pump = get_pump_from_request(req)
    try:
        return pump.calibrate(
            run_seconds=req.run_seconds,
            hz=req.hz,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run-ml")
def api_run_pump_ml(req: PumpMlRequest):
    pump = get_pump_from_request(req)
    try:
        return pump.dispense_ml(
            ml=req.ml,
            hz=req.hz,
            direction=req.direction,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calibration")
def api_get_calibration():
    return config_store.load_calibration()

@router.post("/calibration")
def api_set_calibration(req: PumpCalibrationUpdate):
    if req.pump not in PUMP_PINS:
        raise HTTPException(status_code=400, detail=f"Unknown pump '{req.pump}'")
    try:
        return config_store.set_pump_calibration(req.pump, req.ml_per_sec)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
