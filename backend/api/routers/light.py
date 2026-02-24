from fastapi import APIRouter, HTTPException, BackgroundTasks

from ..models import LightStateRequest, LightTimedRequest, LightConfig
from ...light import manager as light_manager

router = APIRouter(prefix="/light", tags=["light"])

@router.get("")
def api_get_light_state():
    try:
        return light_manager.main_light.get_state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
def api_set_light_state(req: LightStateRequest):
    try:
        return light_manager.main_light.set_state(req.on)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/toggle")
def api_toggle_light():
    try:
        return light_manager.main_light.toggle()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/on-for")
def api_light_on_for(req: LightTimedRequest, background_tasks: BackgroundTasks):
    try:
        light_manager.main_light.set_state(True)
        background_tasks.add_task(light_manager.main_light.set_after_delay, False, req.seconds)
        return {"status": "scheduled", "seconds": req.seconds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config")
def api_get_light_config():
    try:
        return light_manager.main_light.get_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config")
def api_set_light_config(req: LightConfig):
    try:
        return light_manager.main_light.set_config(req.mode, req.day_start, req.day_end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apply-daynight")
def api_apply_light_daynight():
    try:
        return light_manager.main_light.apply_daynight_now()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
