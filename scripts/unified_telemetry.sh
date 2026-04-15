#!/bin/bash
# AMiGA Unified Telemetry Logger
# Safely aggregates data from all hardware nodes using the local FastAPI REST layer to avoid low-level resource collisions.

set -euo pipefail

# Configuration (Obscured into System Variables)
API_BASE="${AMIGA_API_BASE:-http://localhost:8000}"
RUNTIME_DATA_DIR="${AMIGA_RUNTIME_DIR:-$HOME/.amiga_runtime_data}"
CSV_FILE="$RUNTIME_DATA_DIR/unified_telemetry.csv"

# Timeouts and intervals safely pull from system environment or default locally
POLL_INTERVAL_SEC=${AMIGA_POLL_INTERVAL:-2.5}
SYNC_INTERVAL_SEC=${AMIGA_SYNC_INTERVAL:-10800}

# Dependency validation
if ! command -v jq &> /dev/null; then
    echo "[!] Fatal error: 'jq' is not installed. Please install jq to run this script."
    exit 1
fi
if ! command -v curl &> /dev/null; then
    echo "[!] Fatal error: 'curl' is not installed. Please install curl to run this script."
    exit 1
fi

mkdir -p "$RUNTIME_DATA_DIR"

echo "[i] Starting Unified Telemetry Logger. Writing to: $CSV_FILE"
echo "[i] Periodic rotation & network SFTP transfer every ${SYNC_INTERVAL_SEC} seconds."
echo "[i] Press CTRL+C to stop."

# Graceful exit handling
trap 'echo "\n[i] Telemetry script terminated cleanly."; exit 0' SIGINT SIGTERM

LAST_SYNC_TIME=$(date +%s)

while true; do
    # 0. Header Validation (Dynamic atomic lock handler)
    if [ ! -f "$CSV_FILE" ]; then
        echo "TIMESTAMP,SCALE_WEIGHT,SCD41_CO2,SCD41_TEMP,SCD41_RH,TSL2561_LUX,SIS_N,SIS_P,SIS_K,SIS_MOISTURE,SIS_TEMP,SIS_EC,SIS_PH,MAIN_LIGHT_STATUS,ADC_MOISTURE_PROBE" > "$CSV_FILE"
        chmod 644 "$CSV_FILE"
        echo "[i] Constructed base CSV file structure."
    fi

    # 1. System ISO 8601 Timestamp
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # 2. Scale (GET)
    SCALE_RES=$(curl -s -m 2.0 "${API_BASE}/scale/read" || echo "")
    SCALE_WEIGHT=$(echo "${SCALE_RES}" | jq -r '.weight // "N/A"' 2>/dev/null || echo "N/A")

    # 3. SCD41 Atmospheric (GET)
    SCD41_RES=$(curl -s -m 2.0 "${API_BASE}/scd41/read" || echo "")
    SCD41_CO2=$(echo "${SCD41_RES}" | jq -r '.co2 // "N/A"' 2>/dev/null || echo "N/A")
    SCD41_TEMP=$(echo "${SCD41_RES}" | jq -r '.temp // "N/A"' 2>/dev/null || echo "N/A")
    SCD41_RH=$(echo "${SCD41_RES}" | jq -r '.rh // "N/A"' 2>/dev/null || echo "N/A")

    # 4. TSL2561 Lux (GET)
    TSL_RES=$(curl -s -m 2.0 "${API_BASE}/tsl2561/read" || echo "")
    TSL_LUX=$(echo "${TSL_RES}" | jq -r '.lux // "N/A"' 2>/dev/null || echo "N/A")

    # 5. SIS 7-in-1 Soil Sensor (POST)
    SIS_RES=$(curl -s -X POST -m 3.0 "${API_BASE}/sis/read" -H "Content-Type: application/json" -d "{}" || echo "")
    SIS_N=$(echo "${SIS_RES}" | jq -r '.nitrogen // "N/A"' 2>/dev/null || echo "N/A")
    SIS_P=$(echo "${SIS_RES}" | jq -r '.phosphorus // "N/A"' 2>/dev/null || echo "N/A")
    SIS_K=$(echo "${SIS_RES}" | jq -r '.potassium // "N/A"' 2>/dev/null || echo "N/A")
    SIS_MOISTURE=$(echo "${SIS_RES}" | jq -r '.moisture // "N/A"' 2>/dev/null || echo "N/A")
    SIS_TEMP=$(echo "${SIS_RES}" | jq -r '.temp // "N/A"' 2>/dev/null || echo "N/A")
    SIS_EC=$(echo "${SIS_RES}" | jq -r '.ec // "N/A"' 2>/dev/null || echo "N/A")
    SIS_PH=$(echo "${SIS_RES}" | jq -r '.ph // "N/A"' 2>/dev/null || echo "N/A")

    # 6. Light State (GET)
    LIGHT_RES=$(curl -s -m 2.0 "${API_BASE}/light" || echo "")
    LIGHT_STATE=$(echo "${LIGHT_RES}" | jq -r '.state // "N/A"' 2>/dev/null || echo "N/A")

    # 7. ADC Core Sensors (POST) - e.g. generic moisture probe array
    ADC_RES=$(curl -s -X POST -m 2.0 "${API_BASE}/sensors/read" -H "Content-Type: application/json" -d "{}" || echo "")
    # Note: Extracting the first node's data array as an example target. 
    ADC_MOISTURE=$(echo "${ADC_RES}" | jq -r '.moisture[0] // "N/A"' 2>/dev/null || echo "N/A")

    # Build and append the unified dynamic CSV row
    ROW="${TIMESTAMP},${SCALE_WEIGHT},${SCD41_CO2},${SCD41_TEMP},${SCD41_RH},${TSL_LUX},${SIS_N},${SIS_P},${SIS_K},${SIS_MOISTURE},${SIS_TEMP},${SIS_EC},${SIS_PH},${LIGHT_STATE},${ADC_MOISTURE}"
    echo "$ROW" >> "$CSV_FILE"

    # --- ATOMIC ROTATION & SFTP NETWORK DISPATCH LOGIC ---
    CURRENT_TIME=$(date +%s)
    ELAPSED=$(( CURRENT_TIME - LAST_SYNC_TIME ))
    if [ "$ELAPSED" -ge "$SYNC_INTERVAL_SEC" ]; then
        echo "[i] 3-Hour cycle elapsed. Structurally rotating logfile..."
        UPLOAD_FILE="${CSV_FILE%.*}_${CURRENT_TIME}.csv.upload"
        
        # Atomically isolate the file. Next top-of-loop cycle natively re-generates baseline CSV headers instantly.
        mv "$CSV_FILE" "$UPLOAD_FILE"
        LAST_SYNC_TIME=$CURRENT_TIME
        
        # Fire-and-forget SFTP network push on decoupled background thread. (Does not block telemetry tracking).
        "$(dirname "$0")/send_sftp.sh" "$UPLOAD_FILE" &
    fi

    # Sleep loop (adjust config variable above to increase/decrease frequency)
    sleep "$POLL_INTERVAL_SEC"
done
