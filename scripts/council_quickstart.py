#!/usr/bin/env python3
"""Quick Start - Council of Teachers

Minimal example showing how to use the Council Router in 3 lines.
Perfect for copy-paste into your own scripts.

Usage:
    python scripts/council_quickstart.py
"""

import os

# 1. Set your API key (or set OPENROUTER_API_KEY environment variable)
os.environ["OPENROUTER_API_KEY"] = "your-key-here"  # Replace with real key

# 2. Import and create router
from src.runtime.council_router import CouncilRouter
router = CouncilRouter()

# 3. Use role-based routing
paradox = router.route_request(
    role="DEAN",  # Deep reasoning specialist
    prompt="Generate a self-referential paradox",
    system_msg="You are a logic professor",
)

code = router.route_request(
    role="ENGINEER",  # Code specialist
    prompt=f"Write Python to analyze: {paradox}",
    system_msg="You are a Python expert",
)

grade = router.route_request(
    role="ARBITER",  # Grading specialist
    prompt=f"Grade this code (1-10): {code}",
    system_msg="You are a code reviewer",
)

# That's it!
print("="*70)
print("🎓 COUNCIL OF TEACHERS - Quick Start Demo")
print("="*70)
print(f"\n📚 DEAN (Logic):\n{paradox[:200]}...\n")
print(f"🔧 ENGINEER (Code):\n{code[:200]}...\n")
print(f"⚖️ ARBITER (Grade):\n{grade[:200]}...\n")

# Pro Tips:
# - DEANs are expensive ($0.01-0.10/request) - use for hard problems only
# - TAs are cheap ($0.0001-0.001/request) - use for simple/bulk tasks
# - Set spending limits in OpenRouter dashboard: https://openrouter.ai/account
# - Check config/council_config.yaml for full 15-model roster

print("="*70)
print("✅ Demo complete! See docs/COUNCIL_ROUTER.md for full documentation")
print("="*70)
