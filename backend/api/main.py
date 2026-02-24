from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import pumps, sensors, light, control
from .. import pumps as hs_pumps
from .. import sensors as hs_sensors
from .. import light as hs_light
from .. import grow_scheduler
from .. import config_store
from ..settings import PUMP_PINS, DEFAULT_ADDR, DEFAULT_GAIN, DEFAULT_AVG, DEFAULT_THRESH, DEFAULT_HZ, DEFAULT_DIR, DEFAULT_VOTE_K, DEFAULT_IRR_SEC

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Start background scheduler and init global managers when the API starts 
    and stop them on shutdown.
    """
    hs_pumps.manager.startup()
    hs_light.manager.startup()
    hs_sensors.manager.startup(use_digital=True)
    grow_scheduler.start()
    
    try:
        yield
    finally:
        grow_scheduler.stop()
        hs_pumps.manager.shutdown()
        hs_light.manager.shutdown()
        hs_sensors.manager.shutdown()


app = FastAPI(title="AMiGA API", lifespan=lifespan)

# CORS for React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all Modular Routers
app.include_router(pumps.router)
app.include_router(sensors.router)
app.include_router(light.router)
app.include_router(control.router)


@app.get("/config", tags=["system"])
def get_config():
    """Global system configuration."""
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
