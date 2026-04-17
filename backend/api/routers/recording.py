from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
import os

from ... import scale_telemetry
from ... import sis_telemetry
from ... import sensors_telemetry
from ... import scd41_telemetry
from ... import tsl2561_telemetry
from ... import light_telemetry
from ... import pump_telemetry

router = APIRouter(
    prefix="/recording",
    tags=["recording"],
)

# Global tracking variable
_active_session_dir: Optional[str] = None
_is_recording: bool = False

class RecordingConfigRequest(BaseModel):
    recipeName: Optional[str] = None
    frequencies: Dict[str, float] = {
        "scale": 5.0,
        "sis": 5.0,
        "sensors": 10.0,
        "co2": 10.0,
        "light": 10.0,
        "light_status": 10.0,
        "pump_status": 5.0
    }

def _get_base_path() -> Path:
    # Resolve the intended unified data directory regardless of cwd
    return Path(__file__).resolve().parents[3] / "data" / "records"

@router.post("/start")
def start_recording(config: RecordingConfigRequest):
    global _active_session_dir, _is_recording
    
    if _is_recording:
        return {"status": "already_recording", "session_dir": _active_session_dir}
        
    try:
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        prefix = config.recipeName.replace(" ", "_") if config.recipeName else "manual"
        session_folder = f"session_{prefix}_{now_str}"
        session_path = _get_base_path() / session_folder
        session_path.mkdir(parents=True, exist_ok=True)
        
        _active_session_dir = str(session_path)
        
        # Pull frequencies, applying defaults if missing
        f = config.frequencies
        scale_telemetry.start(_active_session_dir, f.get("scale", 5.0))
        sis_telemetry.start(_active_session_dir, f.get("sis", 5.0))
        sensors_telemetry.start(_active_session_dir, f.get("sensors", 10.0))
        scd41_telemetry.start(_active_session_dir, f.get("co2", 10.0))
        tsl2561_telemetry.start(_active_session_dir, f.get("light", 10.0))
        light_telemetry.start(_active_session_dir, f.get("light_status", 10.0))
        pump_telemetry.start(_active_session_dir, f.get("pump_status", 5.0))
        
        _is_recording = True
        return {"status": "recording_started", "session_dir": _active_session_dir}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start recording: {e}")

@router.post("/stop")
def stop_recording():
    global _is_recording, _active_session_dir
    
    if not _is_recording:
        return {"status": "not_recording"}
        
    try:
        scale_telemetry.stop()
        sis_telemetry.stop()
        sensors_telemetry.stop()
        scd41_telemetry.stop()
        tsl2561_telemetry.stop()
        light_telemetry.stop()
        pump_telemetry.stop()
        
        last_session = _active_session_dir
        _is_recording = False
        _active_session_dir = None
        
        return {"status": "recording_stopped", "session_dir": last_session}
        
    except Exception as e:
        # Emergency reset
        _is_recording = False
        raise HTTPException(status_code=500, detail=f"Failed to cleanly stop recording: {e}")

@router.get("/status")
def get_recording_status():
    return {
        "is_recording": _is_recording,
        "session_dir": _active_session_dir
    }

@router.get("/active/list")
def list_active_files():
    """Lists all CSV files in the currently active recording session."""
    if not _is_recording or not _active_session_dir:
        raise HTTPException(status_code=400, detail="No active recording session.")
    
    session_path = Path(_active_session_dir)
    if not session_path.exists():
        raise HTTPException(status_code=404, detail="Active session directory not found on disk.")
    
    files = [f.name for f in session_path.glob("*.csv")]
    return {
        "status": "active",
        "session": session_path.name,
        "files": files
    }

@router.get("/active/download/{filename}")
def download_active_file(filename: str):
    """Streams a specific CSV file from the active recording session."""
    if not _is_recording or not _active_session_dir:
        raise HTTPException(status_code=400, detail="No active recording session.")
    
    # Security: only allow CSV files
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Access denied: Only .csv files are exposed.")
    
    # Path traversal protection: Path() handles the basename well
    file_path = Path(_active_session_dir) / os.path.basename(filename)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found in active session.")
    
    return FileResponse(
        path=file_path,
        media_type='text/csv',
        filename=filename
    )
