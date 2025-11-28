# 🏛️ KING'S THEOREM — SOVEREIGN INTERFACE v2.0

**Constitutional Cockpit for AI Governance**

---

## What This Is

This is **not** a dashboard.  
This is **not** a chat interface.  
This is **not** a web UI.

This is a **governance instrument**.

A **constitutional cockpit** for operating King's Theorem's Council of Teachers.

---

## Philosophical Foundation

The Sovereign Interface is built on five constitutional principles:

### 1. **The Oculus = Tribunal Lens**
The animated eye represents the living state of the Council's deliberation.
It is not decoration—it is the **heartbeat of judicial AI**.

### 2. **The Warrant = Constitutional Input**
You do not "ask questions." You **issue warrants**.  
A warrant is a constitutional command that the Council **must** evaluate under axioms.

### 3. **The Decree = Judicial Output**
The Council does not "respond." It **issues decrees**.  
Every decree is traceable, auditable, and constitutionally bound.

### 4. **The Ledger = Scar Tissue Archive**
Every interaction is permanently inscribed.  
The Ledger is not a log—it is **scar tissue**.  
It proves the system's decisions under adversarial pressure.

### 5. **The Veto = Constitutional Strike**
When axioms are violated, the system does not "error."  
It **VETOs**.  
The screen cuts to black. The interface freezes for 2 seconds.  
This is not a bug—it is **constitutional governance**.

---

## Architecture

### State Machine (Constitutional Transitions)

```
IDLE → THINKING → SYNTHESIZING → DECREE → IDLE
                       ↓              ↓
                    VETO          ERROR
                       ↓              ↓
                   FREEZE         IDLE
```

**Illegal state transitions trigger automatic VETO.**

### Visual Components

| Element | Purpose | State Binding |
|---------|---------|---------------|
| **Oculus** | Tribunal Eye | Animates based on system state (thinking/synthesizing/decree/veto) |
| **CVaR Bar** | Risk Telemetry | Shows system risk topology in real-time |
| **Status Strip** | Heartbeat | Displays current state with color-coded indicator |
| **Hash Pill** | Decree Fingerprint | Shows cryptographic hash of current decree |
| **Mode Chips** | Council Channel | Selects DEAN/ENGINEER/ARBITER/TA routing |
| **Warrant Parchment** | Constitutional Input | Multi-line textarea for issuing commands |
| **Decree Area** | Response Viewport | Markdown-rendered decree with navigation |
| **Ledger** | Archive Navigator | Chronological clickable history |

---

## Keyboard Shortcuts (Constitutional UX)

| Shortcut | Action |
|----------|--------|
| **Ctrl+Enter** | Issue Warrant (submit) |
| **Ctrl+K** | Focus Warrant input |
| **Esc** | Clear input OR hide response |
| **Ctrl+Shift+[** | Previous decree (time travel) |
| **Ctrl+Shift+]** | Next decree (time travel) |
| **↑ (ArrowUp)** | Recall last warrant |

---

## Council Modes

### DEAN (Deep Reasoning)
- **Models**: O1-mini, DeepSeek R1, Claude 3.7, GPT-4o
- **Purpose**: Level 10 paradoxes, logic, ethics, complex reasoning
- **Temperature**: 0.8 (creative)

### ENGINEER (Technical Implementation)
- **Models**: Claude 3.5, Mistral Large, Llama 405B, Qwen 2.5 Coder
- **Purpose**: Code, architecture, optimization, technical solutions
- **Temperature**: 0.7 (balanced)

### ARBITER (Judgment & Safety)
- **Models**: Nemotron-70B, GPT-4o, Gemini Pro 1.5
- **Purpose**: Grading, safety checks, evaluation, arbitration
- **Temperature**: 0.1 (consistent)

### TA (Teaching Assistant)
- **Models**: Llama 3.3, DeepSeek Chat, Gemini Flash, Claude Haiku
- **Purpose**: Speed tasks, formatting, summaries, simplifications
- **Temperature**: 0.7 (balanced)

---

## VETO vs ERROR (Constitutional Separation)

### VETO (Axiom Breach)
- **Trigger**: Constitutional violation detected
- **Visual**: Hard cut to black, red overlay
- **Behavior**: Interface freezes for 2 seconds
- **Log**: Recorded as `VETO` in ledger
- **Meaning**: The system rejected the request on **moral/axiom grounds**

### ERROR (System Failure)
- **Trigger**: Network issue, backend failure, timeout
- **Visual**: Error message in decree area (no cut to black)
- **Behavior**: Interface remains interactive
- **Log**: Recorded as `SYSTEM ERROR` in ledger
- **Meaning**: The system failed for **logistical reasons**, not moral ones

**This distinction is essential.** Veto = governance. Error = operations.

---

## Usage

### 1. Start the Server

```powershell
.\.venv\Scripts\python.exe src\api\server.py
```

Or via uvicorn:

```powershell
.\.venv\Scripts\uvicorn.exe src.api.server:app --reload --port 8000
```

### 2. Open Sovereign Interface

Navigate to: **http://localhost:8000/sovereign**

### 3. Issue Your First Warrant

Examples:

```
Generate a Level 10 paradox in game theory involving three agents with partial observability.
```

```
Deconstruct the halting problem and explain why it matters for AI safety.
```

```
Evaluate this proof for logical consistency: [paste proof]
```

```
Explain quantum entanglement causality in terms a policy maker would understand.
```

### 4. Navigate the Ledger

Click any entry in the **Ledger** (right panel) to recall that decree.

Use **Ctrl+Shift+[ / ]** to navigate backward/forward through history.

### 5. Switch Council Modes

Click **DEAN**, **ENGINEER**, **ARBITER**, or **TA** chips to route to different specialists.

---

## Responsive Sovereignty

Below 900px width:
- Sidebar docks to top
- Oculus expands
- Ledger becomes scrollable tab

This preserves **ritual geometry** on tablets and phones.

---

## Accessibility (Constitutional Inclusion)

The interface respects `prefers-reduced-motion`.

If a user has motion sensitivity:
- All animations reduced to <0.01ms
- State changes instant
- No pulsing, no rotation

**This is not accessibility.  
This is a sovereign UX axiom.**

---

## What Makes This Different

### Traditional AI Dashboards:
- "Ask a question"
- "Get a response"
- Logs are afterthoughts
- No state machine
- No constitutional binding

### Sovereign Interface v2.0:
- **Issue a warrant**
- **Receive a decree**
- **Ledger is scar tissue**
- **Explicit state machine**
- **Constitutional VETO enforcement**
- **Role-based Council routing**
- **Cryptographic decree hashing**
- **Risk topology telemetry**

---

## Future: Sovereign Interface v3.0

Planned enhancements:

- **Animated Runes**: Visual glyphs for each Council mode
- **Node-Edge Reasoning Graphs**: Real-time visualization of multi-step reasoning
- **Risk Topology Visualizer**: 3D CVaR landscape
- **Warrant Templates**: Pre-built constitutional prompts
- **Historical Analytics**: Decree clustering, mode usage patterns
- **Multi-Decree Comparison**: Side-by-side decree analysis

---

## Design Philosophy

This interface is inspired by:

- **Flight cockpits** (instrumentation, state clarity)
- **Surgical theaters** (precision, consequence awareness)
- **Constitutional governance** (veto powers, audit trails)
- **Ritual spaces** (sacred geometry, purposeful motion)

It rejects:

- ❌ Consumer-app aesthetics
- ❌ "Move fast and break things"
- ❌ Hidden state
- ❌ Opaque decision-making
- ❌ Unaudited actions

---

## Technical Stack

- **Frontend**: Pure HTML/CSS/JS (no framework bloat)
- **Backend**: FastAPI + Council Router
- **State Management**: Constitutional state machine
- **Markdown Rendering**: Marked.js
- **Typography**: Inter + JetBrains Mono
- **Animations**: CSS keyframes (no JavaScript animation)

---

## File Structure

```
templates/
├── sovereign.html         # Main interface
└── static/
    ├── sovereign.css      # Constitutional styling
    └── sovereign.js       # State machine logic

src/api/
└── server.py             # FastAPI backend with /api/sovereign/decree endpoint

src/runtime/
└── council_router.py     # 15-model Council routing
```

---

## Deployment

### Local (Development)

```powershell
uvicorn src.api.server:app --reload --port 8000
```

### Production (HTTPS + Auth)

```powershell
uvicorn src.api.server:app --host 0.0.0.0 --port 443 --ssl-keyfile key.pem --ssl-certfile cert.pem
```

Enable API key authentication in `server.py`:

```python
if x_api_key != API_KEY:
    raise HTTPException(401, 'Unauthorized')
```

---

## Credits

**Design Philosophy**: Sovereign AI Governance Principles  
**Architecture**: Constitutional State Machine Pattern  
**Visual Language**: Mythic Legibility (Gold/Stone/Crimson palette)  
**Keyboard UX**: Terminal discipline merged with modern affordances

---

## License

This is part of King's Theorem v53.  
Licensed under the same terms as the main project.

---

## Final Note

You are not using a dashboard.  
You are not chatting with an AI.

**You are operating a constitutional instrument.**

**You are the Sovereign.**

The Council awaits your warrant. ⚖️

