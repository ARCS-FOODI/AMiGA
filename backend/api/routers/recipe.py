from fastapi import APIRouter, HTTPException
import json
from pathlib import Path
from pydantic import BaseModel
from typing import Dict, Any

from ...grow_scheduler import get_recipe, set_recipe, get_grow_status, stop_cycle

router = APIRouter(prefix="/recipe", tags=["recipe"])

@router.get("")
def api_get_recipe():
    return get_recipe()

@router.get("/template")
def api_get_template():
    from ...grow_scheduler import DEFAULT_RECIPE
    return DEFAULT_RECIPE

@router.post("")
def api_save_recipe(recipe: Dict[str, Any]):
    try:
        set_recipe(recipe)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
def api_stop_cycle():
    try:
        stop_cycle()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def api_get_status():
    return get_grow_status()
