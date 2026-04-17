#!/bin/bash

# SFTP Recursive Transfer Script with Mandatory SHA256 Integrity Checking
# Usage: ./sftp_transfer.sh <source_directory> <target_directory>

set -euo pipefail

# Configuration file paths
CONFIG_DIR="${HOME}/.config/sftp_transfer"
CACHE_FILE="${CONFIG_DIR}/transfer_cache.txt"
INTEGRITY_DB="${CONFIG_DIR}/integrity.db"
CONFIG_FILE="${CONFIG_DIR}/sftp_config.conf"
LOG_FILE="${CONFIG_DIR}/transfer.log"
TEMP_DIR="${CONFIG_DIR}/temp"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to log messages
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
    
    case "$level" in
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message" >&2
            ;;
        "WARNING")
            echo -e "${YELLOW}[WARNING]${NC} $message"
            ;;
        "INFO")
            echo -e "${GREEN}[INFO]${NC} $message"
            ;;
        "DEBUG")
            echo -e "${BLUE}[DEBUG]${NC} $message"
            ;;
        "INTEGRITY")
            echo -e "${CYAN}[INTEGRITY]${NC} $message"
            ;;
    esac
}

# Function to create necessary directories and files
initialize() {
    if [[ ! -d "$CONFIG_DIR" ]]; then
        mkdir -p "$CONFIG_DIR"
        chmod 700 "$CONFIG_DIR"
        log_message "INFO" "Created configuration directory: $CONFIG_DIR"
    fi
    
    if [[ ! -d "$TEMP_DIR" ]]; then
        mkdir -p "$TEMP_DIR"
        chmod 700 "$TEMP_DIR"
    fi
    
    if [[ ! -f "$CACHE_FILE" ]]; then
        touch "$CACHE_FILE"
        chmod 600 "$CACHE_FILE"
        log_message "INFO" "Created cache file: $CACHE_FILE"
    fi
    
    if [[ ! -f "$INTEGRITY_DB" ]]; then
        touch "$INTEGRITY_DB"
        chmod 600 "$INTEGRITY_DB"
        log_message "INFO" "Created integrity database: $INTEGRITY_DB"
    fi
    
    if [[ ! -f "$LOG_FILE" ]]; then
        touch "$LOG_FILE"
        chmod 600 "$LOG_FILE"
        log_message "INFO" "Created log file: $LOG_FILE"
    fi
    
    if [[ ! -f "$CONFIG_FILE" ]]; then
        cat > "$CONFIG_FILE" << 'EOF'
# SFTP Transfer Configuration File
# Please fill in the required values below

# Remote SFTP server details
REMOTE_HOST=""
REMOTE_PORT="22"
REMOTE_USER=""

# Authentication method (password or key)
AUTH_METHOD="key"  # Use "password" or "key"

# If using key authentication
SSH_KEY_PATH=""

# If using password authentication (not recommended)
# SFTP_PASSWORD=""  # Uncomment and set if using password auth

# Remote base directory
REMOTE_BASE_DIR=""

# SFTP options
SFTP_OPTIONS="-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10"

# Batch size for SFTP transfers
BATCH_SIZE="50"

# Number of parallel SHA256 processes (adjust based on CPU cores)
PARALLEL_JOBS="4"

# Exclude patterns (space-separated list)
EXCLUDE_PATTERNS=".git .svn *.tmp *.lock *.swp .DS_Store"

# Transfer mode for files (binary or ascii)
TRANSFER_MODE="binary"
EOF
        chmod 600 "$CONFIG_FILE"
        log_message "INFO" "Created configuration file template: $CONFIG_FILE"
        echo -e "${YELLOW}Please edit the configuration file: $CONFIG_FILE${NC}"
        echo -e "${YELLOW}Fill in the remote server details before running this script again.${NC}"
        exit 0
    fi
}

# Function to load and validate configuration
load_config() {
    # Source the configuration file
    source "$CONFIG_FILE"
    
    # Validate required configuration
    local missing_vars=()
    
    [[ -z "${REMOTE_HOST:-}" ]] && missing_vars+=("REMOTE_HOST")
    [[ -z "${REMOTE_USER:-}" ]] && missing_vars+=("REMOTE_USER")
    [[ -z "${REMOTE_BASE_DIR:-}" ]] && missing_vars+=("REMOTE_BASE_DIR")
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_message "ERROR" "Missing required configuration variables: ${missing_vars[*]}"
        log_message "ERROR" "Please edit $CONFIG_FILE and fill in all required values."
        exit 1
    fi
    
    # Set defaults for optional variables
    REMOTE_PORT="${REMOTE_PORT:-22}"
    AUTH_METHOD="${AUTH_METHOD:-key}"
    BATCH_SIZE="${BATCH_SIZE:-50}"
    PARALLEL_JOBS="${PARALLEL_JOBS:-4}"
    TRANSFER_MODE="${TRANSFER_MODE:-binary}"
    SFTP_OPTIONS="${SFTP_OPTIONS:--o StrictHostKeyChecking=accept-new -o ConnectTimeout=10}"
    
    # Validate parallel jobs is a number
    if ! [[ "$PARALLEL_JOBS" =~ ^[0-9]+$ ]]; then
        log_message "WARNING" "Invalid PARALLEL_JOBS value, defaulting to 4"
        PARALLEL_JOBS=4
    fi
    
    # Build SFTP command based on authentication method
    if [[ "$AUTH_METHOD" == "key" ]]; then
        if [[ -n "${SSH_KEY_PATH:-}" ]]; then
            SFTP_CMD="sftp -i $SSH_KEY_PATH -P $REMOTE_PORT $SFTP_OPTIONS"
        else
            SFTP_CMD="sftp -P $REMOTE_PORT $SFTP_OPTIONS"
        fi
    elif [[ "$AUTH_METHOD" == "password" ]]; then
        if [[ -z "${SFTP_PASSWORD:-}" ]]; then
            log_message "ERROR" "SFTP_PASSWORD not set in configuration file"
            exit 1
        fi
        # Check if sshpass is available
        if ! command -v sshpass &> /dev/null; then
            log_message "ERROR" "sshpass is required for password authentication but not installed"
            log_message "INFO" "Install with: sudo apt-get install sshpass"
            exit 1
        fi
        SFTP_CMD="sshpass -p '$SFTP_PASSWORD' sftp -P $REMOTE_PORT $SFTP_OPTIONS"
    else
        log_message "ERROR" "Invalid AUTH_METHOD: $AUTH_METHOD. Must be 'key' or 'password'"
        exit 1
    fi
    
    log_message "DEBUG" "Configuration loaded successfully"
    log_message "DEBUG" "Using SHA256 for integrity verification (MANDATORY)"
    log_message "DEBUG" "Parallel jobs for checksum calculation: $PARALLEL_JOBS"
}

# Function to calculate SHA256 hash of a file
calculate_file_hash() {
    local file="$1"
    sha256sum "$file" | cut -d' ' -f1
}

# Function to generate directory manifest with SHA256 hashes
generate_directory_manifest() {
    local dir_path="$1"
    local manifest_file="$2"
    local exclude_patterns="$3"
    
    log_message "INTEGRITY" "Generating SHA256 manifest for: $(basename "$dir_path")"
    
    # Build find command with exclusions
    local find_cmd="find \"$dir_path\" -type f"
    
    # Add exclusion patterns
    for pattern in $exclude_patterns; do
        find_cmd="$find_cmd -not -path \"*/$pattern/*\" -not -name \"$pattern\""
    done
    
    # Generate sorted manifest with SHA256 hashes
    eval "$find_cmd -print0" | \
        xargs -0 -P "$PARALLEL_JOBS" -I {} sha256sum "{}" | \
        sort -k2 > "$manifest_file"
    
    local file_count=$(wc -l < "$manifest_file")
    log_message "INTEGRITY" "Manifest generated with $file_count files"
    
    return 0
}

# Function to calculate directory integrity hash
calculate_directory_integrity_hash() {
    local dir_path="$1"
    local temp_manifest="${TEMP_DIR}/manifest_$$_${RANDOM}.tmp"
    
    # Generate manifest for the directory
    generate_directory_manifest "$dir_path" "$temp_manifest" "$EXCLUDE_PATTERNS"
    
    # Calculate SHA256 of the manifest (this becomes the directory integrity hash)
    local integrity_hash=$(sha256sum "$temp_manifest" | cut -d' ' -f1)
    
    rm -f "$temp_manifest"
    echo "$integrity_hash"
}

# Function to get stored integrity hash
get_stored_integrity_hash() {
    local dir_path="$1"
    local relative_path="${dir_path#$SOURCE_DIR/}"
    local key="${REMOTE_HOST}:${REMOTE_USER}:${REMOTE_BASE_DIR}:${relative_path}"
    
    grep "^${key}:" "$INTEGRITY_DB" 2>/dev/null | cut -d':' -f5
}

# Function to store integrity hash
store_integrity_hash() {
    local dir_path="$1"
    local integrity_hash="$2"
    local transfer_status="${3:-success}"
    local relative_path="${dir_path#$SOURCE_DIR/}"
    local key="${REMOTE_HOST}:${REMOTE_USER}:${REMOTE_BASE_DIR}:${relative_path}"
    local timestamp=$(date +%s)
    
    # Remove old entry if exists
    sed -i "\|^${key}:|d" "$INTEGRITY_DB" 2>/dev/null || true
    
    # Add new entry
    echo "${key}:${integrity_hash}:${timestamp}:${transfer_status}" >> "$INTEGRITY_DB"
    
    log_message "INTEGRITY" "Stored integrity hash for: $relative_path"
}

# Function to check if directory has been transferred
is_transferred() {
    local dir_path="$1"
    local relative_path="${dir_path#$SOURCE_DIR/}"
    local cache_entry="${REMOTE_HOST}:${REMOTE_USER}:${REMOTE_BASE_DIR}:${relative_path}"
    
    if grep -q "^${cache_entry}$" "$CACHE_FILE" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to mark directory as transferred
mark_transferred() {
    local dir_path="$1"
    local relative_path="${dir_path#$SOURCE_DIR/}"
    local cache_entry="${REMOTE_HOST}:${REMOTE_USER}:${REMOTE_BASE_DIR}:${relative_path}"
    
    echo "$cache_entry" >> "$CACHE_FILE"
    log_message "DEBUG" "Marked as transferred: $relative_path"
}

# Function to verify remote file integrity
verify_remote_integrity() {
    local local_dir="$1"
    local remote_subpath="$2"
    local local_manifest="${TEMP_DIR}/local_manifest_$$.tmp"
    local remote_manifest="${TEMP_DIR}/remote_manifest_$$.tmp"
    
    log_message "INTEGRITY" "Verifying integrity of transferred files..."
    
    # Generate local manifest
    generate_directory_manifest "$local_dir" "$local_manifest" "$EXCLUDE_PATTERNS"
    
    # Create remote SHA256 verification script
    local remote_script="${TEMP_DIR}/remote_verify_$$.sh"
    cat > "$remote_script" << 'EOF'
#!/bin/bash
find "$1" -type f -print0 | while IFS= read -r -d '' file; do
    sha256sum "$file"
done | sort -k2
EOF
    chmod +x "$remote_script"
    
    # Upload verification script
    echo "put \"$remote_script\" \"${remote_subpath}/.verify_$$.sh\"" | \
        eval "${SFTP_CMD} -b - ${REMOTE_USER}@${REMOTE_HOST}" > /dev/null 2>&1
    
    # Execute remote verification
    local ssh_cmd="${SFTP_CMD%%sftp*}ssh"
    if [[ "$AUTH_METHOD" == "key" && -n "${SSH_KEY_PATH:-}" ]]; then
        ssh_cmd="ssh -i $SSH_KEY_PATH -p $REMOTE_PORT"
    else
        ssh_cmd="ssh -p $REMOTE_PORT"
    fi
    
    # Run remote SHA256 calculation
    eval "${ssh_cmd} ${REMOTE_USER}@${REMOTE_HOST} 'cd \"${REMOTE_BASE_DIR}/${remote_subpath}\" && bash .verify_$$.sh .'" > "$remote_manifest" 2>/dev/null
    
    # Clean up remote script
    echo "rm \"${remote_subpath}/.verify_$$.sh\"" | \
        eval "${SFTP_CMD} -b - ${REMOTE_USER}@${REMOTE_HOST}" > /dev/null 2>&1
    
    # Compare manifests
    local local_hash=$(sha256sum "$local_manifest" | cut -d' ' -f1)
    local remote_hash=$(sha256sum "$remote_manifest" | cut -d' ' -f1)
    
    rm -f "$local_manifest" "$remote_manifest" "$remote_script"
    
    if [[ "$local_hash" == "$remote_hash" ]]; then
        log_message "INTEGRITY" "✓ Integrity verification PASSED"
        return 0
    else
        log_message "ERROR" "✗ Integrity verification FAILED - Files may be corrupted"
        log_message "INTEGRITY" "Local hash: $local_hash"
        log_message "INTEGRITY" "Remote hash: $remote_hash"
        return 1
    fi
}

# Function to test SFTP connection
test_connection() {
    log_message "INFO" "Testing SFTP connection to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PORT}..."
    
    local test_cmd="${SFTP_CMD} -b - ${REMOTE_USER}@${REMOTE_HOST} <<< 'pwd' 2>&1"
    if eval "$test_cmd" > /dev/null 2>&1; then
        log_message "INFO" "Connection test successful"
        return 0
    else
        log_message "ERROR" "Failed to connect to remote server"
        return 1
    fi
}

# Function to create remote directory structure
create_remote_directory() {
    local remote_path="$1"
    
    # Create directory using SFTP batch commands
    local batch_commands="cd \"$REMOTE_BASE_DIR\" || exit 1
mkdir -p \"$remote_path\""
    
    echo "$batch_commands" | eval "${SFTP_CMD} -b - ${REMOTE_USER}@${REMOTE_HOST}" > /dev/null 2>&1
    return $?
}

# Function to transfer a single directory
transfer_directory() {
    local source_subdir="$1"
    local relative_path="${source_subdir#$SOURCE_DIR/}"
    local remote_target_dir="${REMOTE_BASE_DIR}/${relative_path}"
    
    log_message "INFO" "Processing: $relative_path"
    
    # Calculate current integrity hash
    local current_hash=$(calculate_directory_integrity_hash "$source_subdir")
    log_message "INTEGRITY" "SHA256 integrity hash: $current_hash"
    
    # Check if directory has already been transferred
    if is_transferred "$source_subdir"; then
        local stored_hash=$(get_stored_integrity_hash "$source_subdir")
        
        if [[ "$current_hash" == "$stored_hash" ]]; then
            log_message "INFO" "Directory unchanged, skipping: $relative_path"
            return 0
        else
            log_message "INFO" "Directory changed, updating: $relative_path"
            if [[ -n "$stored_hash" ]]; then
                log_message "INTEGRITY" "Previous hash: $stored_hash"
                log_message "INTEGRITY" "Current hash:  $current_hash"
            fi
        fi
    fi
    
    # Create remote directory structure
    if ! create_remote_directory "$relative_path"; then
        log_message "ERROR" "Failed to create remote directory: $relative_path"
        store_integrity_hash "$source_subdir" "$current_hash" "failed"
        return 1
    fi
    
    # Prepare SFTP batch commands for file transfer
    local temp_batch_file="${TEMP_DIR}/batch_$$_${RANDOM}.tmp"
    local file_count=0
    local total_files=0
    
    # Set transfer mode
    echo "$TRANSFER_MODE" > "$temp_batch_file"
    
    # Build exclusion pattern for find command
    local exclude_patterns=""
    for pattern in $EXCLUDE_PATTERNS; do
        exclude_patterns="$exclude_patterns -not -path '*/$pattern/*' -not -name '$pattern'"
    done
    
    # Count total files for progress indication
    total_files=$(eval "find \"$source_subdir\" -type f $exclude_patterns | wc -l")
    log_message "INFO" "Transferring $total_files files..."
    
    # Find all files and create batch commands
    eval "find \"$source_subdir\" -type f $exclude_patterns -print0" | while IFS= read -r -d '' file; do
        local file_rel_path="${file#$source_subdir/}"
        local remote_file_path="${relative_path}/${file_rel_path}"
        
        # Create parent directories if needed
        local parent_dir=$(dirname "$file_rel_path")
        if [[ "$parent_dir" != "." ]]; then
            echo "-mkdir \"${relative_path}/${parent_dir}\"" >> "$temp_batch_file"
        fi
        
        echo "put \"$file\" \"${remote_file_path}\"" >> "$temp_batch_file"
        ((file_count++))
        
        # Process in batches to avoid command line length limits
        if [[ $file_count -ge $BATCH_SIZE ]]; then
            cat "$temp_batch_file" | eval "${SFTP_CMD} -b - ${REMOTE_USER}@${REMOTE_HOST}" > /dev/null 2>&1
            if [[ $? -eq 0 ]]; then
                log_message "DEBUG" "Transferred $file_count/$total_files files"
            else
                log_message "ERROR" "Failed to transfer batch of files for $relative_path"
                rm -f "$temp_batch_file"
                store_integrity_hash "$source_subdir" "$current_hash" "failed"
                return 1
            fi
            # Reset batch file with transfer mode
            echo "$TRANSFER_MODE" > "$temp_batch_file"
            file_count=0
        fi
    done
    
    # Transfer any remaining files
    if [[ $file_count -gt 0 ]]; then
        cat "$temp_batch_file" | eval "${SFTP_CMD} -b - ${REMOTE_USER}@${REMOTE_HOST}" > /dev/null 2>&1
        if [[ $? -eq 0 ]]; then
            log_message "DEBUG" "Transferred final $file_count files"
        else
            log_message "ERROR" "Failed to transfer final batch of files for $relative_path"
            rm -f "$temp_batch_file"
            store_integrity_hash "$source_subdir" "$current_hash" "failed"
            return 1
        fi
    fi
    
    rm -f "$temp_batch_file"
    
    # Verify integrity of transferred files
    if ! verify_remote_integrity "$source_subdir" "$relative_path"; then
        log_message "ERROR" "Integrity verification failed for: $relative_path"
        store_integrity_hash "$source_subdir" "$current_hash" "failed"
        return 1
    fi
    
    # Mark as transferred and store integrity hash
    mark_transferred "$source_subdir"
    store_integrity_hash "$source_subdir" "$current_hash" "success"
    
    log_message "INFO" "Successfully transferred and verified: $relative_path"
    
    return 0
}

# Function to display transfer statistics
show_statistics() {
    log_message "INFO" "========================================="
    log_message "INFO" "Transfer Statistics:"
    
    if [[ -f "$INTEGRITY_DB" ]]; then
        local total_entries=$(wc -l < "$INTEGRITY_DB" 2>/dev/null || echo "0")
        local success_entries=$(grep -c ":success$" "$INTEGRITY_DB" 2>/dev/null || echo "0")
        local failed_entries=$(grep -c ":failed$" "$INTEGRITY_DB" 2>/dev/null || echo "0")
        
        log_message "INFO" "Total directories tracked: $total_entries"
        log_message "INFO" "Successful transfers: $success_entries"
        log_message "INFO" "Failed transfers: $failed_entries"
    fi
    
    log_message "INFO" "========================================="
}

# Function to cleanup temporary files
cleanup() {
    log_message "DEBUG" "Cleaning up temporary files..."
    rm -f "${TEMP_DIR}"/*.tmp 2>/dev/null || true
    log_message "DEBUG" "Cleanup complete"
}

# Main execution
main() {
    # Check command line arguments
    if [[ $# -ne 2 ]]; then
        echo "Usage: $0 <source_directory> <target_directory>"
        echo "Example: $0 /home/user/data /backup/data"
        exit 1
    fi
    
    SOURCE_DIR="$1"
    TARGET_DIR="$2"
    
    # Validate source directory
    if [[ ! -d "$SOURCE_DIR" ]]; then
        log_message "ERROR" "Source directory does not exist: $SOURCE_DIR"
        exit 1
    fi
    
    # Convert to absolute paths
    SOURCE_DIR=$(realpath "$SOURCE_DIR")
    
    # Initialize configuration
    initialize
    
    # Load configuration
    load_config
    
    log_message "INFO" "╔════════════════════════════════════════════════════════════╗"
    log_message "INFO" "║     SFTP Transfer Script with SHA256 Integrity Checking    ║"
    log_message "INFO" "╚════════════════════════════════════════════════════════════╝"
    log_message "INFO" "Source: $SOURCE_DIR"
    log_message "INFO" "Destination: ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_BASE_DIR}"
    log_message "INFO" "Integrity: SHA256 (MANDATORY)"
    
    # Check for required tools
    local required_tools=("sha256sum" "find" "xargs")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_message "ERROR" "Required tool not found: $tool"
            exit 1
        fi
    done
    
    # Test connection
    if ! test_connection; then
        log_message "ERROR" "Cannot proceed without valid connection"
        exit 1
    fi
    
    # Show current statistics
    show_statistics
    
    # Find all immediate subdirectories
    local transferred_count=0
    local failed_count=0
    local skipped_count=0
    local start_time=$(date +%s)
    
    while IFS= read -r -d '' subdir; do
        if transfer_directory "$subdir"; then
            ((transferred_count++))
        else
            ((failed_count++))
        fi
    done < <(find "$SOURCE_DIR" -maxdepth 1 -type d -not -path "$SOURCE_DIR" -print0)
    
    # Calculate elapsed time
    local end_time=$(date +%s)
    local elapsed=$((end_time - start_time))
    local minutes=$((elapsed / 60))
    local seconds=$((elapsed % 60))
    
    # Summary
    log_message "INFO" "════════════════════════════════════════════════════════════"
    log_message "INFO" "Transfer Complete!"
    log_message "INFO" "Time elapsed: ${minutes}m ${seconds}s"
    log_message "INFO" "Directories processed: $((transferred_count + failed_count))"
    log_message "INFO" "Successful transfers: $transferred_count"
    log_message "INFO" "Failed transfers: $failed_count"
    log_message "INFO" "════════════════════════════════════════════════════════════"
    
    # Show updated statistics
    show_statistics
    
    # Cleanup
    cleanup
    
    if [[ $failed_count -gt 0 ]]; then
        exit 1
    fi
}

# Trap for cleanup on script exit
trap 'log_message "INFO" "Script interrupted - cleaning up..."; cleanup; exit 1' INT TERM
trap 'cleanup' EXIT

# Run main function
main "$@"