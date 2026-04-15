#!/bin/bash
# AMiGA Network TimescaleDB Ingestion Script
# Designed for autonomous deployment directly on the NVIDIA Jetson Orin

set -euo pipefail

# Secure Configuration Wrapper
# Fails instantly and natively if environment variables are left completely unassigned.
# Example: export PGHOST="localhost"
DB_HOST="${PGHOST:?PGHOST environment variable must be set securely via Bash}"
DB_PORT="${PGPORT:-5432}"
DB_NAME="${PGDATABASE:?PGDATABASE environment variable must be set}"
DB_USER="${PGUSER:?PGUSER environment variable must be set}"
DB_TABLE="${PGTABLE:?PGTABLE environment variable must be set (Your DBeaver Table Target)}"

# The source directory matching where your SFTP script drops the raw .upload data stream
INGEST_DIR="${AMIGA_INGEST_DIR:-$HOME/amiga_telemetry}"
ARCHIVE_DIR="$INGEST_DIR/archived"

# Ensure structurally necessary tracking directories exist safely
mkdir -p "$INGEST_DIR"
mkdir -p "$ARCHIVE_DIR"

echo "[i] Launching Universal AMiGA Database Intake..."
echo "[i] Scanning $INGEST_DIR for incoming bulk matrix files."

shopt -s nullglob
# Targets .upload extension specifically utilized by the AMiGA network wrapper
for FILE in "$INGEST_DIR"/*.csv.upload; do
    echo "[i] Detected incoming payload vector: $(basename "$FILE")"
    
    # Advanced Bulk CSV ingestion utilizing internal PostgreSQL wrapper mechanisms.
    # Seamlessly translates 'N/A' strings implicitly mapped during system crashes back into native NULL parameters.
    # Targets the exact table you already configured via DBeaver!
    if psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -c "\copy \"$DB_TABLE\" FROM '$FILE' WITH (FORMAT csv, HEADER true, NULL 'N/A');"; then
        echo "[+] Processing Success! Matrix logged structurally into hyperbase."
        
        # Protects identical data drops from duplicating mathematically by archiving correctly mapped files instantly out of stream.
        mv "$FILE" "$ARCHIVE_DIR/"
    else
        echo "[!] Processing Failed for $(basename "$FILE")."
        echo "[i] Halting destructive actions. File maintained in spool structure for later re-acquisition."
    fi
done

echo "[i] Ingestion Cycle Complete."
