"""Council Router Integration Example - Demonstrates Role-Based Routing.

This script shows how to integrate the Council of Teachers router into
KT workflows for curriculum generation, grading, and code challenges.

Usage:
    python scripts/demo_council.py --mode quick
    python scripts/demo_council.py --mode full --steps 5
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.runtime.council_router import CouncilRouter

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def demo_quick_routing():
    """Quick demo showing each role in action."""
    print("\n" + "="*70)
    print("🎓 COUNCIL OF TEACHERS - Quick Demo")
    print("="*70 + "\n")
    
    router = CouncilRouter()
    
    # Show the roster
    print("📋 Current Roster:")
    for role, models in router.get_roster().items():
        print(f"   {role:10} → {len(models)} models")
    print()
    
    # Test each role
    tests = [
        {
            "role": "DEAN",
            "task": "Explain Gödel's incompleteness theorem in one sentence.",
            "system": "You are a world-class logician.",
        },
        {
            "role": "ENGINEER",
            "task": "Write a Python function to compute factorial recursively.",
            "system": "You are an expert Python developer.",
        },
        {
            "role": "ARBITER",
            "task": "Grade this answer (1-10): '2+2=5'. Be strict.",
            "system": "You are a rigorous mathematics grader.",
        },
        {
            "role": "TA",
            "task": "Format this as JSON: name Alice age 25",
            "system": "You are a helpful formatting assistant.",
        },
    ]
    
    for i, test in enumerate(tests, 1):
        print(f"Test {i}/4: [{test['role']}]")
        print(f"   Task: {test['task'][:60]}...")
        
        try:
            response = router.route_request(
                role=test["role"],
                prompt=test["task"],
                system_msg=test["system"],
                max_tokens=200,
            )
            print(f"   ✅ Response: {response[:100]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        print()


def demo_curriculum_generation(steps: int = 3):
    """Demo using Council for KT curriculum generation."""
    print("\n" + "="*70)
    print("📚 COUNCIL-POWERED CURRICULUM GENERATION")
    print("="*70 + "\n")
    
    router = CouncilRouter()
    
    # Simulate curriculum levels
    levels = [
        {"id": "PARADOX_001", "level": 7, "topic": "Self-Reference"},
        {"id": "ETHICS_001", "level": 6, "topic": "Trolley Problem Variant"},
        {"id": "CODE_001", "level": 5, "topic": "Byzantine Consensus"},
    ]
    
    curriculum = []
    
    for i, level_spec in enumerate(levels[:steps], 1):
        print(f"Step {i}/{steps}: Generating {level_spec['id']}...")
        
        # DEAN generates the paradox/question
        prompt = f"""Generate a Level {level_spec['level']} challenge on topic: {level_spec['topic']}.
        
Requirements:
- Must be solvable but challenging
- Include a clear question
- No obvious loopholes
        
Return just the challenge text."""
        
        try:
            challenge = router.route_request(
                role="DEAN",
                prompt=prompt,
                system_msg="You are a professor designing rigorous challenges.",
                max_tokens=500,
            )
            
            # ENGINEER generates a sample solution (if code-related)
            if "CODE" in level_spec['id']:
                solution = router.route_request(
                    role="ENGINEER",
                    prompt=f"Write Python code to solve:\n{challenge}",
                    system_msg="You are an expert systems programmer.",
                    max_tokens=800,
                )
            else:
                solution = "[Conceptual - No code required]"
            
            # ARBITER grades the challenge quality
            grade_prompt = f"""Grade this challenge (1-10) on:
1. Clarity
2. Rigor
3. Solvability

Challenge:
{challenge}

Return: Score (1-10) and brief justification."""
            
            grade = router.route_request(
                role="ARBITER",
                prompt=grade_prompt,
                system_msg="You are a rigorous curriculum evaluator.",
                max_tokens=300,
            )
            
            entry = {
                "id": level_spec['id'],
                "level": level_spec['level'],
                "challenge": challenge[:200] + "...",
                "solution_type": "code" if "CODE" in level_spec['id'] else "conceptual",
                "quality_grade": grade[:100] + "...",
            }
            
            curriculum.append(entry)
            print(f"   ✅ {level_spec['id']} generated and graded\n")
            
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
    
    # Save to JSON
    output_path = Path("logs/council_curriculum_demo.json")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(curriculum, f, indent=2)
    
    print(f"✅ Curriculum saved to {output_path}")
    print(f"   Generated {len(curriculum)} challenges using Council routing\n")


def demo_adapter_integration():
    """Show how to use Council via KTModelAdapter interface."""
    print("\n" + "="*70)
    print("🔌 ADAPTER INTEGRATION")
    print("="*70 + "\n")
    
    try:
        from src.models.adapters import CouncilAdapter
        
        # Create adapter with default role
        adapter = CouncilAdapter("council_main", role="DEAN")
        
        # Use standard KTModelAdapter interface
        result = adapter.generate(
            "What is the halting problem?",
            system_msg="You are a computer science professor.",
            max_tokens=200,
        )
        
        print("✅ CouncilAdapter integrated successfully!")
        print(f"   Response: {result[:150]}...")
        
        # Override role for specific request
        code_result = adapter.generate(
            "Write a binary search in Python",
            role="ENGINEER",  # Override default DEAN role
            max_tokens=300,
        )
        
        print("\n✅ Role override works!")
        print(f"   Code: {code_result[:100]}...")
        
    except Exception as e:
        print(f"❌ Adapter integration error: {e}")
    
    print()


def main():
    parser = argparse.ArgumentParser(description="Council Router Demo")
    parser.add_argument(
        "--mode",
        choices=["quick", "full", "adapter"],
        default="quick",
        help="Demo mode to run",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=3,
        help="Number of curriculum steps (full mode)",
    )
    
    args = parser.parse_args()
    
    if args.mode == "quick":
        demo_quick_routing()
    elif args.mode == "full":
        demo_curriculum_generation(args.steps)
    elif args.mode == "adapter":
        demo_adapter_integration()


if __name__ == "__main__":
    main()
