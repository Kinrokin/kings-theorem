#!/usr/bin/env python3
"""
Validation Script - Test all Ouroboros components
Runs dry-run tests to ensure all generators work correctly.
"""

import sys
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_imports() -> bool:
    """Validate all imports work correctly."""
    print("\n" + "="*70)
    print("🔍 PHASE 1: VALIDATING IMPORTS")
    print("="*70)
    
    try:
        print("  ✓ Importing EventHorizonGenerator...")
        from scripts.generate_event_horizon import EventHorizonGenerator
        
        print("  ✓ Importing DomainCurvatureGenerator...")
        from src.crucibles.domain_curvature import DomainCurvatureGenerator
        
        print("  ✓ Importing FusionGenerator...")
        from scripts.generate_fusion import FusionGenerator
        
        print("  ✓ Importing CouncilRouter...")
        from src.runtime.council_router import CouncilRouter
        
        # Silence unused import warnings
        _ = (EventHorizonGenerator, DomainCurvatureGenerator, FusionGenerator, CouncilRouter)
        
        print("\n✅ All imports successful!")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        return False


def validate_event_horizon() -> bool:
    """Validate EventHorizonGenerator has all required methods."""
    print("\n" + "="*70)
    print("🔍 PHASE 2: VALIDATING EVENT HORIZON GENERATOR")
    print("="*70)
    
    try:
        # Import the class without instantiating
        from scripts.generate_event_horizon import EventHorizonGenerator
        
        # Check required methods exist on the class
        required_methods = [
            '_generate_paradox',
            '_initial_deconstruction',
            '_fractal_refinement_loop',
            '_compress_solution',
            '_score_solution',
            '_criticize_solution',
            'mine_singularity',
            'mine_singularity_from_seed',
            '_log',
        ]
        
        for method in required_methods:
            if not hasattr(EventHorizonGenerator, method):
                print(f"  ❌ Missing method: {method}")
                return False
            print(f"  ✓ Method exists: {method}")
        
        # Check method signatures
        import inspect
        
        # Validate mine_singularity_from_seed signature
        sig = inspect.signature(EventHorizonGenerator.mine_singularity_from_seed)
        params = list(sig.parameters.keys())
        
        # Remove 'self' from params
        if 'self' in params:
            params.remove('self')
        
        if 'domain' not in params or 'paradox_seed' not in params or 'curvature_type' not in params:
            print(f"  ❌ mine_singularity_from_seed has wrong signature: {params}")
            return False
        
        print(f"  ✓ mine_singularity_from_seed signature correct: {params}")
        
        print("\n✅ EventHorizonGenerator validation passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ EventHorizonGenerator validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_curvature_generator() -> bool:
    """Validate DomainCurvatureGenerator."""
    print("\n" + "="*70)
    print("🔍 PHASE 3: VALIDATING CURVATURE GENERATOR")
    print("="*70)
    
    try:
        from src.crucibles.domain_curvature import DomainCurvatureGenerator
        
        # Check required methods on class
        if not hasattr(DomainCurvatureGenerator, 'generate'):
            print("  ❌ Missing method: generate")
            return False
        print("  ✓ Method exists: generate")
        
        if not hasattr(DomainCurvatureGenerator, 'detect_flattening'):
            print("  ❌ Missing method: detect_flattening")
            return False
        print("  ✓ Method exists: detect_flattening")
        
        # Test flattening detection (static method)
        test_flat = "This linearizes to classical logic."
        if not DomainCurvatureGenerator.detect_flattening(test_flat):
            print("  ❌ Flattening detection not working")
            return False
        print("  ✓ Flattening detection working")
        
        test_curved = "This exhibits hyperbolic divergence."
        if DomainCurvatureGenerator.detect_flattening(test_curved):
            print("  ❌ False positive in flattening detection")
            return False
        print("  ✓ No false positives in flattening detection")
        
        print("\n✅ DomainCurvatureGenerator validation passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ DomainCurvatureGenerator validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_fusion_generator() -> bool:
    """Validate FusionGenerator."""
    print("\n" + "="*70)
    print("🔍 PHASE 4: VALIDATING FUSION GENERATOR")
    print("="*70)
    
    try:
        from scripts.generate_fusion import FusionGenerator
        
        # Check required methods on class
        if not hasattr(FusionGenerator, 'mine_fusion_singularity'):
            print("  ❌ Missing method: mine_fusion_singularity")
            return False
        print("  ✓ Method exists: mine_fusion_singularity")
        
        # Check signature
        import inspect
        sig = inspect.signature(FusionGenerator.mine_fusion_singularity)
        params = list(sig.parameters.keys())
        
        # Remove 'self' from params
        if 'self' in params:
            params.remove('self')
        
        if 'domain' not in params or 'seed_a' not in params or 'seed_b' not in params:
            print(f"  ❌ mine_fusion_singularity has wrong signature: {params}")
            return False
        
        print(f"  ✓ mine_fusion_singularity signature correct: {params}")
        
        print("\n✅ FusionGenerator validation passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ FusionGenerator validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def validate_scripts_exist() -> bool:
    """Validate all required scripts exist."""
    print("\n" + "="*70)
    print("🔍 PHASE 5: VALIDATING SCRIPT FILES")
    print("="*70)
    
    base = Path(__file__).parent.parent
    
    required_scripts = [
        "scripts/generate_event_horizon.py",
        "scripts/run_curved_curriculum.py",
        "scripts/generate_fusion.py",
        "scripts/verify_harvest.py",
    ]
    
    all_exist = True
    for script in required_scripts:
        path = base / script
        if path.exists():
            print(f"  ✓ {script}")
        else:
            print(f"  ❌ Missing: {script}")
            all_exist = False
    
    if all_exist:
        print("\n✅ All required scripts exist!")
    else:
        print("\n❌ Some scripts are missing!")
    
    return all_exist


def validate_modules_exist() -> bool:
    """Validate all required modules exist."""
    print("\n" + "="*70)
    print("🔍 PHASE 6: VALIDATING MODULE FILES")
    print("="*70)
    
    base = Path(__file__).parent.parent
    
    required_modules = [
        "src/crucibles/domain_curvature.py",
    ]
    
    all_exist = True
    for module in required_modules:
        path = base / module
        if path.exists():
            print(f"  ✓ {module}")
        else:
            print(f"  ❌ Missing: {module}")
            all_exist = False
    
    if all_exist:
        print("\n✅ All required modules exist!")
    else:
        print("\n❌ Some modules are missing!")
    
    return all_exist


def main() -> int:
    """Run all validation checks."""
    print("\n" + "="*70)
    print("🛡️  OUROBOROS PROTOCOL - VALIDATION SUITE")
    print("="*70)
    print("Testing all components for Phase 8 compliance...")
    
    results: List[Tuple[str, bool]] = []
    
    # Run all validations
    results.append(("Script Files", validate_scripts_exist()))
    results.append(("Module Files", validate_modules_exist()))
    results.append(("Imports", validate_imports()))
    results.append(("Event Horizon Generator", validate_event_horizon()))
    results.append(("Curvature Generator", validate_curvature_generator()))
    results.append(("Fusion Generator", validate_fusion_generator()))
    
    # Final report
    print("\n" + "="*70)
    print("📊 VALIDATION SUMMARY")
    print("="*70)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("="*70)
    
    if all_passed:
        print("\n🎉 ALL VALIDATIONS PASSED!")
        print("The Ouroboros Protocol is ready for deployment.")
        print("\nNext steps:")
        print("  1. Run: python scripts/run_curved_curriculum.py --count 5")
        print("  2. Verify: python scripts/verify_harvest.py data/curved_curriculum.jsonl")
        print("  3. Generate fusions: python scripts/generate_fusion.py --input data/curved_curriculum.jsonl --count 3")
        return 0
    else:
        print("\n❌ VALIDATION FAILED!")
        print("Fix the errors above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
