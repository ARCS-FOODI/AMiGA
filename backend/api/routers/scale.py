from fastapi import APIRouter
from ...scale import manager as scale_manager

router = APIRouter(prefix="/scale", tags=["scale"])

@router.get("/weight")
def get_weight():
    """
    Returns the latest continuously polled weight from the U.S. Solid scale.
    """
    return scale_manager.scale.get_latest()
