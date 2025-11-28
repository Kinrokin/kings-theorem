#!/usr/bin/env python3
"""Verify Qwen 3 8B Installation and Reasoning Capabilities.

Usage:
    python scripts/verify_qwen3.py
"""

import requests
import json
import sys

OLLAMA_API = "http://localhost:11434/api/generate"

def check_model_available():
    """Check if qwen3:8b is installed."""
    print("🔍 Checking if Qwen 3 8B is available...")
    
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = resp.json().get("models", [])
        
        qwen3_found = any("qwen3" in m.get("name", "").lower() for m in models)
        
        if qwen3_found:
            print("✅ Qwen 3 8B found in Ollama")
            return True
        else:
            print("❌ Qwen 3 8B not found")
            print("\nTo install:")
            print("  ollama pull qwen3:8b")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        print("\nMake sure Ollama is running:")
        print("  Docker: docker-compose up -d")
        print("  Native: ollama serve")
        return False


def test_basic_inference():
    """Test basic model inference."""
    print("\n🧪 Testing basic inference...")
    
    payload = {
        "model": "qwen3:8b",
        "prompt": "What is 2+2? Answer in one word.",
        "stream": False,
        "options": {"temperature": 0.1}
    }
    
    try:
        resp = requests.post(OLLAMA_API, json=payload, timeout=30)
        
        if resp.status_code != 200:
            print(f"❌ API returned {resp.status_code}: {resp.text}")
            return False
        
        output = resp.json().get("response", "")
        print(f"   Response: {output.strip()}")
        
        if "4" in output:
            print("✅ Basic inference working")
            return True
        else:
            print("⚠️  Unexpected response")
            return False
            
    except Exception as e:
        print(f"❌ Inference error: {e}")
        return False


def test_reasoning_mode():
    """Test if Qwen 3 shows explicit reasoning."""
    print("\n🧠 Testing reasoning capabilities...")
    
    payload = {
        "model": "qwen3:8b",
        "prompt": """Show your step-by-step reasoning to solve this:
        
If 5 machines make 5 widgets in 5 minutes, how many machines are needed to make 100 widgets in 100 minutes?

Think through this carefully and show your work.""",
        "stream": False,
        "options": {"temperature": 0.7}
    }
    
    try:
        resp = requests.post(OLLAMA_API, json=payload, timeout=60)
        output = resp.json().get("response", "")
        
        print(f"   Response length: {len(output)} chars")
        print(f"   First 200 chars: {output[:200]}...")
        
        # Check for reasoning indicators
        reasoning_markers = [
            "step", "first", "then", "therefore", "because",
            "let's", "think", "reasoning", "calculate"
        ]
        
        has_reasoning = any(marker in output.lower() for marker in reasoning_markers)
        
        if has_reasoning:
            print("✅ Explicit reasoning detected")
            
            # Check for think tags (may not always be present)
            if "<think>" in output or "<reasoning>" in output:
                print("✅ Reasoning tags found (<think> or <reasoning>)")
            else:
                print("ℹ️  No explicit tags, but step-by-step logic present")
            
            return True
        else:
            print("⚠️  Response seems direct without reasoning steps")
            return False
            
    except Exception as e:
        print(f"❌ Reasoning test error: {e}")
        return False


def test_paradox_handling():
    """Test handling of a simple logical paradox."""
    print("\n🔀 Testing paradox handling...")
    
    payload = {
        "model": "qwen3:8b",
        "prompt": """Analyze this statement: "This statement is false."

What is the logical problem here? Explain step-by-step.""",
        "stream": False,
        "options": {"temperature": 0.7}
    }
    
    try:
        resp = requests.post(OLLAMA_API, json=payload, timeout=60)
        output = resp.json().get("response", "")
        
        print(f"   Response length: {len(output)} chars")
        
        # Check for key concepts
        key_concepts = ["paradox", "self-reference", "contradiction", "liar"]
        has_concepts = any(concept in output.lower() for concept in key_concepts)
        
        if has_concepts:
            print("✅ Paradox correctly identified")
            return True
        else:
            print("⚠️  May not fully understand the paradox")
            print(f"   Response: {output[:150]}...")
            return False
            
    except Exception as e:
        print(f"❌ Paradox test error: {e}")
        return False


def main():
    print("="*70)
    print("🎓 Qwen 3 8B Verification Script")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Model Available", check_model_available()))
    
    if not results[0][1]:
        print("\n❌ Cannot proceed without Qwen 3 8B installed")
        sys.exit(1)
    
    results.append(("Basic Inference", test_basic_inference()))
    results.append(("Reasoning Mode", test_reasoning_mode()))
    results.append(("Paradox Handling", test_paradox_handling()))
    
    # Summary
    print("\n" + "="*70)
    print("📊 VERIFICATION SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name:20} : {status}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nScore: {passed_count}/{total_count}")
    
    if passed_count == total_count:
        print("\n🎉 Qwen 3 8B is ready for KT curriculum generation!")
        print("\nNext steps:")
        print("  1. Update config/master_config.yaml with model_name: 'qwen3:8b'")
        print("  2. Generate curriculum: python scripts/run_curriculum.py --use-council --steps 10")
        print("  3. Train: python scripts/train_sft.py --model qwen3:8b")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check Ollama setup and model installation.")
        sys.exit(1)


if __name__ == "__main__":
    main()
