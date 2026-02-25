from typing import Dict

# Pump pin maps (BCM numbering)
PUMP_PINS: Dict[str, Dict[str, int]] = {
    "food": {      # pump for food solution
        "STEP": 27,  
        "DIR": 22,   
    },
    "water": {  # pump for water
        "STEP": 16,
        "DIR": 26,
    },
}

# Global Enable Pin (Active LOW) shared by all stepper motor drivers
# E.g. connect both drivers' EN pins to this physical board pin
GLOBAL_PUMP_EN = 12

# GPIO chip index
CHIP = 0  # usually /dev/gpiochip0
LIGHT_PIN = 26
# Sensor defaults
DEFAULT_ADDR   = 0x48
DEFAULT_GAIN   = 1          # ±4.096 V
DEFAULT_AVG    = 5
DEFAULT_INTSEC = 1.0
DEFAULT_SAMPLES= 30
DEFAULT_DRY_V  = 3.28
DEFAULT_WET_V  = 0.00
# Now interpreted as a **voltage** threshold in volts
DEFAULT_THRESH = 2.00       # V threshold for irrigation logic
DEFAULT_DO_PIN = 6          # optional digital wet/dry

# Motor defaults
DEFAULT_HZ     = 10000
DEFAULT_DIR    = "forward"

# Full scenario defaults
DEFAULT_VOTE_K      = 2     # need at least K of 4 over threshold
DEFAULT_COOLDOWN_S  = 60.0  # wait after an irrigation cycle
DEFAULT_IRR_SEC     = 5.0   # seconds to run pump when triggered

import os
# Set to True to explicitely mock Raspberry Pi GPIO hardware (For Mac/Windows UI dev)
SIMULATE = True if os.environ.get("AMIGA_SIMULATE", "0") == "1" else False
