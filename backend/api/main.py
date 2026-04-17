from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import pumps, sensors, light, control, scale, sis, scd41, tsl2561
from .. import pumps as hs_pumps
from .. import sensors as hs_sensors
from .. import light as hs_light
from .. import scale as hs_scale
from .. import scd41 as hs_scd41
from .. import tsl2561 as hs_tsl2561
from .. import grow_scheduler
from .. import scale_telemetry
from .. import sis_telemetry
from .. import sensors_telemetry
from .. import scd41_telemetry
from .. import tsl2561_telemetry
from .. import light_telemetry
from .. import pump_telemetry
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
    hs_scale.manager.startup()
    hs_scd41.manager.startup()
    hs_tsl2561.manager.startup()
    grow_scheduler.start()
    
    # Do not auto-start scale and sis telemetry here; let /recording/start handle it.
    # We remove scale_telemetry.start() and sis_telemetry.start() from startup.
    
    print("\n" + "="*50)
    print("  AMiGA API backend is running.")
    print("  Interactive API Docs: http://localhost:8000/docs#/")
    print("="*50 + "\n")
    
    try:
        yield
    finally:
        sis_telemetry.stop()
        scale_telemetry.stop()
        sensors_telemetry.stop()
        scd41_telemetry.stop()
        tsl2561_telemetry.stop()
        light_telemetry.stop()
        pump_telemetry.stop()
        
        grow_scheduler.stop()
        hs_pumps.manager.shutdown()
        hs_light.manager.shutdown()
        hs_sensors.manager.shutdown()
        hs_scale.manager.shutdown()
        hs_scd41.manager.shutdown()
        hs_tsl2561.manager.shutdown()


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
app.include_router(scale.router)
app.include_router(sis.router)
app.include_router(scd41.router)
app.include_router(tsl2561.router)

from .routers import recording, recipe
app.include_router(recording.router)
app.include_router(recipe.router)


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


@app.get("/health", tags=["system"])
def get_health():
    """
    Per-device health check — inspects in-memory manager state only, no hardware I/O.
    Returns status per module: 'ok' | 'simulated' | 'error'
    """
    from ..settings import SIMULATE_GPIO, SIMULATE_SCALE

    devices = {}

    # ── Pumps (GPIO stepper drivers) ──────────────────────────────────────────
    try:
        if SIMULATE_GPIO:
            devices["pumps"] = {"status": "simulated"}
        elif hs_pumps.manager._handle is not None:
            devices["pumps"] = {"status": "ok"}
        else:
            devices["pumps"] = {"status": "error", "error": "GPIO handle not opened"}
    except Exception as e:
        devices["pumps"] = {"status": "error", "error": str(e)}

    # ── Soil moisture sensors / ADC ───────────────────────────────────────────
    try:
        if SIMULATE_GPIO:
            devices["sensors"] = {"status": "simulated"}
        elif hs_sensors.manager._handle is not None:
            devices["sensors"] = {"status": "ok"}
        else:
            devices["sensors"] = {"status": "error", "error": "GPIO chip not opened"}
    except Exception as e:
        devices["sensors"] = {"status": "error", "error": str(e)}

    # ── Grow light ────────────────────────────────────────────────────────────
    try:
        lm = hs_light.manager
        if SIMULATE_GPIO:
            devices["light"] = {"status": "simulated"}
        elif getattr(lm, "_handle", None) is not None or getattr(lm.main_light, "_handle", None) is not None:
            devices["light"] = {"status": "ok"}
        else:
            devices["light"] = {"status": "error", "error": "Light GPIO handle not opened"}
    except Exception as e:
        devices["light"] = {"status": "error", "error": str(e)}

    # ── Scale ─────────────────────────────────────────────────────────────────
    try:
        if SIMULATE_SCALE:
            devices["scale"] = {"status": "simulated"}
        elif isinstance(hs_scale.manager, hs_scale._HardwareScaleManager):
            if hs_scale.manager._running and hs_scale.manager._ser and hs_scale.manager._ser.is_open:
                devices["scale"] = {"status": "ok"}
            else:
                devices["scale"] = {"status": "error", "error": "Serial port not open or thread stopped"}
        else:
            devices["scale"] = {"status": "ok"}
    except Exception as e:
        devices["scale"] = {"status": "error", "error": str(e)}

    # ── SCD41 (CO2 / Temp / Humidity) ────────────────────────────────────────
    try:
        if SIMULATE_GPIO:
            devices["scd41"] = {"status": "simulated"}
        elif hs_scd41.manager._sensor is not None:
            devices["scd41"] = {"status": "ok"}
        else:
            devices["scd41"] = {"status": "error", "error": "I2C sensor not initialized"}
    except Exception as e:
        devices["scd41"] = {"status": "error", "error": str(e)}

    # ── TSL2561 (Luminosity) ──────────────────────────────────────────────────
    try:
        if SIMULATE_GPIO:
            devices["tsl2561"] = {"status": "simulated"}
        elif hs_tsl2561.manager._sensor is not None:
            devices["tsl2561"] = {"status": "ok"}
        else:
            devices["tsl2561"] = {"status": "error", "error": "I2C sensor not initialized"}
    except Exception as e:
        devices["tsl2561"] = {"status": "error", "error": str(e)}

    # ── SIS (Soil NPK / pH — Modbus) ─────────────────────────────────────────
    # SIS has no persistent manager — each read opens/closes the port.
    # We mark it as simulated when GPIO sim is on, otherwise unknown until a read fails.
    devices["sis"] = {"status": "simulated" if SIMULATE_GPIO else "ok"}

    # ── Overall summary ───────────────────────────────────────────────────────
    error_count     = sum(1 for d in devices.values() if d["status"] == "error")
    simulated_count = sum(1 for d in devices.values() if d["status"] == "simulated")
    total           = len(devices)

    if error_count == total:
        overall = "offline"
    elif error_count > 0:
        overall = "degraded"
    elif simulated_count == total:
        overall = "simulated"
    else:
        overall = "ok"

    return {"overall": overall, "devices": devices}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)

