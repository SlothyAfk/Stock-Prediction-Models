# Interactive Pod Workflow

**Work directly inside the LEAN container - all commands run from within the pod.**

---

## 🎯 Philosophy

Instead of running one-off Docker commands from your host, this workflow gives you a **long-running interactive pod** that you log into and work from inside. All scripts, data, and configurations are mounted and available.

**Think of it like SSH-ing into a server** - but it's your local LEAN container.

---

## 🚀 Quick Start

### 1. Start the Pod

```bash
cd lean
docker-compose up -d
```

The container starts and stays running. All volumes are mounted.

### 2. Enter the Pod

```bash
docker-compose exec lean-engine bash
```

You're now inside the LEAN container!

### 3. Run the Helper Menu

```bash
/Lean/scripts/lean-helper.sh
```

This launches an interactive menu with all common tasks.

---

## 📦 What's Mounted

When you're inside the pod, everything is available:

| Host Path | Pod Path | Purpose |
|-----------|----------|---------|
| `./algorithms/` | `/Lean/Algorithm/` | Your trading algorithms |
| `./custom/` | `/Lean/Algorithm/custom/` | Custom extensions |
| `./config/` | `/Lean/config/` | Configuration files |
| `./scripts/` | `/Lean/scripts/` | Helper scripts |
| `./data/` | `/Lean/data/` | Market data |
| `./results/` | `/Results/` | Backtest results |
| `./logs/` | `/Lean/Logs/` | Application logs |
| `./storage/` | `/Lean/storage/` | Live trading state |

**All mounts are read-write** - changes inside the pod reflect on your host immediately.

---

## 🛠️ Common Workflows

### Download Market Data

```bash
# Inside the pod
cd /Lean/scripts

# Download default 10 tech stocks (last month, 5-min)
python download_yfinance_data.py

# Or customize
python download_yfinance_data.py \
  --tickers AAPL MSFT GOOGL \
  --period 2mo \
  --interval 5m
```

### List Downloaded Data

```bash
find /Lean/data/custom -name "*.csv" -exec ls -lh {} \;
```

### Run a Backtest

```bash
cd /Lean/Launcher/bin/Debug

# Run with custom config
dotnet QuantConnect.Lean.Launcher.dll \
  --config /Lean/config/config.custom.json
```

### Edit Your Algorithm

```bash
# Use nano (available in container)
nano /Lean/Algorithm/custom_data_alert_strategy.py

# Or edit on host (changes reflect immediately)
# Just open ./algorithms/custom_data_alert_strategy.py in your editor
```

### Check Python Packages

```bash
pip list | grep yfinance
python -c "import yfinance; print(yfinance.__version__)"
```

### View Results

```bash
ls -lh /Results/
cat /Results/*.json | jq '.'  # If jq installed
```

### Run Python Interactively

```bash
python
# Or if ipython is installed
ipython
```

```python
>>> import yfinance as yf
>>> data = yf.Ticker("AAPL").history(period="1d")
>>> print(data)
```

---

## 🎛️ Interactive Helper Menu

The `lean-helper.sh` script provides a menu-driven interface:

```bash
/Lean/scripts/lean-helper.sh
```

```
╔════════════════════════════════════════════════════════════╗
║           LEAN Algorithmic Trading Pod                    ║
║           Interactive Command Helper                      ║
╚════════════════════════════════════════════════════════════╝

Current Status:
  📂 Working Directory: /Lean/Launcher/bin/Debug
  🐍 Python Version: Python 3.11.x
  📦 Pip Location: /usr/local/bin/pip
  ⏰ Time Zone: America/New_York

Available Commands:

Data Management:
  1) Download market data (YFinance)
  2) List downloaded data
  3) Verify data files

Backtesting:
  4) Run backtest (custom strategy)
  5) Run backtest (example strategy)
  6) View last backtest results

Configuration:
  7) List configurations
  8) Edit algorithm
  9) Check Python packages

Development:
  10) Python shell (IPython if available)
  11) Run custom Python script

  s) Show status
  h) Show this help
  q) Quit

Enter choice:
```

---

## 📝 Step-by-Step: Complete Backtest

### From Outside the Pod

```bash
# 1. Start pod
docker-compose up -d

# 2. Enter pod
docker-compose exec lean-engine bash
```

### Now Inside the Pod

```bash
# 3. Download data
python /Lean/scripts/download_yfinance_data.py

# 4. Verify data downloaded
ls -lh /Lean/data/custom/aapl/

# 5. Check configuration
cat /Lean/config/config.custom.json

# 6. Run backtest
cd /Lean/Launcher/bin/Debug
dotnet QuantConnect.Lean.Launcher.dll --config /Lean/config/config.custom.json

# 7. Check results
ls -lh /Results/
```

### Back on Host

```bash
# View results (they're in ./results/)
ls -lh results/
cat results/*.json
```

---

## 🔧 Advanced Usage

### Multiple Terminal Sessions

You can have multiple terminals connected to the same pod:

```bash
# Terminal 1
docker-compose exec lean-engine bash
# Run backtest

# Terminal 2 (simultaneously)
docker-compose exec lean-engine bash
# Watch logs: tail -f /Lean/Logs/*.log

# Terminal 3
docker-compose exec lean-engine bash
# Edit algorithm
```

### Install Additional Packages

```bash
# Inside pod
pip install some-package

# But remember: Changes are lost when container restarts
# To persist, add to requirements.in and rebuild:
# (On host) Edit requirements.in
# (On host) docker-compose build --no-cache
# (On host) docker-compose up -d
```

### Run One-Off Commands Without Entering

```bash
# From host
docker-compose exec lean-engine python /Lean/scripts/download_yfinance_data.py

docker-compose exec lean-engine ls -lh /Lean/data/custom/

docker-compose exec lean-engine /Lean/scripts/lean-helper.sh status
```

### Copy Files In/Out

```bash
# Host to pod
docker cp ./my_algo.py lean-engine-locked:/Lean/Algorithm/

# Pod to host
docker cp lean-engine-locked:/Results/backtest.json ./
```

---

## 🔄 Common Commands Reference

### Pod Lifecycle

```bash
# Start pod
docker-compose up -d

# Stop pod
docker-compose stop

# Restart pod
docker-compose restart

# Stop and remove pod
docker-compose down

# Rebuild image
docker-compose build --no-cache

# View logs
docker-compose logs -f
docker-compose logs --tail=100
```

### Inside Pod

```bash
# Data download
python /Lean/scripts/download_yfinance_data.py

# Run backtest
cd /Lean/Launcher/bin/Debug && \
  dotnet QuantConnect.Lean.Launcher.dll --config /Lean/config/config.custom.json

# Helper menu
/Lean/scripts/lean-helper.sh

# Check environment
echo $PYTHONPATH
echo $TZ
python --version
pip list
```

### File Locations

```bash
# Algorithms
ls /Lean/Algorithm/
ls /Lean/Algorithm/custom/

# Data
ls /Lean/data/custom/

# Config
ls /Lean/config/

# Results
ls /Results/

# Logs
ls /Lean/Logs/

# Scripts
ls /Lean/scripts/
```

---

## 🐛 Troubleshooting

### Pod won't start

```bash
# Check logs
docker-compose logs lean-engine

# Check if port conflicts
docker ps

# Remove and restart
docker-compose down
docker-compose up -d
```

### Can't execute scripts

```bash
# Make sure scripts are executable (on host)
chmod +x scripts/*.sh
chmod +x scripts/*.py

# Or inside pod
chmod +x /Lean/scripts/*.sh
```

### Data not showing up

```bash
# Check volume mounts
docker inspect lean-engine-locked | grep -A 20 Mounts

# Verify on host
ls -la lean/data/custom/

# Verify in pod
docker-compose exec lean-engine ls -la /Lean/data/custom/
```

### Permission issues

```bash
# On host, fix ownership
sudo chown -R $USER:$USER lean/

# Inside pod, you're root by default
whoami  # Should show 'root'
```

---

## 💡 Pro Tips

### 1. Keep Pod Running

The pod stays running with `tail -f /dev/null`. This is intentional - you can log in/out freely without stopping it.

### 2. Edit Locally, Run in Pod

Edit files on your host machine with your favorite IDE/editor. Changes are immediately available in the pod because of volume mounts.

### 3. Use .bashrc

Create `/root/.bashrc` inside the pod for convenience:

```bash
# Inside pod
cat >> /root/.bashrc << 'EOF'
alias ll='ls -lah'
alias la='ls -A'
alias l='ls -CF'
alias cdalgo='cd /Lean/Algorithm'
alias cddata='cd /Lean/data'
alias cdscripts='cd /Lean/scripts'
alias cdlean='cd /Lean/Launcher/bin/Debug'

# Helpful prompt
PS1='\[\033[01;32m\]\u@lean-pod\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

# Quick commands
alias download='python /Lean/scripts/download_yfinance_data.py'
alias backtest='cd /Lean/Launcher/bin/Debug && dotnet QuantConnect.Lean.Launcher.dll'
alias helper='/Lean/scripts/lean-helper.sh'

echo "🚀 LEAN Pod Ready!"
echo "   Type 'helper' for interactive menu"
EOF

source /root/.bashrc
```

But remember: This is lost when container is recreated. To persist, add it to a mounted volume.

### 4. Use Screen/Tmux for Long-Running Backtests

```bash
# Install in Dockerfile or run:
apt-get update && apt-get install -y screen

# Start screen session
screen -S backtest

# Run backtest
cd /Lean/Launcher/bin/Debug
dotnet QuantConnect.Lean.Launcher.dll --config /Lean/config/config.custom.json

# Detach: Ctrl+A then D
# Reattach: screen -r backtest
```

---

## ✅ Checklist

Before running your first backtest:

- [ ] Pod is running: `docker-compose ps`
- [ ] Can exec in: `docker-compose exec lean-engine bash`
- [ ] Data is downloaded: `ls /Lean/data/custom/`
- [ ] Config exists: `cat /Lean/config/config.custom.json`
- [ ] Algorithm exists: `cat /Lean/Algorithm/custom_data_alert_strategy.py`
- [ ] Scripts are executable: `ls -l /Lean/scripts/`
- [ ] Python imports work: `python -c "import yfinance"`

---

## 🆚 Comparison: Interactive vs One-Off

### ❌ Old Way (One-Off Commands)

```bash
# Every command spins up a new container
docker-compose run --rm lean-engine python download.py
docker-compose run --rm lean-engine dotnet backtest.dll
docker-compose run --rm lean-engine ls /Results/

# Slow, verbose, disconnected
```

### ✅ New Way (Interactive Pod)

```bash
# One-time: Start pod
docker-compose up -d

# Use it many times
docker-compose exec lean-engine bash

# Inside: Fast, integrated, stateful
python download.py
dotnet backtest.dll
ls /Results/
```

---

## 🎓 Learning Path

1. **Start**: Get pod running and exec in
2. **Download**: Use helper menu or Python script to download data
3. **Run**: Execute a backtest with example strategy
4. **Modify**: Edit the algorithm and run again
5. **Custom**: Create your own strategy
6. **Advanced**: Add custom data providers, execution models, etc.

---

<p align="center">
  <strong>You're now ready to trade algorithms from inside your pod! 🚀📈</strong>
</p>
