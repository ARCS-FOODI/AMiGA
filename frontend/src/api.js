// Centralized API fetching logic
const API_BASE = `http://${window.location.hostname}:8000`;

const handleResponse = async (res) => {
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `API Error: ${res.status}`);
    }
    return res.json();
};

export const fetchConfig = () => fetch(`${API_BASE}/config`).then(handleResponse);

export const getLightState = () => fetch(`${API_BASE}/light`).then(handleResponse);
export const toggleLight = () => fetch(`${API_BASE}/light/toggle`, { method: "POST" }).then(handleResponse);
export const getLightConfig = () => fetch(`${API_BASE}/light/config`).then(handleResponse);
export const setLightConfig = (data) =>
    fetch(`${API_BASE}/light/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    }).then(handleResponse);

export const runPumpSeconds = (pump, seconds, hz = 1000, direction = "forward") =>
    fetch(`${API_BASE}/pump/run-seconds`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pump, seconds, hz, direction })
    }).then(handleResponse);

export const runPumpMl = (pump, ml, hz = 1000, direction = "forward") =>
    fetch(`${API_BASE}/pump/run-ml`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pump, ml, hz, direction })
    }).then(handleResponse);

export const getCalibration = () => fetch(`${API_BASE}/pump/calibration`).then(handleResponse);
export const calibratePump = (pump, ml_per_sec) =>
    fetch(`${API_BASE}/pump/calibration`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pump, ml_per_sec })
    }).then(handleResponse);

export const stopAllPumps = () => fetch(`${API_BASE}/pump/stop-all`, { method: "POST" }).then(handleResponse);
export const unlockAllPumps = () => fetch(`${API_BASE}/pump/unlock-all`, { method: "POST" }).then(handleResponse);
export const getPumpsStatus = () => fetch(`${API_BASE}/pump/status`).then(handleResponse);

export const snapshotSensors = (options = {}) => {
    const { samples = 1, avg = 5, addr = 0x48, do_pin = 6 } = options;
    return fetch(`${API_BASE}/sensors/read`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ samples, avg, addr, do_pin })
    }).then(handleResponse);
};

export const snapshotSIS = (options = {}) => {
    const { port = null, slave_id = null } = options;
    return fetch(`${API_BASE}/sis/read`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ port, slave_id })
    }).then(handleResponse);
};

export const snapshotSCD41 = () => fetch(`${API_BASE}/scd41/read`).then(handleResponse);

export const snapshotTSL2561 = () => fetch(`${API_BASE}/tsl2561/read`).then(handleResponse);

export const runControlCycle = (data) =>
    fetch(`${API_BASE}/control/cycle-once`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    }).then(handleResponse);

export const getScaleWeight = () => fetch(`${API_BASE}/scale/read`).then(handleResponse);
export const getScaleBundles = () => fetch(`${API_BASE}/scale/bundles`).then(handleResponse);
export const tareScale = () => fetch(`${API_BASE}/scale/tare`, { method: "POST" }).then(handleResponse);

export const getRecordingStatus = () => fetch(`${API_BASE}/recording/status`).then(handleResponse);
export const startRecording = (frequencies) => 
    fetch(`${API_BASE}/recording/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ frequencies })
    }).then(handleResponse);
export const stopRecording = () => fetch(`${API_BASE}/recording/stop`, { method: "POST" }).then(handleResponse);
