// Centralized API fetching logic
export const API_BASE = `http://${window.location.hostname}:8000`;

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
export const startRecording = (frequencies, recipeName = null) => 
    fetch(`${API_BASE}/recording/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ frequencies, recipeName })
    }).then(handleResponse);
export const stopRecording = () => fetch(`${API_BASE}/recording/stop`, { method: "POST" }).then(handleResponse);

export const getRecipe = () => fetch(`${API_BASE}/recipe`).then(handleResponse);
export const getRecipeTemplate = () => fetch(`${API_BASE}/recipe/template`).then(handleResponse);
export const getRecipeStatus = () => fetch(`${API_BASE}/recipe/status`).then(handleResponse);
export const stopCycle = () => fetch(`${API_BASE}/recipe/stop`, { method: "POST" }).then(handleResponse);
export const saveRecipe = (recipe) => 
    fetch(`${API_BASE}/recipe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(recipe)
    }).then(handleResponse);

export const getHealth = () => fetch(`${API_BASE}/health`).then(handleResponse);

export const fetchTelemetry = (filename) => 
    fetch(`${API_BASE}/recording/active/download/${filename}`)
        .then(async res => {
            if (!res.ok) throw new Error(`Telemetry Error: ${res.status}`);
            return res.text();
        });

export const fetchTelemetryWindow = (filename, hours = 4) => 
    fetch(`${API_BASE}/recording/active/window/${filename}?hours=${hours}&max_points=60`)
        .then(async res => {
            if (!res.ok) throw new Error(`Telemetry Error: ${res.status}`);
            
            const text = await res.text();
            
            // --- PAYLOAD METRICS & DIAGNOSTICS ---
            const bytes = new Blob([text]).size;
            const kbSize = (bytes / 1024).toFixed(2);
            let level = 'info';
            let message = '';
            
            if (bytes > 500 * 1024) { // > 500 KB Warning
                level = 'error';
                message = `🚨 Massive payload detected for ${filename}: ${kbSize} KB. Backend downsampling failed?`;
                console.warn(message);
            } else if (bytes > 50 * 1024) { // > 50 KB Notice
                level = 'warn';
                message = `⚠️ Large payload for ${filename}: ${kbSize} KB. High DOM overhead.`;
                console.warn(message);
            } else {
                level = 'info';
                message = `📦 ${filename} synced: ${kbSize} KB`;
                console.debug(message);
            }
            
            // Dispatch to the UI Diagnostic Console overlay
            try {
                window.dispatchEvent(new CustomEvent('telemetry-metric', {
                    detail: { filename, kbSize, level, message, time: new Date().toLocaleTimeString([], { hour12: false }) }
                }));
            } catch (e) {}
            
            return text;
        });

