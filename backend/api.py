# backend/api.py
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .settings import (
    PUMP_PINS,
    DEFAULT_ADDR,
    DEFAULT_GAIN,
    DEFAULT_AVG,
    DEFAULT_INTSEC,
    DEFAULT_DRY_V,
    DEFAULT_WET_V,
    DEFAULT_THRESH,
    DEFAULT_DO_PIN,
    DEFAULT_HZ,
    DEFAULT_DIR,
    DEFAULT_VOTE_K,
    DEFAULT_IRR_SEC,
    DEFAULT_SAMPLES,
)
from . import sensors, pumps, control, config_store


app = FastAPI(title="AMiGA Irrigation API")

# CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten later if you want
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Pydantic request models ----------

class PumpSecondsRequest(BaseModel):
    pump: str = Field("water")
    seconds: float = Field(..., gt=0)
    hz: float = Field(DEFAULT_HZ, gt=0)
    direction: str = Field(DEFAULT_DIR)


class PumpCalibrateRequest(BaseModel):
    pump: str = Field("water")
    run_seconds: float = Field(..., gt=0)
    hz: float = Field(DEFAULT_HZ, gt=0)


class PumpMlRequest(BaseModel):
    pump: str = Field("water")
    ml: float = Field(..., gt=0)
    hz: float = Field(DEFAULT_HZ, gt=0)
    direction: str = Field(DEFAULT_DIR)


class PumpCalibrationUpdate(BaseModel):
    pump: str = Field("water")
    ml_per_sec: float = Field(..., gt=0)


class SensorsRequest(BaseModel):
    addr: int = DEFAULT_ADDR
    gain: int = DEFAULT_GAIN
    samples: int = Field(1, ge=1, le=DEFAULT_SAMPLES)
    interval: float = Field(DEFAULT_INTSEC, ge=0.0)
    avg: int = Field(DEFAULT_AVG, ge=1)
    dry_v: float = DEFAULT_DRY_V
    wet_v: float = DEFAULT_WET_V
    thresh_pct: float = DEFAULT_THRESH
    use_digital: bool = False
    do_pin: int = DEFAULT_DO_PIN
    invert_do: bool = False


class ControlCycleRequest(BaseModel):
    pump: str = Field("water")
    target_threshold: float = 40.0
    vote_k: int = DEFAULT_VOTE_K
    hz: float = DEFAULT_HZ
    irrigate_seconds: float = DEFAULT_IRR_SEC
    direction: str = DEFAULT_DIR
    addr: int = DEFAULT_ADDR
    gain: int = DEFAULT_GAIN
    avg: int = DEFAULT_AVG
    dry_v: float = DEFAULT_DRY_V
    wet_v: float = DEFAULT_WET_V


# ---------- Info endpoints ----------

@app.get("/config")
def get_config():
    return {
        "pumps": list(PUMP_PINS.keys()),
        "defaults": {
            "addr": DEFAULT_ADDR,
            "gain": DEFAULT_GAIN,
            "avg": DEFAULT_AVG,
            "dry_v": DEFAULT_DRY_V,
            "wet_v": DEFAULT_WET_V,
            "thresh_pct": DEFAULT_THRESH,
            "hz": DEFAULT_HZ,
            "dir": DEFAULT_DIR,
            "vote_k": DEFAULT_VOTE_K,
            "irrigate_seconds": DEFAULT_IRR_SEC,
        },
        "calibration": config_store.load_calibration(),
    }


# ---------- Pump endpoints ----------

@app.post("/pump/run-seconds")
def api_run_pump_seconds(req: PumpSecondsRequest):
    if req.pump not in PUMP_PINS:
        raise HTTPException(status_code=400, detail=f"Unknown pump '{req.pump}'")
    try:
        return pumps.run_pump_seconds(
            pump=req.pump,
            seconds=req.seconds,
            hz=req.hz,
            direction=req.direction,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pump/calibrate-seconds")
def api_calibrate_pump(req: PumpCalibrateRequest):
    if req.pump not in PUMP_PINS:
        raise HTTPException(status_code=400, detail=f"Unknown pump '{req.pump}'")
    try:
        return pumps.calibrate_pump_seconds(
            pump=req.pump,
            run_seconds=req.run_seconds,
            hz=req.hz,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pump/run-ml")
def api_run_pump_ml(req: PumpMlRequest):
    if req.pump not in PUMP_PINS:
        raise HTTPException(status_code=400, detail=f"Unknown pump '{req.pump}'")
    try:
        return pumps.run_pump_ml(
            pump=req.pump,
            ml=req.ml,
            hz=req.hz,
            direction=req.direction,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pump/calibration")
def api_get_calibration():
    return config_store.load_calibration()


@app.post("/pump/calibration")
def api_set_calibration(req: PumpCalibrationUpdate):
    if req.pump not in PUMP_PINS:
        raise HTTPException(status_code=400, detail=f"Unknown pump '{req.pump}'")
    try:
        return config_store.set_pump_calibration(req.pump, req.ml_per_sec)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Sensors endpoint ----------

@app.post("/sensors/read")
def api_sensors(req: SensorsRequest):
    try:
        return sensors.snapshot_sensors(
            addr=req.addr,
            gain=req.gain,
            samples=req.samples,
            interval=req.interval,
            avg=req.avg,
            dry_v=req.dry_v,
            wet_v=req.wet_v,
            thresh_pct=req.thresh_pct,
            use_digital=req.use_digital,
            do_pin=req.do_pin,
            invert_do=req.invert_do,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Control cycle endpoint ----------

@app.post("/control/cycle-once")
def api_control_cycle(req: ControlCycleRequest):
    if req.pump not in PUMP_PINS:
        raise HTTPException(status_code=400, detail=f"Unknown pump '{req.pump}'")
    try:
        return control.control_cycle_once(
            pump=req.pump,
            target_threshold=req.target_threshold,
            vote_k=req.vote_k,
            hz=req.hz,
            irrigate_seconds=req.irrigate_seconds,
            direction=req.direction,
            addr=req.addr,
            gain=req.gain,
            avg=req.avg,
            dry_v=req.dry_v,
            wet_v=req.wet_v,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Uvicorn entrypoint (optional)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api:app", host="0.0.0.0", port=8000, reload=True)
