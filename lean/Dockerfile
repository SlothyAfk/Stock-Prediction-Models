# ==============================================================================
# IMMUTABLE LEAN ENGINE DOCKERFILE
# ==============================================================================
#
# This Dockerfile implements the "Locked Down" production architecture for
# running QuantConnect's LEAN algorithmic trading engine with:
#   1. Immutable base image (pinned by SHA256 digest)
#   2. Strictly pinned Python dependencies (==version.subversion)
#
# Architecture: Modular Dockerfile Approach (Path 2 from blueprint)
# - Treats official quantconnect/lean as pre-built binary
# - Adds only a lightweight Python dependency layer
# - No C# compilation required
# - Fast, simple, maintainable
#
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Base Image with Immutable Digest
# ------------------------------------------------------------------------------
# CRITICAL: This digest MUST be obtained by inspecting the official image.
#
# To update this digest:
#   1. Pull the desired tag: docker pull quantconnect/lean:latest
#   2. Inspect to get digest: docker image inspect quantconnect/lean:latest \
#                             --format '{{index .RepoDigests 0}}'
#   3. Replace the ARG BASE_DIGEST value below with the output
#
# The digest is a cryptographic SHA256 hash. If any byte of the image changes,
# the digest changes. This guarantees immutability.
# ------------------------------------------------------------------------------

ARG BASE_DIGEST="sha256:6b5eeea3f82130b4a0f097ce2a6651d0a06b452dcf6289cb5893fa2a61fdab70"

# Use the official LEAN engine image, pinned by immutable digest
FROM quantconnect/lean@${BASE_DIGEST}

# Metadata
LABEL maintainer="Stock Prediction Models - LEAN Team"
LABEL description="Immutable LEAN Engine with Locked Python Dependencies"
LABEL version="1.0.0"

# ------------------------------------------------------------------------------
# Stage 2: Install System Dependencies and TA-Lib C Library
# ------------------------------------------------------------------------------

# Switch to root user for package installation
# (The base LEAN image runs as root by default)
USER root

# Install build dependencies for TA-Lib
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib C library (required for ta-lib Python wrapper)
RUN cd /tmp && \
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    ldconfig && \
    cd /tmp && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# ------------------------------------------------------------------------------
# Stage 3: Install Locked Python Dependencies
# ------------------------------------------------------------------------------

# Set working directory for dependency installation
WORKDIR /tmp/build

# Install numpy first (required by TA-Lib and other packages)
RUN pip install --no-cache-dir numpy==1.26.4

# Copy ONLY the locked requirements file
# This minimizes cache invalidation - requirements change less frequently than code
COPY requirements.locked.txt .

# Install dependencies with strict version pinning
# Note: Using --no-deps removed - TA-Lib needs to build against numpy
# Flags explained:
#   --no-cache-dir: Don't cache packages (reduces image size)
#   -r: Install from requirements file
RUN pip install --no-cache-dir -r requirements.locked.txt

# Clean up temporary files
RUN rm -rf /tmp/build

# ------------------------------------------------------------------------------
# Stage 4: Runtime Configuration
# ------------------------------------------------------------------------------

# Return to the LEAN working directory
WORKDIR /Lean/Launcher/bin/Debug

# Set Python path to include LEAN's Python libraries
ENV PYTHONPATH="/Lean/Launcher/bin/Debug:${PYTHONPATH}"

# Expose standard LEAN ports
# 5678: Debugger port (for debugging algorithms)
# 8080: API port (for live trading API)
EXPOSE 5678 8080

# Health check to verify LEAN engine is responsive
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD pgrep -f "QuantConnect.Lean.Launcher" || exit 1

# Default entrypoint: Run the LEAN engine
# This can be overridden in docker-compose.yml or at runtime
ENTRYPOINT ["dotnet", "QuantConnect.Lean.Launcher.dll"]

# Default command: Run with default configuration
CMD ["--config", "/Lean/Launcher/config.json"]

# ==============================================================================
# Build Instructions:
# ==============================================================================
#
# 1. Update BASE_DIGEST (see instructions above)
#
# 2. Build the image with a versioned tag:
#    docker build -t lean-locked:1.0.0 -f Dockerfile .
#
# 3. (Optional) Tag for production:
#    docker tag lean-locked:1.0.0 lean-locked:production
#
# 4. (Optional) Push to private registry:
#    docker tag lean-locked:1.0.0 your-registry.com/lean-locked:1.0.0
#    docker push your-registry.com/lean-locked:1.0.0
#
# ==============================================================================
