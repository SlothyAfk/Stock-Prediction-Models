# The Immutable LEAN Pod

<p align="center">
  <strong>A Production-Grade Architectural Blueprint for Containerizing QuantConnect LEAN</strong>
</p>

<p align="center">
  <em>Building "Locked Down," Reproducible LEAN Environments with Pinned Dependencies and Immutable Image Digests</em>
</p>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Directory Structure](#directory-structure)
- [Configuration](#configuration)
- [Usage](#usage)
- [Updating Dependencies](#updating-dependencies)
- [Updating LEAN Version](#updating-lean-version)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [References](#references)

---

## 🎯 Overview

This directory implements a **production-grade, immutable containerized environment** for running QuantConnect's LEAN algorithmic trading engine. Unlike the default `lean-cli` configuration optimized for development convenience, this setup prioritizes:

### Core Principles

1. **Image Immutability**: Base images referenced exclusively by SHA256 content digest, not floating tags like `:latest`
2. **Dependency Immutability**: All Python packages pinned to exact versions (`==version.subversion`)
3. **Reproducibility**: Byte-for-byte identical builds across environments and time
4. **Auditability**: Complete dependency manifests committed to version control
5. **Production-Ready**: Suitable for CI/CD pipelines, live trading, and compliance requirements

### Why This Matters

The default `lean-cli` is designed to:
- Automatically check for and pull updated images weekly
- Use floating `:latest` tags that can change at any time
- Install "latest compatible versions" of dependencies

This is **perfect for development** but **problematic for production**, where stability and reproducibility are non-negotiable.

This blueprint solves that problem.

---

## 🏗️ Architecture

### Two-Part Immutability Strategy

#### 1. Image Immutability (SHA256 Digest)

```dockerfile
# ❌ Mutable (BAD for production)
FROM quantconnect/lean:latest

# ✅ Immutable (GOOD for production)
FROM quantconnect/lean@sha256:8c1e1b4e8e8c8f8e...
```

Docker tags are **pointers** that can be moved. Digests are **cryptographic hashes** that cannot change.

#### 2. Dependency Immutability (Exact Versions)

```txt
# ❌ Unpinned (BAD for production)
pandas
numpy

# ✅ Pinned (GOOD for production)
pandas==2.1.4
numpy==1.26.4
```

### Modular Dockerfile Approach (Recommended Path 2)

We use a **modular architecture** that treats the official `quantconnect/lean` image as a pre-built binary and adds only a lightweight Python dependency layer:

```
┌─────────────────────────────────────┐
│  quantconnect/lean@sha256:...       │  ← Official LEAN engine (immutable)
│  (Pre-compiled C# engine)           │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│  + requirements.locked.txt          │  ← Your pinned dependencies
│  + pip install --no-deps            │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│  lean-locked:1.0.0                  │  ← Your immutable image
└─────────────────────────────────────┘
```

**Benefits:**
- ✅ Fast builds (no C# compilation)
- ✅ Simple maintenance (no LEAN source code fork)
- ✅ Clean separation (platform vs. user code)
- ✅ Standard Docker best practices

---

## 📦 Prerequisites

### Required Software

- **Docker**: >= 20.10 ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: >= 2.0 ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **Git**: For version control

### Recommended Tools

- **pip-tools**: For dependency compilation
  ```bash
  pip install pip-tools
  ```

---

## 🚀 Quick Start

### Step 1: Clone and Navigate

```bash
cd lean
```

### Step 2: Get the Immutable Digest

```bash
# Pull the official LEAN image
docker pull quantconnect/lean:latest

# Extract its immutable digest
docker image inspect quantconnect/lean:latest --format '{{index .RepoDigests 0}}'
```

Output example:
```
quantconnect/lean@sha256:8c1e1b4e8e8c8f8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e8e
```

### Step 3: Update the Dockerfile

Edit `Dockerfile` and replace the `ARG BASE_DIGEST` value with your digest:

```dockerfile
ARG BASE_DIGEST="sha256:YOUR_ACTUAL_DIGEST_HERE"
```

### Step 4: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials and configuration
nano .env
```

### Step 5: Create Directory Structure

```bash
# Create required directories
mkdir -p algorithms config data results logs

# Create a sample algorithm
cat > algorithms/main.py << 'EOF'
from AlgorithmImports import *

class BasicTemplateAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2020, 12, 31)
        self.SetCash(100000)
        self.AddEquity("SPY", Resolution.Daily)

    def OnData(self, data):
        if not self.Portfolio.Invested:
            self.SetHoldings("SPY", 1)
EOF
```

### Step 6: Get Default Config

```bash
# Extract default LEAN configuration
docker run --rm quantconnect/lean:latest cat /Lean/Launcher/config.json > config/config.json

# Customize config.json as needed
```

### Step 7: Build the Image

```bash
# Build your immutable LEAN image
docker-compose build --no-cache
```

### Step 8: Run

```bash
# Start LEAN engine
docker-compose up
```

---

## 📁 Directory Structure

```
lean/
├── Dockerfile                   # Immutable LEAN engine image definition
├── docker-compose.yml          # Service orchestration
├── requirements.in             # Top-level Python dependencies
├── requirements.locked.txt     # Pinned dependency manifest (autogenerated)
├── .env.example                # Environment variable template
├── .env                        # Your actual environment config (gitignored)
├── .gitignore                  # Git ignore patterns
├── README.md                   # This file
│
├── algorithms/                 # Your trading algorithms (.py, .cs)
│   └── main.py
│
├── config/                     # LEAN configuration
│   └── config.json
│
├── data/                       # Market data cache (gitignored)
├── results/                    # Backtest results (gitignored)
├── logs/                       # Application logs (gitignored)
└── storage/                    # Live trading state (gitignored)
```

---

## ⚙️ Configuration

### Environment Variables

All configuration is managed through the `.env` file. See `.env.example` for all available options.

**Key Variables:**

```bash
# Image Configuration
LEAN_BASE_DIGEST=sha256:...        # Immutable base image digest
LEAN_VERSION=1.0.0                 # Your image version tag

# LEAN Mode
LEAN_MODE=backtesting              # backtesting, live-paper, live
LEAN_ENVIRONMENT=live-paper        # live-paper or live

# API Credentials (QuantConnect)
QC_API_TOKEN=your_token_here
QC_USER_ID=your_user_id

# Brokerage Credentials
IB_ACCOUNT=your_account
IB_USER_NAME=your_username
IB_PASSWORD=your_password

# Resource Limits
LEAN_CPU_LIMIT=4.0
LEAN_MEMORY_LIMIT=8G
```

### LEAN Configuration (config.json)

The `config/config.json` file controls LEAN's behavior. Key sections:

```json
{
  "algorithm-type-name": "BasicTemplateAlgorithm",
  "algorithm-language": "Python",
  "algorithm-location": "/Lean/Algorithm/main.py",

  "environment": "live-paper",
  "live-mode": false,

  "data-folder": "/Lean/Data",
  "results-destination-folder": "/Results",

  "log-handler": "ConsoleLogHandler",
  "messaging-handler": "StreamingApi",
  "api-handler": "Api"
}
```

---

## 🔧 Usage

### Backtesting

```bash
# Run a backtest
docker-compose run --rm lean-engine \
  --config /Lean/Launcher/config.json \
  --algorithm-location /Lean/Algorithm/main.py
```

### Live Paper Trading

1. Edit `.env`:
   ```bash
   LEAN_MODE=live-paper
   LEAN_ENVIRONMENT=live-paper
   ```

2. Configure brokerage credentials in `.env`

3. Update `config/config.json` with brokerage settings

4. Run:
   ```bash
   docker-compose up -d
   ```

### Live Trading (Real Money)

⚠️ **WARNING: Live trading involves real money. Test thoroughly in paper mode first.**

1. Edit `.env`:
   ```bash
   LEAN_MODE=live
   LEAN_ENVIRONMENT=live
   ```

2. Update `config.json` with production brokerage credentials

3. Run:
   ```bash
   docker-compose up -d
   ```

### View Logs

```bash
# Real-time logs
docker-compose logs -f lean-engine

# Last 100 lines
docker-compose logs --tail=100 lean-engine
```

### Stop Services

```bash
# Stop gracefully
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes
docker-compose down -v
```

---

## 📦 Updating Dependencies

### Method 1: Using pip-compile (Recommended)

This ensures compatibility with the LEAN environment:

```bash
# 1. Edit requirements.in with your top-level dependencies
echo "scikit-learn>=1.3.0" >> requirements.in

# 2. Run pip-compile inside the base LEAN container
docker run --rm \
  -v $(pwd):/app \
  quantconnect/lean@sha256:YOUR_DIGEST \
  bash -c "pip install pip-tools && pip-compile /app/requirements.in -o /app/requirements.locked.txt"

# 3. Rebuild your image
docker-compose build --no-cache

# 4. Commit changes
git add requirements.in requirements.locked.txt
git commit -m "feat: add scikit-learn dependency"
```

### Method 2: Manual Pinning

```bash
# 1. Add dependency to requirements.locked.txt
echo "scikit-learn==1.3.2" >> requirements.locked.txt

# 2. Rebuild
docker-compose build --no-cache
```

---

## 🔄 Updating LEAN Version

When QuantConnect releases a new LEAN version:

### Step 1: Pull New Image

```bash
docker pull quantconnect/lean:latest
```

### Step 2: Get New Digest

```bash
NEW_DIGEST=$(docker image inspect quantconnect/lean:latest --format '{{index .RepoDigests 0}}' | cut -d'@' -f2)
echo "New digest: $NEW_DIGEST"
```

### Step 3: Update Configuration

**Option A: Update Dockerfile**
```dockerfile
ARG BASE_DIGEST="sha256:NEW_DIGEST_HERE"
```

**Option B: Update .env**
```bash
LEAN_BASE_DIGEST=sha256:NEW_DIGEST_HERE
```

### Step 4: Rebuild

```bash
docker-compose build --no-cache
```

### Step 5: Test

```bash
# Run tests in isolated environment
docker-compose run --rm lean-engine --config /Lean/Launcher/config.json
```

### Step 6: Commit and Tag

```bash
git add Dockerfile .env
git commit -m "chore: update LEAN to digest sha256:NEW_DIGEST"
git tag -a v1.1.0 -m "LEAN update to version X.Y.Z"
git push && git push --tags
```

---

## 🚀 Production Deployment

### 1. Build Production Image

```bash
# Build with production tag
docker build -t lean-locked:production -f Dockerfile .

# Tag with version
docker tag lean-locked:production lean-locked:1.0.0
```

### 2. Push to Private Registry

```bash
# Tag for your registry
docker tag lean-locked:1.0.0 your-registry.com/lean-locked:1.0.0

# Push
docker push your-registry.com/lean-locked:1.0.0
```

### 3. Deploy to Production Server

```bash
# On production server
docker pull your-registry.com/lean-locked:1.0.0

# Update docker-compose.yml
image: your-registry.com/lean-locked:1.0.0

# Deploy
docker-compose up -d
```

### 4. Kubernetes Deployment (Optional)

See `kubernetes/` directory for example manifests (coming soon).

---

## 🔍 Troubleshooting

### Issue: "Cannot connect to Docker daemon"

**Solution:**
```bash
# Start Docker service
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Issue: "Port already in use"

**Solution:**
```bash
# Find process using port
sudo lsof -i :8080

# Change port in .env
LEAN_API_PORT=8081
```

### Issue: "Permission denied" on volumes

**Solution:**
```bash
# Fix directory permissions
sudo chown -R $USER:$USER data/ results/ logs/

# Or run with sudo (not recommended)
sudo docker-compose up
```

### Issue: "Algorithm not found"

**Solution:**
```bash
# Check algorithm path in config.json
"algorithm-location": "/Lean/Algorithm/main.py"

# Ensure file exists in algorithms/ directory
ls -la algorithms/

# Check volume mount in docker-compose.yml
volumes:
  - ./algorithms:/Lean/Algorithm:ro
```

### Issue: Dependencies conflict

**Solution:**
```bash
# Regenerate locked requirements
docker run --rm -v $(pwd):/app quantconnect/lean@sha256:YOUR_DIGEST \
  bash -c "pip install pip-tools && pip-compile /app/requirements.in -o /app/requirements.locked.txt --resolver=backtracking"

# Rebuild clean
docker-compose build --no-cache --pull
```

---

## 🔒 Security Considerations

### Credentials Management

1. **NEVER commit `.env` file**
   - Always use `.env.example` as template
   - Store production credentials in secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)

2. **Use environment-specific configurations**
   ```bash
   # Development
   .env.development

   # Staging
   .env.staging

   # Production
   .env.production
   ```

3. **Rotate credentials regularly**
   - API tokens should be rotated every 90 days
   - Brokerage passwords should follow broker's security policy

### Container Security

1. **Read-only root filesystem** (optional)
   ```yaml
   read_only: true
   tmpfs:
     - /tmp
   ```

2. **Non-root user** (optional)
   ```dockerfile
   RUN useradd -m leanuser
   USER leanuser
   ```

3. **Resource limits**
   - Always set CPU and memory limits in production
   - Prevents resource exhaustion attacks

4. **Network isolation**
   - Use dedicated Docker networks
   - Implement firewall rules
   - Only expose necessary ports

---

## 📚 References

### Official Documentation

- [QuantConnect LEAN GitHub](https://github.com/QuantConnect/Lean)
- [QuantConnect Documentation](https://www.quantconnect.com/docs)
- [LEAN CLI Documentation](https://github.com/QuantConnect/lean-cli)

### Docker Best Practices

- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Docker Compose Production Guide](https://docs.docker.com/compose/production/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

### Related Tools

- [pip-tools](https://github.com/jazzband/pip-tools) - Python dependency management
- [Docker BuildKit](https://docs.docker.com/build/buildkit/) - Enhanced Docker builds
- [Hadolint](https://github.com/hadolint/hadolint) - Dockerfile linter

---

## 📝 License

This project follows the license of the parent Stock-Prediction-Models repository.

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📧 Support

For issues related to:
- **This Docker setup**: Open an issue in this repository
- **LEAN engine**: Visit [QuantConnect Forums](https://www.quantconnect.com/forum)
- **QuantConnect platform**: Contact [QuantConnect Support](https://www.quantconnect.com/contact)

---

<p align="center">
  <strong>Built with ❤️ for reproducible, production-grade algorithmic trading</strong>
</p>
