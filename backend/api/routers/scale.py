from fastapi import APIRouter
from ...scale import manager
from ... import scale_telemetry

router = APIRouter(
    prefix="/scale",
    tags=["scale"],
)

@router.get("/read")
def read_scale():
    """
    Returns the current measured weight in grams.
    Factors in both added liquid (dispensed by pumps) and simulated plant growth.
    """
    return {
        "weight": manager.get_weight(),
        "status": "ok"
    }

@router.get("/bundles")
def get_bundles():
    """
    Returns the history of scale data bundles (average weight per bundle).
    """
    return {
        "history": scale_telemetry.get_recent_averages(),
        "status": "ok"
    }

@router.post("/tare")
def tare_scale():
    """
    Zeroes the scale. Subsequent reads will be relative to the current weight.
    """
    new_weight = manager.tare()
    return {
        "weight": new_weight,
        "status": "tared"
    }
