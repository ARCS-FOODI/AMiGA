from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

<<<<<<< HEAD
from .routers import pumps, sensors, light, control, scale
from .. import pumps as hs_pumps
from .. import sensors as hs_sensors
from .. import light as hs_light
=======
from .routers import pumps, sensors, light, control, npk_sensors
from .. import pumps as hs_pumps
from .. import sensors as hs_sensors
from .. import light as hs_light
from .. import npk_sensor
>>>>>>> 200cc1a (feat: implement 7-in-1 NPK soil sensor UI with boxed layout and equal-sized components)
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
<<<<<<< HEAD
=======
    
    # Initialize NPK sensor with default settings
    try:
        from ..settings import NPK_PORT, NPK_SLAVE_ID, NPK_BAUDRATE, NPK_TIMEOUT
        npk_sensor.manager.initialize(
            port=NPK_PORT,
            slave_id=NPK_SLAVE_ID,
            baudrate=NPK_BAUDRATE,
            timeout=NPK_TIMEOUT
        )
    except Exception as e:
        print(f"Warning: Could not initialize NPK sensor: {e}")
    
>>>>>>> 200cc1a (feat: implement 7-in-1 NPK soil sensor UI with boxed layout and equal-sized components)
    grow_scheduler.start()
    
    print("\n" + "="*50)
    print("  AMiGA API backend is running.")
    print("  Interactive API Docs: http://localhost:8000/docs#/")
    print("="*50 + "\n")
    
    try:
        yield
    finally:
        grow_scheduler.stop()
        hs_pumps.manager.shutdown()
        hs_light.manager.shutdown()
        hs_sensors.manager.shutdown()
<<<<<<< HEAD
=======
        npk_sensor.manager.shutdown()
>>>>>>> 200cc1a (feat: implement 7-in-1 NPK soil sensor UI with boxed layout and equal-sized components)


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
<<<<<<< HEAD
app.include_router(light.router)
app.include_router(control.router)
app.include_router(scale.router)
=======
app.include_router(npk_sensors.router)
app.include_router(light.router)
app.include_router(control.router)
>>>>>>> 200cc1a (feat: implement 7-in-1 NPK soil sensor UI with boxed layout and equal-sized components)


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
