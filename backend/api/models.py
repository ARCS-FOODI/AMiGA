from pydantic import BaseModel, Field
from typing import List, Literal

from ..settings import (
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
)

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
    gain: float = DEFAULT_GAIN
    samples: int = Field(1, ge=1, le=DEFAULT_SAMPLES)
    interval: float = Field(DEFAULT_INTSEC, ge=0.0)
    avg: int = Field(DEFAULT_AVG, ge=1)
    use_digital: bool = False
    do_pin: int = DEFAULT_DO_PIN
    invert_do: bool = False

class ControlCycleRequest(BaseModel):
    pump: str = Field("water")
    target_threshold: float = DEFAULT_THRESH
    vote_k: int = DEFAULT_VOTE_K
    hz: float = Field(DEFAULT_HZ)
    irrigate_seconds: float = Field(DEFAULT_IRR_SEC)
    direction: str = Field(DEFAULT_DIR)
    addr: int = DEFAULT_ADDR
    gain: float = DEFAULT_GAIN
    avg: int = DEFAULT_AVG

class LightStateRequest(BaseModel):
    on: bool

class LightTimedRequest(BaseModel):
    seconds: float = Field(..., gt=0)

class LightConfig(BaseModel):
    mode: Literal["manual", "daynight"] = "manual"
    day_start: str = "19:00"
    day_end: str = "07:00"
