#!/bin/bash

# ==============================================================================
# Compile Python Requirements for LEAN
# ==============================================================================
#
# This script uses pip-compile to generate a fully locked requirements.txt
# file with exact versions of all dependencies and their transitive dependencies.
#
# The compilation is run INSIDE the LEAN container to ensure compatibility
# with the target environment.
#
# Usage:
#   ./scripts/compile-requirements.sh [digest]
#
# Examples:
#   ./scripts/compile-requirements.sh
#   ./scripts/compile-requirements.sh sha256:abc123...
#
# ==============================================================================

set -e
set -u
set -o pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
REQUIREMENTS_IN="${REQUIREMENTS_IN:-requirements.in}"
REQUIREMENTS_LOCKED="${REQUIREMENTS_LOCKED:-requirements.locked.txt}"
DOCKER_IMAGE="${DOCKER_IMAGE:-quantconnect/lean}"

# Functions
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

# Main script
main() {
    log_info "Compiling Python requirements for LEAN..."
    echo ""

    # Step 1: Check if requirements.in exists
    if [ ! -f "${REQUIREMENTS_IN}" ]; then
        log_error "File not found: ${REQUIREMENTS_IN}"
        log_error "Please create ${REQUIREMENTS_IN} with your top-level dependencies"
        exit 1
    fi

    log_success "Found ${REQUIREMENTS_IN}"
    echo ""

    # Step 2: Determine image digest
    if [ $# -eq 0 ]; then
        # No argument provided, try to extract from Dockerfile
        log_info "No digest provided, extracting from Dockerfile..."

        if [ ! -f "Dockerfile" ]; then
            log_error "Dockerfile not found"
            log_error "Please provide a digest as argument or ensure Dockerfile exists"
            exit 1
        fi

        DIGEST=$(grep "ARG BASE_DIGEST=" Dockerfile | cut -d'"' -f2)

        if [ -z "${DIGEST}" ]; then
            log_error "Could not extract BASE_DIGEST from Dockerfile"
            log_error "Please provide digest as argument"
            exit 1
        fi

        log_success "Extracted digest from Dockerfile: ${DIGEST}"
    else
        DIGEST="$1"
        log_info "Using provided digest: ${DIGEST}"
    fi

    FULL_IMAGE="${DOCKER_IMAGE}@${DIGEST}"
    echo ""

    # Step 3: Display requirements.in
    log_info "Input dependencies (${REQUIREMENTS_IN}):"
    echo "---"
    cat "${REQUIREMENTS_IN}"
    echo "---"
    echo ""

    # Step 4: Pull the image (if needed)
    log_info "Ensuring image is available: ${FULL_IMAGE}"
    if ! docker image inspect "${FULL_IMAGE}" >/dev/null 2>&1; then
        log_info "Image not found locally, pulling..."
        docker pull "${FULL_IMAGE}"
    fi
    log_success "Image ready"
    echo ""

    # Step 5: Run pip-compile inside the container
    log_info "Running pip-compile inside LEAN container..."
    log_warning "This may take a few minutes..."
    echo ""

    docker run --rm \
        -v "$(pwd):/app" \
        -w /app \
        "${FULL_IMAGE}" \
        bash -c "
            set -e
            echo '[Container] Installing pip-tools...'
            pip install --quiet pip-tools
            echo '[Container] Running pip-compile...'
            pip-compile \
                ${REQUIREMENTS_IN} \
                --output-file=${REQUIREMENTS_LOCKED} \
                --resolver=backtracking \
                --verbose \
                --annotation-style=line
            echo '[Container] Compilation complete!'
        "

    echo ""

    # Step 6: Verify output
    if [ ! -f "${REQUIREMENTS_LOCKED}" ]; then
        log_error "Failed to generate ${REQUIREMENTS_LOCKED}"
        exit 1
    fi

    log_success "Requirements compiled successfully!"
    echo ""

    # Step 7: Display summary
    PACKAGE_COUNT=$(grep -c "^[a-zA-Z]" "${REQUIREMENTS_LOCKED}" || true)

    echo "================================================================"
    log_success "Compilation Summary"
    echo "================================================================"
    echo ""
    echo "Input:       ${REQUIREMENTS_IN}"
    echo "Output:      ${REQUIREMENTS_LOCKED}"
    echo "Packages:    ${PACKAGE_COUNT} total (including transitive dependencies)"
    echo "Image:       ${FULL_IMAGE}"
    echo ""
    echo "Next steps:"
    echo "  1. Review the locked requirements:"
    echo "     cat ${REQUIREMENTS_LOCKED}"
    echo ""
    echo "  2. Commit the locked file:"
    echo "     git add ${REQUIREMENTS_LOCKED}"
    echo "     git commit -m \"chore: update locked Python dependencies\""
    echo ""
    echo "  3. Rebuild your Docker image:"
    echo "     docker-compose build --no-cache"
    echo ""
    echo "================================================================"
}

# Run main
main "$@"
