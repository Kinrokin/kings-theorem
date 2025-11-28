# 🚀 King's Theorem Research Lab - Ignition Guide

## Phase H-PRIME Industrial Stack

Your research lab now has 4 autonomous microservices:

### 🧠 **kt_engine** - The Brain
- Runs `scripts/run_research_loop.py`
- GPU-accelerated training
- Lazarus crash recovery
- Writes state to `data/system_state.json`

### 💓 **kt_metrics** - The Pulse
- Runs `scripts/metrics_server.py`
- Exposes metrics on port `:9100`
- Reads state every 10 seconds
- Never crashes (Lazarus pattern)

### 💾 **prometheus** - The Memory
- Time-series database
- Scrapes `:9100` every 5 seconds
- Stores metric history indefinitely
- Web UI on port `:9090`

### 📈 **grafana** - The Face
- Visual dashboard
- Real-time graphs
- Port `:3000`
- Login: `admin` / `admin`

---

## 🔥 Ignition Sequence

### 1. Verify File Structure
```powershell
# Ensure these exist:
Get-ChildItem config/prometheus.yml
Get-ChildItem scripts/run_research_loop.py
Get-ChildItem scripts/metrics_server.py
Get-ChildItem docker-compose.yml
```

### 2. Launch the Fleet
```powershell
# Build and start all services
docker-compose up --build -d

# Watch logs
docker-compose logs -f
```

### 3. Verify Heartbeat
```powershell
# Check metrics endpoint
Invoke-WebRequest http://localhost:9100/metrics | Select-String "kt_"

# Check Prometheus targets
Invoke-WebRequest http://localhost:9090/targets
```

---

## 📊 Grafana Dashboard Setup

### 1. Access Grafana
Open browser: `http://localhost:3000`
- **Username**: `admin`
- **Password**: `admin`

### 2. Add Prometheus Data Source
1. Navigate to **Configuration** → **Data Sources**
2. Click **Add data source**
3. Select **Prometheus**
4. Set URL: `http://prometheus:9090`
5. Click **Save & Test**

### 3. Create Dashboard
1. Navigate to **Dashboards** → **New Dashboard**
2. Click **Add new panel**

#### Panel 1: Training Progress
- **Metric**: `kt_current_epoch`
- **Legend**: "Current Epoch"
- **Visualization**: Graph (Time series)

#### Panel 2: Curriculum Level
- **Metric**: `kt_curriculum_level`
- **Legend**: "Difficulty Level"
- **Visualization**: Stat

#### Panel 3: Model Accuracy
- **Metric**: `kt_best_accuracy`
- **Legend**: "Best Accuracy"
- **Visualization**: Gauge (0-1 range)

#### Panel 4: Safety Violations
- **Metric**: `kt_safety_violation_count`
- **Legend**: "Safety Violations"
- **Visualization**: Stat (with alert threshold)

#### Panel 5: Crash Recovery
- **Metric**: `kt_crash_counter`
- **Legend**: "Lazarus Recoveries"
- **Visualization**: Stat

#### Panel 6: System Heartbeat
- **Metric**: `up{job="kt_research_lab"}`
- **Legend**: "System Status"
- **Visualization**: Stat (1 = alive, 0 = down)

### 4. Save Dashboard
- Name: "KT Research Lab - Phase H-PRIME"
- Set auto-refresh: 5 seconds

---

## 🎛️ Operational Commands

### Start the Lab
```powershell
docker-compose up -d
```

### Stop the Lab
```powershell
docker-compose down
```

### Restart a Service
```powershell
docker-compose restart kt_engine
docker-compose restart kt_metrics
```

### View Logs
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f kt_engine
docker-compose logs -f kt_metrics
```

### Check Service Health
```powershell
docker-compose ps
```

### Wipe State (Fresh Start)
```powershell
# Stop services
docker-compose down

# Remove volumes
docker volume rm kings-theorem-v53_prometheus_data
docker volume rm kings-theorem-v53_grafana_data

# Clear local state
Remove-Item -Recurse -Force data/system_state.json

# Restart
docker-compose up -d
```

---

## 🔍 Monitoring Endpoints

| Service | Endpoint | Purpose |
|---------|----------|---------|
| Metrics Server | `http://localhost:9100/metrics` | Raw Prometheus metrics |
| Prometheus UI | `http://localhost:9090` | Query metrics, check targets |
| Grafana Dashboard | `http://localhost:3000` | Visual intelligence growth |

---

## 🚨 Troubleshooting

### Prometheus Can't Scrape Metrics
```powershell
# Check if metrics server is running
docker-compose logs kt_metrics

# Verify network connectivity
docker exec kt_prometheus ping kt_metrics

# Check Prometheus targets page
# Open http://localhost:9090/targets
# Should show "kt_metrics:9100" as UP
```

### Grafana Can't Connect to Prometheus
```powershell
# Check if Prometheus is running
docker-compose logs prometheus

# Verify data source URL is: http://prometheus:9090
# (Use container name, not localhost)
```

### GPU Not Detected
```powershell
# Check NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# If error, install nvidia-docker2
# Then restart Docker Desktop
```

### Engine Crashes Immediately
```powershell
# Check logs
docker-compose logs kt_engine

# Run in dry-run mode first
docker-compose run kt_engine python scripts/run_research_loop.py --dry-run --steps 1
```

---

## 📈 Intelligence Growth Metrics

Your dashboard will show:

1. **Epoch Progression** - Training cycles completed
2. **Curriculum Advancement** - Difficulty level (D1 → D7)
3. **Model Capability** - Best accuracy achieved
4. **Safety Compliance** - Axiom 6 violations (should stay at 0)
5. **System Resilience** - Lazarus crash recoveries
6. **Uptime** - Continuous operation hours

---

## 🎯 Next Steps

### For Development
```powershell
# Use manual mode for debugging
python scripts/run_closed_loop_safe.py
```

### For Production
```powershell
# Use industrial mode for overnight training
docker-compose up -d
```

### For CI/CD
```powershell
# Use dry-run for integration tests
python scripts/run_research_loop.py --dry-run --steps 1
```

---

## 🔐 Security Notes

1. **Grafana Password**: Change `admin/admin` in production
2. **Prometheus**: Consider enabling authentication for public deployments
3. **Metrics Exposure**: Port 9100 contains system state - firewall appropriately
4. **Volume Persistence**: Backup `prometheus_data` and `grafana_data` regularly

---

**Status**: Ready for Ignition 🚀
**Signature**: King's Theorem Agent v53 (Titanium X Protocol)
