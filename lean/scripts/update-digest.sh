#!/bin/bash

# ==============================================================================
# Update LEAN Base Image Digest
# ==============================================================================
#
# This script automates the process of updating the immutable LEAN base image
# digest in your Dockerfile.
#
# Usage:
#   ./scripts/update-digest.sh [tag]
#
# Examples:
#   ./scripts/update-digest.sh              # Updates from :latest
#   ./scripts/update-digest.sh v2.5.14      # Updates from specific tag
#
# ==============================================================================

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_IMAGE="quantconnect/lean"
DOCKERFILE="${DOCKERFILE:-Dockerfile}"
ENV_FILE="${ENV_FILE:-.env}"

# Parse arguments
TAG="${1:-latest}"
FULL_IMAGE="${DOCKER_IMAGE}:${TAG}"

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
    log_info "Updating LEAN base image digest..."
    log_info "Image: ${FULL_IMAGE}"
    echo ""

    # Step 1: Pull the image
    log_info "Step 1/4: Pulling image ${FULL_IMAGE}..."
    if ! docker pull "${FULL_IMAGE}"; then
        log_error "Failed to pull image ${FULL_IMAGE}"
        log_error "Please check your internet connection and Docker installation"
        exit 1
    fi
    log_success "Image pulled successfully"
    echo ""

    # Step 2: Extract the digest
    log_info "Step 2/4: Extracting immutable digest..."
    REPO_DIGEST=$(docker image inspect "${FULL_IMAGE}" --format '{{index .RepoDigests 0}}')

    if [ -z "${REPO_DIGEST}" ]; then
        log_error "Failed to extract digest from ${FULL_IMAGE}"
        exit 1
    fi

    # Extract just the sha256 part
    DIGEST=$(echo "${REPO_DIGEST}" | cut -d'@' -f2)

    log_success "Extracted digest: ${DIGEST}"
    echo ""

    # Step 3: Update Dockerfile
    log_info "Step 3/4: Updating ${DOCKERFILE}..."

    if [ ! -f "${DOCKERFILE}" ]; then
        log_error "Dockerfile not found: ${DOCKERFILE}"
        exit 1
    fi

    # Create backup
    cp "${DOCKERFILE}" "${DOCKERFILE}.backup"

    # Update the ARG BASE_DIGEST line
    if grep -q "ARG BASE_DIGEST=" "${DOCKERFILE}"; then
        sed -i.tmp "s|ARG BASE_DIGEST=.*|ARG BASE_DIGEST=\"${DIGEST}\"|" "${DOCKERFILE}"
        rm -f "${DOCKERFILE}.tmp"
        log_success "Dockerfile updated successfully"
    else
        log_error "Could not find 'ARG BASE_DIGEST=' in ${DOCKERFILE}"
        log_warning "Please update manually"
        exit 1
    fi
    echo ""

    # Step 4: Update .env file if it exists
    log_info "Step 4/4: Updating ${ENV_FILE} (if exists)..."

    if [ -f "${ENV_FILE}" ]; then
        # Create backup
        cp "${ENV_FILE}" "${ENV_FILE}.backup"

        if grep -q "LEAN_BASE_DIGEST=" "${ENV_FILE}"; then
            sed -i.tmp "s|LEAN_BASE_DIGEST=.*|LEAN_BASE_DIGEST=${DIGEST}|" "${ENV_FILE}"
            rm -f "${ENV_FILE}.tmp"
            log_success ".env file updated successfully"
        else
            log_warning "LEAN_BASE_DIGEST not found in ${ENV_FILE}"
            log_info "Adding LEAN_BASE_DIGEST to ${ENV_FILE}..."
            echo "" >> "${ENV_FILE}"
            echo "# Updated by update-digest.sh on $(date)" >> "${ENV_FILE}"
            echo "LEAN_BASE_DIGEST=${DIGEST}" >> "${ENV_FILE}"
            log_success "LEAN_BASE_DIGEST added to ${ENV_FILE}"
        fi
    else
        log_warning "${ENV_FILE} not found - skipping"
    fi
    echo ""

    # Summary
    echo "================================================================"
    log_success "LEAN digest update completed!"
    echo "================================================================"
    echo ""
    echo "Summary:"
    echo "  Image:      ${FULL_IMAGE}"
    echo "  New Digest: ${DIGEST}"
    echo ""
    echo "Files updated:"
    echo "  ✓ ${DOCKERFILE}"
    [ -f "${ENV_FILE}" ] && echo "  ✓ ${ENV_FILE}"
    echo ""
    echo "Backups created:"
    echo "  → ${DOCKERFILE}.backup"
    [ -f "${ENV_FILE}.backup" ] && echo "  → ${ENV_FILE}.backup"
    echo ""
    echo "Next steps:"
    echo "  1. Review the changes:"
    echo "     git diff ${DOCKERFILE}"
    echo ""
    echo "  2. Rebuild your image:"
    echo "     docker-compose build --no-cache"
    echo ""
    echo "  3. Test the new build:"
    echo "     docker-compose run --rm lean-engine --version"
    echo ""
    echo "  4. Commit the changes:"
    echo "     git add ${DOCKERFILE}"
    echo "     git commit -m \"chore: update LEAN base digest to ${TAG}\""
    echo ""
    echo "================================================================"
}

# Run main function
main "$@"
