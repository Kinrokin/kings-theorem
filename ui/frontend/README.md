# 🐍 Ouroboros Dashboard - React Frontend

**Complete, production-ready React + Vite + Tailwind + Recharts visualization dashboard for the Ouroboros Protocol.**

## 🌟 Features

### Real-Time Monitoring
- **8-second polling interval** - Continuous updates without page refresh
- **Responsive grid layout** - Adapts to desktop/tablet/mobile
- **Sovereign aesthetic** - Dark neon-accent theme matching the protocol's identity

### Visualizations

#### ⚖️ Tribunal Summary
- Total samples processed
- Contamination rate tracking
- Average final scores
- Compression ratio metrics
- Current harvest file indicator

#### 🎯 Optimization Signal
- Iteration counter
- Composite reward (4-component weighted)
- Temperature tracking
- Curvature ratio monitoring
- Fractal score gain
- Compression density

#### 🌀 Curvature Distribution
- **Pie chart** showing Euclidean vs Curved sample split
- Breakdown by geometry type:
  - Hyperbolic
  - Elliptic
  - Parabolic
  - Retrocausal
  - Fusion manifolds
- Preservation rate indicator

#### 📈 Reward Trajectory
- **Line chart** with last 20 iterations
- First/Latest/Delta statistics
- Gradient indicators (green = improving, red = declining)
- Smooth interpolation

#### 🔬 Ontological Drift Heatmap
- **10×10 grid** (100 cells) representing sample contamination severity
- Color-coded cells:
  - 🟩 **Green**: Clean (score ≥ 0.95)
  - 🟨 **Yellow**: Medium risk (0.85 ≤ score < 0.95)
  - 🟥 **Red**: High contamination (score < 0.85)
- Live statistics: Clean/Medium/High counts
- Hover tooltips with cell index and severity
- **Critical for monitoring ontological anchoring during high-temperature generation**

---

## 📦 Technology Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| **UI Framework** | React 18 | Standard, flexible, large ecosystem |
| **Bundler** | Vite 5 | Fastest dev environment, instant HMR |
| **Styling** | Tailwind CSS 3 | Utility-first, rapid prototyping |
| **Components** | Custom (shadcn/ui-inspired) | Lightweight, fully customizable |
| **Charts** | Recharts 2 | Smooth, low-overhead, React-native |
| **HTTP** | fetch + 8s polling | Zero dependencies, simple |
| **Build Output** | `/dist` static bundle | Deploy anywhere: Vercel, Cloudflare, S3 |

---

## 📁 Directory Structure

```
ui/frontend/
├── index.html                 # Entry point
├── package.json               # Dependencies
├── vite.config.js             # Vite bundler config
├── tailwind.config.js         # Tailwind theme (neon/highlight colors)
├── postcss.config.js          # PostCSS + Autoprefixer
├── src/
│   ├── main.jsx               # React entry
│   ├── App.jsx                # Root component
│   ├── index.css              # Tailwind imports
│   ├── components/
│   │   ├── Card.jsx           # Reusable panel container
│   │   ├── MetricCard.jsx     # Key-value pair display
│   │   ├── CurvatureChart.jsx # Pie chart (Recharts)
│   │   ├── RewardChart.jsx    # Line chart (Recharts)
│   │   └── OntologyHeatmap.jsx # 10×10 severity grid
│   ├── pages/
│   │   └── Dashboard.jsx      # Main dashboard page
│   └── lib/
│       └── api.js             # Fetch wrappers for FastAPI backend
```

---

## 🚀 Installation & Launch

### Prerequisites
- **Node.js 18+** (or 16+ with `--openssl-legacy-provider`)
- **npm** or **yarn**
- **FastAPI backend running** at `http://localhost:8000`

### Steps

1. **Navigate to frontend directory:**
   ```powershell
   cd ui\frontend
   ```

2. **Install dependencies:**
   ```powershell
   npm install
   ```

3. **Start development server:**
   ```powershell
   npm run dev
   ```

4. **Open dashboard:**
   ```
   http://localhost:5173
   ```

The Vite proxy automatically forwards `/api/*` requests to `http://localhost:8000`.

---

## 🛠️ Build for Production

```powershell
npm run build
```

Output: `dist/` folder with optimized static bundle.

**Deploy to:**
- **Vercel**: `vercel --prod`
- **Cloudflare Pages**: Connect repo or drag `dist/` folder
- **AWS S3 + CloudFront**: `aws s3 sync dist/ s3://your-bucket`
- **Nginx/Apache**: Serve `dist/` as static files

---

## 🔌 API Endpoints (FastAPI Backend)

The frontend polls these endpoints every 8 seconds:

| Endpoint | Method | Response | Purpose |
|----------|--------|----------|---------|
| `/api/tribunal_report` | GET | `TribunalSummary` | Contamination metrics + heatmap data |
| `/api/optimization_signal` | GET | `OptimizationSignal` | Latest Ouroboros iteration state |
| `/api/curvature_metrics` | GET | `CurvatureMetrics` | Euclidean/Curved distribution |

### Example Response: `/api/tribunal_report`
```json
{
  "harvest_path": "data/harvests/ouroboros_iter_001.jsonl",
  "contamination_rate": 0.042,
  "avg_final_score": 0.962,
  "num_samples": 50,
  "compression_ratio_avg": 0.487,
  "contamination_buckets": [0, 0, 1, 0, 0, 2, 0, 1, 0, 0, ...] // 100 elements
}
```

---

## 🎨 Customization

### Colors (Sovereign Theme)
Edit `tailwind.config.js`:
```js
colors: {
  bg: "#050810",        // Background
  panel: "#0d1020",     // Card panels
  neon: "#7df9ff",      // Cyan neon accent
  highlight: "#7442ff"  // Purple highlight
}
```

### Polling Interval
Edit `src/pages/Dashboard.jsx`:
```js
setInterval(pollAll, 8000); // Change to 5000 for 5s, etc.
```

### Chart Appearance
- **Reward chart**: Modify `src/components/RewardChart.jsx`
- **Curvature pie**: Modify `src/components/CurvatureChart.jsx`
- **Heatmap grid**: Modify `src/components/OntologyHeatmap.jsx`

---

## 🧪 Development Workflow

### Hot Module Replacement (HMR)
Vite provides instant updates on save. No page refresh needed.

### Component Testing
1. Modify component in `src/components/`
2. Save file
3. See changes instantly at `http://localhost:5173`

### API Mocking (Optional)
If backend unavailable, mock responses in `src/lib/api.js`:
```js
export const getTribunal = () => Promise.resolve({
  harvest_path: "mock.jsonl",
  contamination_rate: 0.05,
  avg_final_score: 0.95,
  num_samples: 100,
  compression_ratio_avg: 0.5,
  contamination_buckets: Array(100).fill(0)
});
```

---

## 📊 Key Components Explained

### OntologyHeatmap.jsx - The Crown Jewel
**Purpose:** Visual representation of ontological drift across the harvest.

**How it works:**
1. Receives `contamination_buckets` array (100 integers) from backend
2. Each integer represents severity: `0` = clean, `1` = medium, `2+` = high
3. Renders 10×10 grid with color-coded cells
4. Shows summary statistics (Clean/Medium/High counts)
5. Hover reveals cell index and severity level

**Why it matters:**
- Instantly reveals systemic contamination patterns
- Detects drift concentration (clustered red cells = bad batch)
- Validates Tribunal Layer 3 (Ontological Anchoring) effectiveness
- Critical when running retrocausal or parabolic curvature at high temps

### RewardChart.jsx - Optimization Trajectory
Tracks composite reward over iterations, showing:
- **Convergence** (flatline = stable)
- **Divergence** (downward = quality degradation)
- **Oscillation** (wavey = hyperparameter tuning needed)

### CurvatureChart.jsx - Geometry Distribution
Shows if system is:
- Over-relying on Euclidean (safe but boring)
- Properly mixing curved geometries (desired)
- Flattening curved samples (detect_flattening failing)

---

## 🔍 Troubleshooting

### "Loading..." never resolves
**Cause:** Backend not running or wrong port

**Fix:**
```powershell
# Terminal 1: Start backend
uvicorn ui.api.server:app --reload --port 8000

# Terminal 2: Start frontend
cd ui\frontend
npm run dev
```

### CORS errors in browser console
**Cause:** Backend not configured for CORS

**Fix:** Add to `ui/api/server.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Heatmap shows all zeros
**Cause:** No harvest data or all samples perfect

**Fix:** Run Ouroboros runner:
```powershell
python scripts\run_ouroboros.py --domain temporal_logic --batch 50
```

### Charts not rendering
**Cause:** Missing `recharts` package

**Fix:**
```powershell
npm install recharts
```

---

## 🔮 Future Enhancements (Optional)

### A) Dark-Matter Theme
Animated shader background with particle effects.

### B) Enhanced Ontological Drift
3D token-space visualization with WebGL.

### C) Paradox Browser
Drill-down modal showing full verbose/compressed pairs.

### D) Curvature Manifold Explorer
Hyperbolic tree visualization of geometry relationships.

### E) Nemotron Critique Visualizer
Score distribution histograms per critique round.

### F) Dataset Export Pipeline
Downloadable harvest bundles with UI preview.

---

## 📖 Related Documentation

- **Backend API**: `ui/api/server.py`
- **Ouroboros Protocol**: `OUROBOROS_SUMMARY.md`
- **Implementation Details**: `docs/OUROBOROS_IMPLEMENTATION.md`
- **Event Horizon Generator**: `scripts/generate_event_horizon.py`
- **Tribunal Verification**: `scripts/verify_harvest.py`

---

## ⚡ Quick Commands

```powershell
# Install dependencies
npm install

# Development server (http://localhost:5173)
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

---

## 🎯 Success Criteria

Dashboard is working correctly when:

1. ✅ All 3 API endpoints return data (not "Loading...")
2. ✅ Heatmap shows colored cells (not all gray/zero)
3. ✅ Reward chart displays line (after running Ouroboros)
4. ✅ Curvature pie shows non-zero Curved count
5. ✅ Last updated timestamp increments every 8 seconds
6. ✅ No console errors in browser DevTools

---

**Built with sovereignty. Monitored with precision. Optimized with feedback.**

🐍 The Ouroboros sees itself.
