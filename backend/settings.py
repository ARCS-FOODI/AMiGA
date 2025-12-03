from typing import Dict

# Pump pin maps (BCM numbering)
PUMP_PINS: Dict[str, Dict[str, int]] = {
    "water": {      # pump for plain water
        "STEP": 5,  # was 17 in the single-pump setup
        "DIR": 6,   # was 27
        "EN": 13,   # was 22 (EN active LOW)
    },
    "food": {  # pump for food solution
        "STEP": 17,
        "DIR": 27,
        "EN": 22,
    },
}

# GPIO chip index
CHIP = 0  # usually /dev/gpiochip0

# Sensor defaults
DEFAULT_ADDR   = 0x48
DEFAULT_GAIN   = 1          # ±4.096 V
DEFAULT_AVG    = 5
DEFAULT_INTSEC = 1.0
DEFAULT_SAMPLES= 30
DEFAULT_DRY_V  = 3.30
DEFAULT_WET_V  = 0.00
# Now interpreted as a **voltage** threshold in volts
DEFAULT_THRESH = 1.50       # V threshold for irrigation logic
DEFAULT_DO_PIN = 6          # optional digital wet/dry

# Motor defaults
DEFAULT_HZ     = 30000
DEFAULT_DIR    = "forward"

# Full scenario defaults
DEFAULT_VOTE_K      = 2     # need at least K of 4 over threshold
DEFAULT_COOLDOWN_S  = 10.0  # wait after an irrigation cycle
DEFAULT_IRR_SEC     = 5.0   # seconds to run pump when triggered
