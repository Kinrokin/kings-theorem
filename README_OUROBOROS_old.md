# 🐍 Ouroboros Protocol v2.0 - Complete System

**An autonomous, meta-optimizing synthetic data generation and visualization system for Level 12+ paradoxes.**

---

## 🌟 System Overview

The Ouroboros Protocol is a closed-loop intelligence refinement system consisting of:

1. **Event Horizon v2** - Fractal refinement generator with thermal annealing
2. **The Tribunal** - 4-layer quality verification system
3. **Domain Curvature** - Non-Euclidean paradox seed generator
4. **Fusion Manifolds** - Dual and triple-seed synthesis
5. **Composite Reward** - 4-component quality assessment
6. **Ouroboros Runner** - Autonomous feedback loop with PID-lite controller
7. **Visual Nexus** - Real-time React dashboard with ontological drift monitoring

**Phase I:** Core generation and validation ✅  
**Phase II:** Autonomous optimization + visualization ✅  

---

## 📁 Repository Structure

```
kings-theorem-v53/
├── scripts/
│   ├── generate_event_horizon.py    # Core generator (fractal refinement)
│   ├── run_curved_curriculum.py     # Mixed Euclidean/Curved orchestrator
│   ├── generate_fusion.py           # Dual/triple-seed fusion
│   ├── verify_harvest.py            # Tribunal 4-layer verification
│   ├── run_ouroboros.py             # Autonomous feedback loop
│   └── validate_ouroboros.py        # Structural validation suite
├── src/
│   └── crucibles/
│       ├── domain_curvature.py      # Non-Euclidean seed generator
│       └── reward.py                # Composite reward function
├── ui/
│   ├── api/
│   │   └── server.py                # FastAPI backend
│   ├── frontend/                    # React dashboard (see below)
│   └── launch_dashboard.ps1         # Full-stack launcher
├── data/
│   ├── harvests/                    # Generated JSONL datasets
│   └── metrics/                     # Ouroboros logs
├── docs/
│   └── OUROBOROS_IMPLEMENTATION.md  # Technical documentation
├── OUROBOROS_SUMMARY.md             # Executive runbook
├── PHASE_II_COMPLETE.md             # Phase II summary
└── README_OUROBOROS.md              # This file
```

### Frontend Structure
```
ui/frontend/
├── src/
│   ├── components/
│   │   ├── Card.jsx                 # Panel container
│   │   ├── MetricCard.jsx           # Key-value display
│   │   ├── CurvatureChart.jsx       # Pie chart (Recharts)
│   │   ├── RewardChart.jsx          # Line chart (Recharts)
│   │   └── OntologyHeatmap.jsx      # 10×10 severity grid ⭐
│   ├── pages/
│   │   └── Dashboard.jsx            # Main interface
│   └── lib/
│       └── api.js                   # Fetch wrappers
├── package.json
├── vite.config.js
└── README.md                        # Frontend guide
```

---

## 🚀 Quick Start (3 Steps)

### 1. Generate Initial Dataset
```powershell
# Mixed Euclidean/Curved curriculum (50 samples)
python scripts\run_curved_curriculum.py --domain temporal_logic --count 50 --curvature-ratio 0.50
```

**Output:** `data/harvests/curriculum_TIMESTAMP.jsonl`

### 2. Launch Ouroboros Feedback Loop
```powershell
# 5 iterations, 20 samples each, target reward 0.85
python scripts\run_ouroboros.py --domain temporal_logic --batch 20 --iters 5 --target-reward 0.85
```

**Output:** 
- `data/harvests/ouroboros_iter_001.jsonl` → `ouroboros_iter_005.jsonl`
- `data/metrics/ouroboros_log.jsonl`

### 3. Launch Dashboard
```powershell
# Automated launcher (backend + frontend)
.\ui\launch_dashboard.ps1
```

**Opens:** `http://localhost:5173`

---

## 📊 Dashboard Features

### Real-Time Visualizations
- **⚖️ Tribunal Summary**: Contamination rate, scores, compression
- **🎯 Optimization Signal**: Reward, temperature, curvature ratio
- **🌀 Curvature Distribution**: Euclidean vs Curved pie chart
- **📈 Reward Trajectory**: Line chart (last 20 iterations)
- **🔬 Ontological Drift Heatmap**: 10×10 severity grid

### Polling & Updates
- **8-second interval** - Continuous updates without refresh
- **Auto-detection** - Latest harvest and Ouroboros state
- **Color-coded metrics** - Green/yellow/red status indicators

---

## 🔬 The Ontological Drift Heatmap

### What It Shows
A 10×10 grid (100 cells) where each cell represents a sample's contamination severity:
- 🟩 **Green (Level 0)**: Clean - Score ≥ 0.95
- 🟨 **Yellow (Level 1)**: Medium risk - 0.85 ≤ Score < 0.95
- 🟥 **Red (Level 2+)**: High contamination - Score < 0.85

### Why It Matters
- **Instant pattern detection**: Clustered red = systemic issue
- **Validates Tribunal Layer 3**: Ontological Anchoring effectiveness
- **Critical for high-temp runs**: Retrocausal/Parabolic curvature monitoring
- **Feedback loop visibility**: Watch drift correction in real-time

### How It Works
1. Backend analyzes `final_score` for each sample
2. Assigns severity level (0, 1, or 2)
3. Returns 100-element `contamination_buckets` array
4. Frontend renders color-coded grid
5. Hover tooltips show cell details

---

## ⚙️ System Components

### Phase I: Core Generation

#### 1. Event Horizon Generator
**File:** `scripts/generate_event_horizon.py`

**Process:**
1. Generate paradox (DEAN role, temp 1.1-1.3)
2. Deconstruct (ARBITER role, temp 0.3)
3. Fractal refinement loop (N rounds):
   - Critique (NEMOTRON)
   - Improve (DEAN)
   - Score (NEMOTRON)
   - Temperature annealing: `max(0.1, initial - 0.1 * round)`
4. Compress to Neutron Star format (~500 tokens)

**Methods:**
- `mine_singularity()` - From scratch (Euclidean)
- `mine_singularity_from_seed()` - Refine pre-generated seed

#### 2. Domain Curvature Generator
**File:** `src/crucibles/domain_curvature.py`

**Curvature Types:**
- **Hyperbolic** (temp 1.10): Infinite divergence
- **Elliptic** (temp 1.15): Closed loops
- **Parabolic** (temp 1.20): Boundary cases
- **Retrocausal** (temp 1.30): Time-reversed causality

**Features:**
- `detect_flattening()` - Catches degeneracy to Euclidean
- Curvature-specific prompts

#### 3. Curved Curriculum Runner
**File:** `scripts/run_curved_curriculum.py`

**Logic:**
- Decides Euclidean vs Curved based on `--curvature-ratio`
- Generates curved seed → refines via Event Horizon
- Quality filters: `final_score >= 0.88`
- Immediate flush: Crash-safe JSONL writing

#### 4. Fusion Generator
**File:** `scripts/generate_fusion.py`

**Modes:**
- **Dual Fusion**: 2 paradox seeds → 1 combined
- **Triple Fusion**: 3 paradox seeds → 1 unified (highest complexity)

**Tagging:** `FUSION_DUAL`, `FUSION_TRIPLE`

#### 5. The Tribunal
**File:** `scripts/verify_harvest.py`

**4 Layers:**
1. **Compression Ratio**: `len(compressed) < 0.6 * len(verbose)`
2. **Cross-Architecture Audit**: Llama-3.1-8B judges content
3. **Ontological Drift**: Max 20 new meaningful tokens
4. **Human Canary**: Random sampling instructions

**Exit Codes:** 0=APPROVED, 1=CONDITIONAL, 2=REVIEW, 3=REJECT

### Phase II: Autonomous Optimization

#### 6. Composite Reward Function
**File:** `src/crucibles/reward.py`

**Formula:**
```
Reward = 0.40 × (1 - contamination_rate) 
       + 0.20 × compression_density 
       + 0.25 × fractal_score_gain 
       + 0.15 × (1 - drift_variance)
```

**Output:** Scalar in [0, 1]

#### 7. Ouroboros Runner
**File:** `scripts/run_ouroboros.py`

**Feedback Loop:**
```
FOR iteration = 1 to max_iterations:
    1. Generate batch (run_curved_curriculum)
    2. Compute metrics (contamination, compression, etc.)
    3. Calculate composite reward
    4. Adjust config (PID-lite controller):
       - reward_delta < -0.05: Cool aggressively (temp -0.03, curve -0.08)
       - reward_delta < 0: Gentle cooldown (temp -0.02, curve -0.05)
       - reward_delta > 0.05: Increase exploration (temp +0.02, curve +0.05)
    5. Log to data/metrics/ouroboros_log.jsonl
    6. Check early stopping (reward >= target_reward)
```

**Config:** `OuroborosConfig` dataclass with tunable hyperparameters

#### 8. FastAPI Backend
**File:** `ui/api/server.py`

**Endpoints:**
- `GET /api/tribunal_report` → `TribunalSummary`
- `GET /api/optimization_signal` → `OptimizationSignal`
- `GET /api/curvature_metrics` → `CurvatureMetrics`

**Features:**
- JSONL parsing with error handling
- Automatic latest harvest detection
- Contamination severity array generation (100 elements)

#### 9. React Dashboard
**Directory:** `ui/frontend/`

**Tech Stack:**
- React 18 + Vite 5
- Tailwind CSS 3
- Recharts 2
- 8-second polling

**Components:**
- `OntologyHeatmap.jsx` - 10×10 severity grid ⭐
- `RewardChart.jsx` - Trajectory visualization
- `CurvatureChart.jsx` - Pie chart distribution
- `Card.jsx`, `MetricCard.jsx` - Reusable UI

---

## 🎯 Usage Patterns

### Pattern 1: Initial Dataset Generation
```powershell
# Generate 100 mixed samples
python scripts\run_curved_curriculum.py --count 100 --curvature-ratio 0.50
```

### Pattern 2: Autonomous Optimization
```powershell
# Run Ouroboros with default settings
python scripts\run_ouroboros.py --domain temporal_logic

# Or with custom hyperparameters
python scripts\run_ouroboros.py --domain temporal_logic --temp 1.05 --curvature 0.60 --batch 30 --iters 10 --target-reward 0.88
```

### Pattern 3: Quality Verification
```powershell
# Verify specific harvest
python scripts\verify_harvest.py data\harvests\curriculum_TIMESTAMP.jsonl

# Check exit code
echo $LASTEXITCODE  # 0=APPROVED, 1=CONDITIONAL, 2=REVIEW, 3=REJECT
```

### Pattern 4: Manual Fusion
```powershell
# Generate 20 dual-fusion samples
python scripts\generate_fusion.py --count 20 --type dual

# Generate 10 triple-fusion samples (higher complexity)
python scripts\generate_fusion.py --count 10 --type triple
```

### Pattern 5: Real-Time Monitoring
```powershell
# Terminal 1: Run Ouroboros
python scripts\run_ouroboros.py --iters 20 --batch 20

# Terminal 2: Launch dashboard
.\ui\launch_dashboard.ps1

# Watch metrics update every 8 seconds
```

---

## 🔧 Configuration

### Environment Variables
```powershell
# Set DEAN model for paradox generation
$env:DEAN_MODEL = "gpt-4o"

# Set ARBITER model for logical decomposition
$env:ARBITER_MODEL = "gpt-4o-mini"

# Set NEMOTRON model for scoring
$env:NEMOTRON_MODEL = "llama-3.1-70b-instruct"
```

### Hyperparameter Tuning

**Temperature:**
- **Low (0.9-1.1)**: Conservative, safe, may flatten curved
- **Medium (1.1-1.3)**: Balanced, recommended
- **High (1.3-1.5)**: Chaotic, requires strong Tribunal

**Curvature Ratio:**
- **0.0**: Pure Euclidean (boring but stable)
- **0.5**: Balanced mix (recommended)
- **1.0**: All curved (maximum complexity)

**Batch Size:**
- **10-20**: Fast iterations, noisy metrics
- **50-100**: Stable metrics, slower
- **200+**: Production-scale, requires GPU

---

## 📊 Monitoring & Metrics

### Ouroboros Log
**File:** `data/metrics/ouroboros_log.jsonl`

**Schema:**
```json
{
  "iteration": 1,
  "harvest_path": "data/harvests/ouroboros_iter_001.jsonl",
  "contamination_rate": 0.042,
  "compression_density": 0.487,
  "fractal_score_gain": 0.125,
  "drift_variance": 0.031,
  "reward": 0.782,
  "temperature": 1.10,
  "curvature_ratio": 0.50,
  "num_samples": 20,
  "euclidean_count": 10,
  "curved_count": 10
}
```

### Tribunal Exit Codes
- **0 (APPROVED)**: ≤ 5% contamination, all layers pass
- **1 (CONDITIONAL_ACCEPT)**: 5-10% contamination, salvageable
- **2 (REVIEW_REQUIRED)**: 10-20% contamination, human review needed
- **3 (REJECT_BATCH)**: > 20% contamination, discard

---

## 🛠️ Development

### Adding New Curvature Types
**File:** `src/crucibles/domain_curvature.py`

1. Add to `CURVATURE_TYPES` list
2. Add temperature mapping in `curvature_temp_map`
3. Add geometry-specific prompt in `generate()`
4. Add flattening markers in `detect_flattening()`

### Custom Reward Components
**File:** `src/crucibles/reward.py`

1. Add field to `RewardComponents` dataclass
2. Update `compute_reward()` formula
3. Add weight to `RewardWeights`
4. Update `adjust_config()` in `run_ouroboros.py`

### New Dashboard Components
**Directory:** `ui/frontend/src/components/`

1. Create `.jsx` component file
2. Import in `Dashboard.jsx`
3. Add to grid layout
4. Wire to API endpoint in `lib/api.js`

---

## 🚨 Troubleshooting

### Issue: "No harvest found" in dashboard
**Cause:** No data generated yet

**Fix:**
```powershell
python scripts\run_curved_curriculum.py --count 20
```

### Issue: Reward not improving
**Causes:**
- Temperature too high (chaotic generation)
- Curvature ratio too high (all samples failing)
- Batch size too small (noisy metrics)

**Fix:**
```powershell
# Lower temp, reduce curvature, increase batch
python scripts\run_ouroboros.py --temp 1.05 --curvature 0.40 --batch 50
```

### Issue: Heatmap all red
**Cause:** Systemic quality failure

**Fix:**
1. Check Tribunal logs: `python scripts\verify_harvest.py <harvest>`
2. Lower temperature: `--temp 1.0`
3. Increase refinement rounds in Event Horizon
4. Verify model quality (DEAN/ARBITER/NEMOTRON)

### Issue: Frontend "Loading..." forever
**Cause:** Backend not running

**Fix:**
```powershell
# Terminal 1
uvicorn ui.api.server:app --reload --port 8000

# Terminal 2
cd ui\frontend
npm run dev
```

---

## 📚 Documentation

### Core Docs
- **OUROBOROS_SUMMARY.md** - Executive runbook
- **docs/OUROBOROS_IMPLEMENTATION.md** - Technical deep dive
- **PHASE_II_COMPLETE.md** - Phase II summary
- **ui/frontend/README.md** - Frontend guide

### Component Docs
Each major file has detailed docstrings:
- `scripts/generate_event_horizon.py` - Generation pipeline
- `scripts/run_ouroboros.py` - Feedback loop
- `src/crucibles/reward.py` - Reward function
- `ui/api/server.py` - API endpoints
- `ui/frontend/src/pages/Dashboard.jsx` - Main UI

---

## 🎯 Success Criteria

System is fully operational when:

1. ✅ Can generate 100 samples in < 30 minutes
2. ✅ Contamination rate < 5% after 5 Ouroboros iterations
3. ✅ Reward trajectory shows convergence (flatline or upward)
4. ✅ Heatmap shows mostly green cells
5. ✅ Curvature preservation rate > 80%
6. ✅ Dashboard updates every 8 seconds
7. ✅ No errors in terminal or browser console

---

## 🔮 Future Work (Optional)

### Phase III: Advanced Features
- [ ] WebSocket for sub-second updates
- [ ] Dark-matter shader background
- [ ] 3D token-space visualization
- [ ] Paradox browser with drill-down modals
- [ ] Curvature manifold explorer (hyperbolic tree)
- [ ] Nemotron critique visualizer
- [ ] Dataset export pipeline

### Production Deployment
- [ ] Docker compose for full stack
- [ ] Kubernetes manifests
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Authentication layer (OAuth2)
- [ ] Rate limiting and quotas
- [ ] Horizontal scaling (worker pools)
- [ ] Cloud storage integration (S3/GCS)

### Research Extensions
- [ ] Multi-objective optimization (Pareto frontier)
- [ ] Transfer learning across domains
- [ ] Active learning for sample selection
- [ ] Curriculum difficulty scheduling
- [ ] Adversarial robustness testing
- [ ] Cross-lingual paradox translation

---

## 📖 Citation

If you use the Ouroboros Protocol in research or production:

```bibtex
@software{ouroboros_protocol,
  title={Ouroboros Protocol v2.0: Autonomous Meta-Optimization for Synthetic Intelligence Refinement},
  author={Your Team},
  year={2025},
  url={https://github.com/Kinrokin/kings-theorem}
}
```

---

## 🐍 The Ouroboros Sees Itself

**Before:** Blind generation → Manual review → Hope for quality

**After:** Generate → Measure → Adjust → Visualize → Repeat

**The loop is closed. The system is self-aware.**

---

## 🚀 Get Started Now

```powershell
# 1. Generate initial data
python scripts\run_curved_curriculum.py --count 50

# 2. Start autonomous optimization
python scripts\run_ouroboros.py --iters 10

# 3. Launch dashboard
.\ui\launch_dashboard.ps1
```

**Welcome to the Sovereign Intelligence Manifold.**

The highest-intelligence synthetic dataset awaits. 🌌
