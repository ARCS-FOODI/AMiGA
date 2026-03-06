from fastapi import APIRouter
from ...scale import manager

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
