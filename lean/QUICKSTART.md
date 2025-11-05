# Quick Start Guide - LEAN Immutable Pod

Get up and running with a production-grade LEAN environment in 5 minutes.

## 🚀 5-Minute Setup

### Prerequisites

- Docker installed and running
- Docker Compose installed
- 8GB+ RAM available
- Internet connection

### Step 1: Get the Digest (2 minutes)

```bash
# Pull the official LEAN image
docker pull quantconnect/lean:latest

# Get the immutable digest
docker image inspect quantconnect/lean:latest --format '{{index .RepoDigests 0}}'
```

Copy the output (looks like: `quantconnect/lean@sha256:abc123...`)

### Step 2: Update Configuration (1 minute)

```bash
# Navigate to the lean directory
cd lean

# Update the Dockerfile with your digest
# Edit line 44: Replace the BASE_DIGEST value with your digest from Step 1
nano Dockerfile
```

Or use the helper script:
```bash
./scripts/update-digest.sh
```

### Step 3: Configure Environment (1 minute)

```bash
# Copy the environment template
cp .env.example .env

# Edit with your settings (optional for basic testing)
nano .env
```

Minimal changes needed:
- Leave defaults for testing
- Add API keys later for live trading

### Step 4: Build & Run (1 minute)

```bash
# Build the immutable image
docker-compose build

# Run a test
docker-compose up
```

That's it! Your immutable LEAN environment is running.

---

## 📝 Quick Examples

### Run the Example Algorithm

The example algorithm is already configured. Just:

```bash
docker-compose up
```

### Create Your Own Algorithm

```bash
# Create a new algorithm file
cat > algorithms/my_strategy.py << 'EOF'
from AlgorithmImports import *

class MyStrategy(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)
        self.AddEquity("SPY", Resolution.Daily)

    def OnData(self, data):
        if not self.Portfolio.Invested:
            self.SetHoldings("SPY", 1)
EOF

# Update config to use your algorithm
# Edit config/config.json:
# "algorithm-type-name": "MyStrategy"
# "algorithm-location": "/Lean/Algorithm/my_strategy.py"

# Run it
docker-compose up
```

### View Results

```bash
# Results are saved to the results/ directory
ls -la results/

# View logs
docker-compose logs -f lean-engine
```

---

## 🔧 Common Tasks

### Update Dependencies

```bash
# Add a new dependency to requirements.in
echo "scipy>=1.10.0" >> requirements.in

# Recompile locked requirements
./scripts/compile-requirements.sh

# Rebuild image
docker-compose build --no-cache
```

### Update LEAN Version

```bash
# Run the update script
./scripts/update-digest.sh

# Rebuild
docker-compose build --no-cache
```

### Debug Mode

```bash
# Run with interactive shell
docker-compose run --rm lean-engine /bin/bash

# Inside container, you can:
python --version
pip list
ls -la /Lean/
```

---

## 📚 What's Included

### Files Created

| File | Purpose |
|------|---------|
| `Dockerfile` | Immutable LEAN image definition |
| `docker-compose.yml` | Service orchestration |
| `requirements.in` | Top-level dependencies |
| `requirements.locked.txt` | Pinned dependency manifest |
| `.env.example` | Configuration template |
| `algorithms/example_algorithm.py` | Sample trading algorithms |
| `config/config.example.json` | LEAN configuration template |
| `scripts/update-digest.sh` | Helper to update base image |
| `scripts/compile-requirements.sh` | Helper to lock dependencies |

### Directories

| Directory | Purpose |
|-----------|---------|
| `algorithms/` | Your trading algorithms |
| `config/` | LEAN configuration files |
| `data/` | Market data cache (auto-created) |
| `results/` | Backtest results (auto-created) |
| `logs/` | Application logs (auto-created) |
| `scripts/` | Helper scripts |

---

## ⚠️ Troubleshooting

### "Cannot connect to Docker daemon"

```bash
# Start Docker
sudo systemctl start docker

# Or on Mac/Windows, start Docker Desktop
```

### "Port already in use"

```bash
# Change ports in .env
LEAN_DEBUG_PORT=5679
LEAN_API_PORT=8081
```

### "Permission denied"

```bash
# Fix permissions
chmod +x scripts/*.sh
sudo chown -R $USER:$USER .
```

### "Algorithm not found"

```bash
# Check your config.json
cat config/config.json | grep algorithm-location

# Ensure file exists
ls -la algorithms/
```

---

## 🎓 Next Steps

### For Learning

1. Read the full [README.md](README.md)
2. Try the example algorithms in `algorithms/example_algorithm.py`
3. Visit [QuantConnect Documentation](https://www.quantconnect.com/docs)
4. Join [QuantConnect Forum](https://www.quantconnect.com/forum)

### For Development

1. Add your own algorithms to `algorithms/`
2. Install your required Python packages via `requirements.in`
3. Customize `config/config.json` for your needs
4. Test with paper trading (`LEAN_MODE=live-paper`)

### For Production

1. Set up a private Docker registry
2. Configure production credentials in `.env`
3. Set resource limits in `docker-compose.yml`
4. Implement monitoring and alerting
5. Set up automated backups
6. Review security settings

---

## 📞 Getting Help

- **This Docker Setup**: Open an issue in this repo
- **LEAN Engine**: [QuantConnect Forum](https://www.quantconnect.com/forum)
- **Docker Issues**: [Docker Documentation](https://docs.docker.com/)

---

## ✅ Verification Checklist

Before going to production, verify:

- [ ] Digest is updated and committed
- [ ] All dependencies are locked in `requirements.locked.txt`
- [ ] `.env` file has production credentials (and is NOT committed)
- [ ] Resource limits are set appropriately
- [ ] Backups are configured
- [ ] Monitoring is in place
- [ ] Paper trading tests passed
- [ ] Security review completed

---

<p align="center">
  <strong>Happy Algorithmic Trading! 📈</strong>
</p>
