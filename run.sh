#!/bin/bash
# Ubuntu FAI Build System Docker Runner
# Handles Docker build and execution with proper volume mounts and permissions

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="ubuntu-fai"
IMAGE_TAG="latest"
CONTAINER_NAME="ubuntu-fai-build"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage information
usage() {
    cat << EOF
Ubuntu FAI Build System Docker Runner

USAGE:
    $0 [OPTIONS] <config.json> [BUILD_ARGS...]

OPTIONS:
    -h, --help              Show this help message
    -b, --build             Force rebuild of Docker image
    -c, --clean             Clean up containers and images
    -d, --debug             Enable debug mode (verbose output)
    --no-cache              Build Docker image without cache
    --output-dir DIR        Specify output directory (default: ./output)

EXAMPLES:
    $0 config.json.example                    # Build ISO with example config
    $0 --build config.json.example           # Rebuild Docker image first
    $0 --output-dir /tmp/iso config.json     # Custom output directory
    $0 --debug config.json                   # Enable verbose logging

NOTES:
    - Docker must be installed and running
    - Config file must exist and be readable
    - Output directory will be created if it doesn't exist
    - Container runs with current user permissions for file access

EOF
}

# Parse command line arguments
FORCE_BUILD=false
CLEAN=false
DEBUG=false
NO_CACHE=false
OUTPUT_DIR="$SCRIPT_DIR/output"
CONFIG_FILE=""
BUILD_ARGS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -b|--build)
            FORCE_BUILD=true
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -*)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            if [[ -z "$CONFIG_FILE" ]]; then
                CONFIG_FILE="$1"
            else
                BUILD_ARGS+=("$1")
            fi
            shift
            ;;
    esac
done

# Enable debug mode if requested
if [[ "$DEBUG" == "true" ]]; then
    set -x
    log_info "Debug mode enabled"
fi

# Clean up function
cleanup() {
    if [[ "$CLEAN" == "true" ]]; then
        log_info "Cleaning up Docker containers and images..."
        docker container rm -f "$CONTAINER_NAME" 2>/dev/null || true
        docker image rm -f "$IMAGE_NAME:$IMAGE_TAG" 2>/dev/null || true
        log_success "Cleanup completed"
        exit 0
    fi
}

# Check Docker availability
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        log_info "Please install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        log_info "Please start Docker and try again"
        exit 1
    fi
}

# Build Docker image
build_image() {
    local build_args=()
    
    if [[ "$NO_CACHE" == "true" ]]; then
        build_args+=("--no-cache")
    fi

    log_info "Building Docker image: $IMAGE_NAME:$IMAGE_TAG"
    
    if ! docker build "${build_args[@]}" -t "$IMAGE_NAME:$IMAGE_TAG" "$SCRIPT_DIR"; then
        log_error "Failed to build Docker image"
        exit 1
    fi
    
    log_success "Docker image built successfully"
}

# Check if image exists and build if necessary
check_and_build_image() {
    if [[ "$FORCE_BUILD" == "true" ]] || ! docker image inspect "$IMAGE_NAME:$IMAGE_TAG" &> /dev/null; then
        build_image
    else
        log_info "Using existing Docker image: $IMAGE_NAME:$IMAGE_TAG"
    fi
}

# Validate config file
validate_config() {
    if [[ -z "$CONFIG_FILE" ]]; then
        log_error "No configuration file specified"
        usage
        exit 1
    fi

    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_error "Configuration file not found: $CONFIG_FILE"
        exit 1
    fi

    if [[ ! -r "$CONFIG_FILE" ]]; then
        log_error "Configuration file not readable: $CONFIG_FILE"
        exit 1
    fi

    # Convert to absolute path
    CONFIG_FILE="$(realpath "$CONFIG_FILE")"
    log_info "Using configuration file: $CONFIG_FILE"
}

# Prepare output directory
prepare_output_dir() {
    # Convert to absolute path
    OUTPUT_DIR="$(realpath -m "$OUTPUT_DIR")"
    
    if [[ ! -d "$OUTPUT_DIR" ]]; then
        log_info "Creating output directory: $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"
    fi
    
    if [[ ! -w "$OUTPUT_DIR" ]]; then
        log_error "Output directory not writable: $OUTPUT_DIR"
        exit 1
    fi
    
    log_info "Using output directory: $OUTPUT_DIR"
}

# Get current user ID and group ID for permission mapping
get_user_info() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        USER_ID=$(id -u)
        GROUP_ID=$(id -g)
    else
        # Linux
        USER_ID=$(id -u)
        GROUP_ID=$(id -g)
    fi
    
    log_info "Running container with UID:GID = $USER_ID:$GROUP_ID"
}

# Run Docker container
run_container() {
    local docker_args=(
        "run"
        "--rm"
        "--name" "$CONTAINER_NAME"
        "--user" "$USER_ID:$GROUP_ID"
        "--volume" "$CONFIG_FILE:/app/config.json:ro"
        "--volume" "$OUTPUT_DIR:/app/output:rw"
        "--volume" "$SCRIPT_DIR:/app/host-src:ro"
        "--workdir" "/app"
    )

    # Add privileged mode for FAI operations (ISO creation requires loop devices)
    docker_args+=("--privileged")
    
    # Add environment variables
    docker_args+=("--env" "PYTHONUNBUFFERED=1")
    
    if [[ "$DEBUG" == "true" ]]; then
        docker_args+=("--env" "FAI_DEBUG=1")
    fi

    # Add image and command
    docker_args+=("$IMAGE_NAME:$IMAGE_TAG")
    docker_args+=("python3" "build.py" "config.json")
    docker_args+=("${BUILD_ARGS[@]}")

    log_info "Starting Ubuntu FAI build container..."
    log_info "Container name: $CONTAINER_NAME"
    log_info "Config file: $CONFIG_FILE"
    log_info "Output directory: $OUTPUT_DIR"
    
    if ! docker "${docker_args[@]}"; then
        log_error "Container execution failed"
        exit 1
    fi
    
    log_success "Build completed successfully"
    log_info "Check output directory: $OUTPUT_DIR"
}

# Main execution
main() {
    # Handle cleanup if requested
    cleanup
    
    # Validate environment
    check_docker
    
    # Validate inputs
    validate_config
    prepare_output_dir
    get_user_info
    
    # Build and run
    check_and_build_image
    run_container
}

# Trap signals for cleanup
trap 'log_warning "Interrupted by user"; exit 130' INT TERM

# Run main function
main "$@"