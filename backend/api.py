# backend/api.py
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Literal

from .settings import (
    PUMP_PINS,
    DEFAULT_ADDR,
    DEFAULT_GAIN,
    DEFAULT_AVG,
    DEFAULT_INTSEC,
    DEFAULT_THRESH,
    DEFAULT_DO_PIN,
    DEFAULT_HZ,
    DEFAULT_DIR,
    DEFAULT_VOTE_K,
    DEFAULT_IRR_SEC,
    DEFAULT_SAMPLES,
    DEFAULT_COOLDOWN_S,
)
from . import sensors, pumps, control, config_store, light, grow_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Start background scheduler when the API starts and stop it on shutdown.
    This replaces deprecated @app.on_event("startup").
    """
    grow_scheduler.start()
    try:
        yield
    finally:
        grow_scheduler.stop()


app = FastAPI(title="AMiGA Irrigation API", lifespan=lifespan)

# CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later if you want
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


class PumpMultiSecondsRequest(BaseModel):
    pumps: List[str] = Field(default_factory=lambda: ["water", "food"])
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
    use_digital: bool = False
    do_pin: int = DEFAULT_DO_PIN
    invert_do: bool = False


class ControlCycleRequest(BaseModel):
    pump: str = Field("water")
    # Interpreted as a voltage threshold (V)
    target_threshold: float = DEFAULT_THRESH
    vote_k: int = DEFAULT_VOTE_K
    hz: float = Field(DEFAULT_HZ)
    irrigate_seconds: float = Field(DEFAULT_IRR_SEC)
    direction: str = Field(DEFAULT_DIR)
    addr: int = DEFAULT_ADDR
    gain: int = DEFAULT_GAIN
    avg: int = DEFAULT_AVG


class LightStateRequest(BaseModel):
    on: bool


class LightTimedRequest(BaseModel):
    seconds: float = Field(..., gt=0)


class LightConfig(BaseModel):
    mode: Literal["manual", "daynight"] = "manual"
    # "HH:MM" or "HH:MM:SS"
    day_start: str = "19:00"
    day_end: str = "07:00"


# ---------- Info endpoints ----------


@app.get("/config")
def get_config():
    return {
        "pumps": list(PUMP_PINS.keys()),
        "defaults": {
            "addr": DEFAULT_ADDR,
            "gain": DEFAULT_GAIN,
            "avg": DEFAULT_AVG,
            "thresh_v": DEFAULT_THRESH,
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


@app.post("/pump/run-multi-seconds")
def api_run_pumps_seconds(req: PumpMultiSecondsRequest):
    for p in req.pumps:
        if p not in PUMP_PINS:
            raise HTTPException(status_code=400, detail=f"Unknown pump '{p}'")
    try:
        return pumps.run_pumps_seconds(
            pumps_list=req.pumps,
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
            use_digital=req.use_digital,
            do_pin=req.do_pin,
            invert_do=req.invert_do,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Control cycle endpoints ----------


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
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/control/run-continuous")
def api_control_run_continuous(req: ControlCycleRequest):
    if req.pump not in PUMP_PINS:
        raise HTTPException(status_code=400, detail=f"Unknown pump '{req.pump}'")

    control.control_cycle_continuous(
        pump=req.pump,
        target_threshold=req.target_threshold,
        vote_k=req.vote_k,
        hz=req.hz,
        irrigate_seconds=req.irrigate_seconds,
        direction=req.direction,
        addr=req.addr,
        gain=req.gain,
        avg=req.avg,
        loop_interval=DEFAULT_COOLDOWN_S,
    )

    return {"status": "stopped"}


# ---------- Light endpoints ----------


@app.get("/light")
def api_get_light_state():
    try:
        return light.get_light_state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/light")
def api_set_light_state(req: LightStateRequest):
    try:
        return light.set_light(req.on)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/light/toggle")
def api_toggle_light():
    try:
        return light.toggle_light()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/light/on-for")
def api_light_on_for(req: LightTimedRequest, background_tasks: BackgroundTasks):
    try:
        light.set_light(True)
        background_tasks.add_task(light.set_light_after_delay, False, req.seconds)
        return {"status": "scheduled", "seconds": req.seconds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/light/config")
def api_get_light_config():
    try:
        return light.get_light_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/light/config")
def api_set_light_config(req: LightConfig):
    try:
        return light.set_light_config(req.mode, req.day_start, req.day_end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/light/apply-daynight")
def api_apply_light_daynight():
    try:
        return light.apply_daynight_now()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api:app", host="0.0.0.0", port=8000, reload=True)
