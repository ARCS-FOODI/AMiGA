#!/bin/bash
# AMiGA Background SFTP/SCP Worker
# Securely transfers archived telemetry to the designated Jetson Orin.

set -euo pipefail

# Network Targets (Obscured via System Environment Variables)
# These must be set securely via ~/.bashrc or export wrappers.
ORIN_USER="${AMIGA_ORIN_USER:?AMIGA_ORIN_USER variable must be set.}"
ORIN_IP="${AMIGA_ORIN_IP:?AMIGA_ORIN_IP variable must be set.}"

# Note: The target directory relies on environment logic, defaulting to user's home namespace.
ORIN_DIR="${AMIGA_ORIN_DIR:-~/}" 

# Validation
if [ -z "${1:-}" ]; then
    echo "[!] Usage: $0 <path_to_csv_upload>"
    exit 1
fi

UPLOAD_FILE="$1"

if [ ! -f "$UPLOAD_FILE" ]; then
    echo "[SFTP-WORKER] Error: File not found: $UPLOAD_FILE"
    exit 1
fi

echo "[SFTP-WORKER] Attempting network transfer of $(basename "$UPLOAD_FILE") to ${ORIN_USER}@${ORIN_IP}..."

# We utilize strictly batch-mode scp (-B) over SSH. 
# If passwordless SSH Authentication is not configured, this will immediately fail rather than hanging indefinitely on a hidden prompt.
if scp -B -p "$UPLOAD_FILE" "${ORIN_USER}@${ORIN_IP}:${ORIN_DIR}"; then
    echo "[SFTP-WORKER] Protocol Success: Transferred securely. Removing local garbage file."
    rm -f "$UPLOAD_FILE"
else
    echo "[SFTP-WORKER] Protocol Failed: Unable to transfer. Ensuring local archive remains intact to avoid data loss."
    # The file is not deleted so it can be handled or backed up later.
    exit 1
fi
