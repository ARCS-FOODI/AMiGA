// Centralized API fetching logic
const API_BASE = "http://localhost:8000";

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

export const runPumpSeconds = (pump, seconds, hz = 10000, direction = "forward") =>
    fetch(`${API_BASE}/pump/run-seconds`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pump, seconds, hz, direction })
    }).then(handleResponse);

export const runPumpMl = (pump, ml, hz = 10000, direction = "forward") =>
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

export const snapshotSensors = (samples = 1, avg = 5) =>
    fetch(`${API_BASE}/sensors/read`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ samples, avg })
    }).then(handleResponse);

export const runControlCycle = (data) =>
    fetch(`${API_BASE}/control/cycle-once`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    }).then(handleResponse);
