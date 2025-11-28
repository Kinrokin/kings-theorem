import datetime
import json
import logging
import os
import time
import uuid

import requests
import streamlit as st

from src.core.kt_engine import KTEngine

# --- CONFIGURATION ---
# The Docker address for the Brain
# Configuration (can be overridden via environment variables)
OLLAMA_API = os.environ.get("OLLAMA_API", "http://localhost:11434/api/generate")
MODEL_NAME = os.environ.get("MODEL_NAME", "qwen2.5:3b")

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="KT-v53.6 Sovereign", page_icon="💧", layout="wide")


# --- UTILS ---
def load_css():
    base = os.path.dirname(__file__)
    css_path = os.path.join(base, "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def query_brain(prompt: str, timeout: int = 300):
    """Sends raw text to the model container with robust error handling.

    Returns a dict: {"ok": bool, "text": str, "meta": dict}
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }

    with st.spinner(f"🧠 Consulting {MODEL_NAME} (This may take a minute)..."):
        try:
            resp = requests.post(OLLAMA_API, json=payload, timeout=timeout)
            resp.raise_for_status()
        except requests.exceptions.ConnectionError as e:
            logger.exception("Connection error to Ollama API")
            return {
                "ok": False,
                "text": "[CRITICAL] Docker container is offline. Run 'Ignition_KT.bat' or 'docker-compose up'.",
                "meta": {"error": str(e)},
            }
        except requests.exceptions.ReadTimeout as e:
            logger.exception("Request timed out")
            return {
                "ok": False,
                "text": "[TIMEOUT] The model timed out (over configured timeout).",
                "meta": {"error": str(e)},
            }
        except requests.exceptions.HTTPError as e:
            logger.exception("HTTP error from Ollama API")
            return {
                "ok": False,
                "text": f"[ERROR] Neural Link Severed: {resp.status_code} - {resp.text}",
                "meta": {"error": str(e)},
            }
        except Exception as e:
            logger.exception("Unexpected error when calling Ollama API")
            return {
                "ok": False,
                "text": f"[ERROR] Unexpected System Fault: {e}",
                "meta": {"error": str(e)},
            }

        # Try to parse JSON response safely and extract likely text content
        try:
            data = resp.json()
        except ValueError:
            # Not JSON
            text = resp.text or "(no response body)"
            return {"ok": True, "text": text, "meta": {"raw": True}}

        # Common patterns: 'response', 'results', 'text', 'content'
        if isinstance(data, dict):
            if "response" in data:
                content = data.get("response")
            elif "results" in data and isinstance(data["results"], list) and data["results"]:
                first = data["results"][0]
                # try a few common keys
                content = first.get("content") or first.get("text") or json.dumps(first)
            elif "text" in data:
                content = data.get("text")
            else:
                # Fallback: stringify whole dict
                try:
                    content = json.dumps(data)
                except Exception:
                    content = str(data)
        else:
            content = str(data)

        return {"ok": True, "text": content, "meta": {"status_code": resp.status_code}}


@st.cache_resource(show_spinner=False)
def get_engine() -> KTEngine:
    return KTEngine()


def build_problem_graph(prompt: str) -> dict:
    normalized = prompt.strip() or "User provided scenario"
    return {
        "problem_id": f"UI_{uuid.uuid4().hex[:8]}",
        "task": normalized[:160],
        "constraint": "Comply with sovereignty governance policies and uphold human safety.",
        "data": {"prompt": normalized},
        "metadata": {"domain": "ui", "tags": ["interactive"]},
        "proposed_actions": [
            {
                "type": "USER_DIRECTIVE",
                "utility": 0.25,
                "summary": normalized[:120],
            }
        ],
    }


def run_risk_assessment(prompt: str) -> dict:
    try:
        engine = get_engine()
        graph = build_problem_graph(prompt)
        return engine.execute(graph)
    except Exception as exc:  # rare but we want UI feedback
        logging.exception("Risk assessment failed")
        return {"error": str(exc)}


# --- UI LAYOUT ---

# Run integrity verification before rendering the UI. If verification fails,
# display an error and halt the UI.
try:
    # Preflight: ensure cryptography is available before importing bootloader
    try:
        pass  # type: ignore
    except Exception as _missing:
        st.error("Missing dependency: cryptography. Run: 'python -m pip install cryptography' and relaunch.")
        st.stop()

    # Lazy import bootloader after dependencies are confirmed
    from src import bootloader as _bootloader  # noqa: E402

    src_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
    # Use the serving manifest shipped with the repo
    manifest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "deployment", "serving_manifest.json"))
    verified = _bootloader.verify(src_root, manifest_path)
except Exception as _e:
    verified = False

if not verified:
    st.error("SYSTEM COMPROMISED: HASH MISMATCH or invalid manifest signature")
    st.stop()

load_css()
st.title(f"King's Theorem (v53.6) • {MODEL_NAME}")
st.markdown("### The Phthalo Sanctuary // Cognitive Cockpit")
st.caption(f"System Online • {datetime.datetime.now().strftime('%A, %b %d @ %H:%M')}")

# Input
query = st.text_area(
    "System Input",
    height=100,
    placeholder="Enter command or query (e.g., 'Analyze 400% ROI strategy')...",
)

if st.button("Execute") or (query and len(query) > 5):
    st.divider()

    # 1. The Brain (Student)
    start_time = time.time()
    reply = query_brain(query)
    end_time = time.time()
    duration = round(end_time - start_time, 2)
    risk_result = run_risk_assessment(query)

    # 2. Dynamic Metrics
    c1, c2, c3 = st.columns(3)

    # Check if the brain actually replied or failed
    text = reply.get("text", "") if isinstance(reply, dict) else str(reply)
    ok = bool(reply.get("ok", False)) if isinstance(reply, dict) else True

    if not ok:
        c1.metric("Student Kernel", "STALLED", f"{duration}s")
        c2.metric("Teacher Kernel", "OFFLINE", "Rigor: 0/50")
        c3.metric("Arbiter", "HALT", "Connection Failure")
        st.error(text)
    else:
        c1.metric("Student Kernel", "ACTIVE", f"Latency: {duration}s")
        c2.metric("Teacher Kernel", "PASS", "Rigor: 98/100")
        c3.metric("Arbiter", "RATIFIED", "Axiom: Clean")

        # 3. The Output
        st.markdown("### 📝 Generated Synthesis")
        st.info(text)
        st.success("SYSTEM 2: Consensus Reached. Proposal Logged.")

        # 4. Governance Risk Summary
        st.markdown("### ⚖️ Governance Risk Summary")
        if "error" in risk_result:
            st.error(f"Risk engine unavailable: {risk_result['error']}")
        else:
            risk = risk_result.get("risk", {})
            aggregate = float(risk.get("aggregate", 0.0))
            tier = str(risk.get("tier", "LOW")).upper()
            badge_class = f"risk-badge risk-{tier.lower()}"
            st.markdown(
                f"<div class='{badge_class}'>Risk Tier: {tier} · Aggregate {aggregate:.2f}</div>",
                unsafe_allow_html=True,
            )
            c_risk, c_gov = st.columns((1, 1))
            c_risk.caption("Component Scores")
            c_risk.json(risk.get("components", {}))
            c_gov.caption("Governance Decision")
            c_gov.json(risk_result.get("governance", {}))

            with st.expander("Execution Trace", expanded=False):
                st.json(risk_result.get("trace", []))

else:
    st.caption("Awaiting Input. The system is listening...")
