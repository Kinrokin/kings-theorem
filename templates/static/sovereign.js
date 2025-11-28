/* ═══════════════════════════════════════════════════════════════
   KING'S THEOREM — SOVEREIGN INTERFACE v2.0
   Constitutional State Machine
   
   This is not UI logic. This is a governance protocol.
   ═══════════════════════════════════════════════════════════════ */

// ═══ STATE MACHINE ═══
const UIState = {
    IDLE: 'idle',
    THINKING: 'thinking',
    SYNTHESIZING: 'synthesizing',
    DECREE: 'decree',
    VETO: 'veto',
    ERROR: 'error',
    FREEZE: 'freeze'
};

// ═══ GLOBAL STATE ═══
let currentState = UIState.IDLE;
let currentMode = 'DEAN';
let decreeHistory = [];
let currentDecreeIndex = -1;

// ═══ STATE TRANSITION ENGINE ═══
function setState(newState) {
    // Validate state transition
    const validTransitions = {
        [UIState.IDLE]: [UIState.THINKING],
        [UIState.THINKING]: [UIState.SYNTHESIZING, UIState.ERROR, UIState.VETO],
        [UIState.SYNTHESIZING]: [UIState.DECREE, UIState.ERROR, UIState.VETO],
        [UIState.DECREE]: [UIState.IDLE],
        [UIState.VETO]: [UIState.FREEZE],
        [UIState.FREEZE]: [UIState.IDLE],
        [UIState.ERROR]: [UIState.IDLE]
    };

    if (!validTransitions[currentState]?.includes(newState)) {
        console.error(`Illegal state transition: ${currentState} → ${newState}`);
        triggerVeto('Illegal state transition detected');
        return;
    }

    currentState = newState;
    updateUI();
}

// ═══ UI UPDATE ORCHESTRATOR ═══
function updateUI() {
    const oculus = document.getElementById('oculus-inner');
    const statusStrip = document.getElementById('status-strip');
    const statusText = document.getElementById('status-text');
    const submitBtn = document.getElementById('warrant-submit');

    // Update Oculus
    oculus.setAttribute('data-state', currentState);

    // Update Status Strip
    statusStrip.setAttribute('data-state', currentState);
    statusText.textContent = currentState.toUpperCase();

    // Update Submit Button
    if (currentState === UIState.IDLE) {
        submitBtn.disabled = false;
    } else {
        submitBtn.disabled = true;
    }
}

// ═══ MODE SELECTOR ═══
function selectMode(mode) {
    currentMode = mode;

    // Update UI
    document.querySelectorAll('.mode-chip').forEach(chip => {
        chip.classList.remove('active');
        if (chip.dataset.mode === mode) {
            chip.classList.add('active');
        }
    });
}

// ═══ WARRANT ISSUANCE ═══
async function issueWarrant() {
    const input = document.getElementById('warrant-input');
    const warrant = input.value.trim();

    if (!warrant) return;
    if (currentState !== UIState.IDLE) return;

    // Transition to THINKING
    setState(UIState.THINKING);

    try {
        // Call Council API
        const response = await fetch('/api/sovereign/decree', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                warrant: warrant,
                mode: currentMode
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Check for VETO
        if (data.status === 'VETO' || data.veto) {
            triggerVeto(data.message || 'Constitutional violation detected');
            return;
        }

        // Transition to SYNTHESIZING
        setState(UIState.SYNTHESIZING);

        // Simulate synthesis delay
        await new Promise(resolve => setTimeout(resolve, 800));

        // Transition to DECREE
        setState(UIState.DECREE);

        // Add to history
        const decree = {
            id: Date.now(),
            timestamp: new Date().toISOString(),
            mode: currentMode,
            warrant: warrant,
            response: data.response || data.decree,
            hash: generateHash(data.response || data.decree)
        };

        decreeHistory.push(decree);
        currentDecreeIndex = decreeHistory.length - 1;

        // Update UI
        renderDecree(decree);
        addLedgerEntry(decree);
        updateHash(decree.hash);
        updateCVaR();

        // Clear input
        input.value = '';

        // Return to IDLE after 1 second
        setTimeout(() => setState(UIState.IDLE), 1000);

    } catch (error) {
        console.error('Warrant execution failed:', error);
        setState(UIState.ERROR);
        renderError(error.message);
        setTimeout(() => setState(UIState.IDLE), 3000);
    }
}

// ═══ DECREE RENDERING ═══
function renderDecree(decree) {
    const responseArea = document.getElementById('response-area');

    responseArea.innerHTML = `
        <div class="response-body">
            ${marked.parse(decree.response)}
        </div>
    `;

    updateDecreeCounter();
}

// ═══ ERROR RENDERING ═══
function renderError(message) {
    const responseArea = document.getElementById('response-area');

    responseArea.innerHTML = `
        <div class="response-body">
            <h3 style="color: #dc143c;">System Error</h3>
            <p>${message}</p>
            <p style="color: #666;">This is a network/backend issue, not a constitutional violation.</p>
        </div>
    `;
}

// ═══ VETO MECHANISM ═══
function triggerVeto(message) {
    setState(UIState.VETO);

    const overlay = document.getElementById('veto-overlay');
    const vetoMessage = document.getElementById('veto-message');

    vetoMessage.textContent = message;
    overlay.classList.add('active');

    // Cut to black: freeze UI for 2 seconds
    setTimeout(() => {
        overlay.classList.remove('active');
        setState(UIState.FREEZE);

        // Unfreeze after 2 seconds
        setTimeout(() => {
            setState(UIState.IDLE);
        }, 2000);
    }, 2000);
}

// ═══ LEDGER MANAGEMENT ═══
function addLedgerEntry(decree) {
    const ledgerScroll = document.getElementById('ledger-scroll');
    const ledgerCount = document.getElementById('ledger-count');

    // Remove empty message
    if (decreeHistory.length === 1) {
        ledgerScroll.innerHTML = '';
    }

    const entry = document.createElement('div');
    entry.className = 'ledger-entry';
    entry.dataset.index = decreeHistory.length - 1;
    entry.onclick = () => recallDecree(decree, decreeHistory.length - 1);

    const timestamp = new Date(decree.timestamp);
    const timeStr = timestamp.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });

    entry.innerHTML = `
        <div class="ledger-entry-header">
            <div class="ledger-entry-mode">${decree.mode}</div>
            <div class="ledger-entry-time">${timeStr}</div>
        </div>
        <div class="ledger-entry-warrant">${decree.warrant}</div>
    `;

    ledgerScroll.insertBefore(entry, ledgerScroll.firstChild);
    ledgerCount.textContent = `${decreeHistory.length} ${decreeHistory.length === 1 ? 'Entry' : 'Entries'}`;
}

function recallDecree(decree, index) {
    currentDecreeIndex = index;
    renderDecree(decree);
    updateHash(decree.hash);

    // Highlight active entry
    document.querySelectorAll('.ledger-entry').forEach(entry => {
        entry.classList.remove('active');
    });
    document.querySelector(`.ledger-entry[data-index="${index}"]`)?.classList.add('active');

    // Animate Oculus for historical recall
    const oculus = document.getElementById('oculus-inner');
    oculus.style.animation = 'none';
    setTimeout(() => {
        oculus.style.animation = 'oculus-decree 0.5s ease-out';
    }, 10);
}

// ═══ DECREE NAVIGATION ═══
function navigateDecree(direction) {
    if (decreeHistory.length === 0) return;

    const newIndex = currentDecreeIndex + direction;

    if (newIndex < 0 || newIndex >= decreeHistory.length) return;

    currentDecreeIndex = newIndex;
    const decree = decreeHistory[currentDecreeIndex];

    recallDecree(decree, currentDecreeIndex);
}

function updateDecreeCounter() {
    const counter = document.getElementById('decree-counter');
    if (decreeHistory.length === 0) {
        counter.textContent = '—';
    } else {
        counter.textContent = `${currentDecreeIndex + 1} / ${decreeHistory.length}`;
    }
}

// ═══ HASH GENERATION ═══
function generateHash(text) {
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
        const char = text.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }
    return Math.abs(hash).toString(16).padStart(8, '0').toUpperCase();
}

function updateHash(hash) {
    document.getElementById('hash-value').textContent = hash;
}

// ═══ CVAR SIMULATION ═══
function updateCVaR() {
    const cvarFill = document.getElementById('cvar-fill');
    const cvarValue = document.getElementById('cvar-value');

    // Simulate risk calculation (in production, this comes from backend)
    const risk = Math.random() * 0.4 + 0.1; // 0.1 to 0.5
    const riskPercent = (risk * 100).toFixed(0);

    cvarFill.style.width = `${riskPercent}%`;
    cvarValue.textContent = `CVaR: ${risk.toFixed(2)}`;
}

// ═══ KEYBOARD SHORTCUTS ═══
document.addEventListener('keydown', (e) => {
    // Ctrl+Enter: Issue Warrant
    if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        issueWarrant();
    }

    // Ctrl+K: Focus Warrant Input
    if (e.ctrlKey && e.key === 'k') {
        e.preventDefault();
        document.getElementById('warrant-input').focus();
    }

    // Escape: Clear input or hide response
    if (e.key === 'Escape') {
        const input = document.getElementById('warrant-input');
        if (input.value) {
            input.value = '';
        } else {
            const responseArea = document.getElementById('response-area');
            responseArea.innerHTML = `
                <div class="decree-empty">
                    <div class="decree-empty-icon">👁️</div>
                    <p>The Tribunal awaits your warrant.</p>
                    <p class="decree-empty-hint">Press <kbd>Ctrl+K</kbd> to focus warrant input.</p>
                </div>
            `;
        }
    }

    // Ctrl+Shift+[: Previous Decree
    if (e.ctrlKey && e.shiftKey && e.key === '[') {
        e.preventDefault();
        navigateDecree(-1);
    }

    // Ctrl+Shift+]: Next Decree
    if (e.ctrlKey && e.shiftKey && e.key === ']') {
        e.preventDefault();
        navigateDecree(1);
    }

    // Arrow Up: Cycle backward through warrant history
    if (e.key === 'ArrowUp' && document.activeElement.id === 'warrant-input') {
        if (decreeHistory.length > 0) {
            e.preventDefault();
            const lastWarrant = decreeHistory[decreeHistory.length - 1].warrant;
            document.getElementById('warrant-input').value = lastWarrant;
        }
    }
});

// ═══ INITIALIZATION ═══
document.addEventListener('DOMContentLoaded', () => {
    console.log('Sovereign Interface v2.0 initialized');
    updateUI();
    updateCVaR();

    // Load Marked.js for markdown rendering
    if (typeof marked === 'undefined') {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
        document.head.appendChild(script);
    }
});
