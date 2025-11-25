#!/usr/bin/env python3
"""
Lockfile Validation and Hash Enforcement Script

This script validates that:
1. requirements.lock exists and is up-to-date with requirements.txt
2. All dependencies have SHA256 hashes for integrity verification
3. Lockfile drift is detected as a violation heuristic

Usage:
    python scripts/validate_lockfile.py [--check] [--generate-hashes] [--output FILE]

Options:
    --check             Check if lockfile is up-to-date (exits 1 if drift detected)
    --generate-hashes   Generate lockfile with hashes (requires pip-tools)
    --output FILE       Output file for lockfile (default: requirements.lock)
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


def parse_requirements(filepath: str) -> dict:
    """Parse requirements file into a dict of package -> version spec."""
    packages = {}
    path = Path(filepath)
    if not path.exists():
        return packages

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Skip extras and environment markers
        if ";" in line:
            line = line.split(";")[0].strip()

        # Parse package>=version or package==version
        match = re.match(r"^([A-Za-z0-9_\-\.]+)\s*(>=|<=|==|~=|!=|>|<)?\s*([0-9a-zA-Z\.\-\*]+)?", line)
        if match:
            pkg = match.group(1).lower()
            op = match.group(2) or ""
            ver = match.group(3) or ""
            packages[pkg] = f"{op}{ver}" if op else ver

    return packages


def parse_lockfile(filepath: str) -> dict:
    """Parse lockfile into a dict of package -> (version, hash)."""
    packages = {}
    path = Path(filepath)
    if not path.exists():
        return packages

    current_pkg = None
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Check for hash line
        if line.startswith("--hash="):
            if current_pkg:
                packages[current_pkg]["hashes"].append(line[7:])
            continue

        # Parse package==version line
        match = re.match(r"^([A-Za-z0-9_\-\.]+)==([0-9a-zA-Z\.\-]+)", line)
        if match:
            pkg = match.group(1).lower()
            ver = match.group(2)
            current_pkg = pkg
            packages[pkg] = {"version": ver, "hashes": []}

    return packages


def check_lockfile_drift(requirements_path: str, lockfile_path: str) -> dict:
    """
    Check if lockfile has drifted from requirements.

    Returns a dict with:
        - status: "ok", "drift", "missing", "missing_hashes"
        - missing_packages: packages in requirements but not in lockfile
        - extra_packages: packages in lockfile but not in requirements
        - version_mismatches: packages with different versions
        - missing_hashes: packages without hashes
    """
    result = {
        "status": "ok",
        "missing_packages": [],
        "extra_packages": [],
        "version_mismatches": [],
        "missing_hashes": [],
    }

    reqs = parse_requirements(requirements_path)
    lock = parse_lockfile(lockfile_path)

    if not lock:
        result["status"] = "missing"
        result["missing_packages"] = list(reqs.keys())
        return result

    # Check for missing packages
    for pkg in reqs:
        if pkg not in lock:
            result["missing_packages"].append(pkg)

    # Check for extra packages
    for pkg in lock:
        if pkg not in reqs:
            result["extra_packages"].append(pkg)

    # Check for version mismatches
    for pkg, spec in reqs.items():
        if pkg in lock:
            locked_ver = lock[pkg]["version"]
            # Simple version check - if spec starts with >= or >, check if locked version meets it
            if spec.startswith(">="):
                min_ver = spec[2:]
                # Simple string comparison (works for most semver)
                if locked_ver < min_ver:
                    result["version_mismatches"].append({"package": pkg, "required": spec, "locked": locked_ver})

    # Check for missing hashes
    for pkg, info in lock.items():
        if not info["hashes"]:
            result["missing_hashes"].append(pkg)

    # Determine overall status
    if result["missing_packages"] or result["version_mismatches"]:
        result["status"] = "drift"
    elif result["missing_hashes"]:
        result["status"] = "missing_hashes"

    return result


def generate_lockfile_with_hashes(requirements_path: str, output_path: str) -> bool:
    """
    Generate lockfile with SHA256 hashes using pip-compile.

    Returns True on success, False on failure.
    """
    try:
        # Check if pip-tools is installed
        subprocess.run([sys.executable, "-m", "pip", "show", "pip-tools"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("pip-tools not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pip-tools"], check=True)

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "piptools",
                "compile",
                "--generate-hashes",
                "--output-file",
                output_path,
                requirements_path,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"Error generating lockfile: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def compute_file_hash(filepath: str) -> str:
    """Compute SHA256 hash of a file."""
    path = Path(filepath)
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Lockfile validation and hash enforcement")
    parser.add_argument("--check", action="store_true", help="Check if lockfile is up-to-date")
    parser.add_argument("--generate-hashes", action="store_true", help="Generate lockfile with hashes")
    parser.add_argument("--requirements", default="requirements.txt", help="Path to requirements.txt")
    parser.add_argument("--lockfile", default="requirements.lock", help="Path to lockfile")
    parser.add_argument("--output", default="lockfile_status.json", help="Output file for status")
    parser.add_argument("--strict", action="store_true", help="Fail on any warnings")

    args = parser.parse_args()

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    requirements_path = project_root / args.requirements
    lockfile_path = project_root / args.lockfile

    if args.generate_hashes:
        success = generate_lockfile_with_hashes(str(requirements_path), str(lockfile_path))
        sys.exit(0 if success else 1)

    # Check lockfile drift
    result = check_lockfile_drift(str(requirements_path), str(lockfile_path))

    # Add file hashes for integrity
    result["requirements_hash"] = compute_file_hash(str(requirements_path))
    result["lockfile_hash"] = compute_file_hash(str(lockfile_path))

    # Output results
    output_path = project_root / args.output
    output_path.write_text(json.dumps(result, indent=2))

    # Print summary
    print(f"Lockfile Status: {result['status'].upper()}")

    if result["missing_packages"]:
        print(f"  Missing packages: {', '.join(result['missing_packages'])}")
    if result["extra_packages"]:
        print(f"  Extra packages: {', '.join(result['extra_packages'])}")
    if result["version_mismatches"]:
        for m in result["version_mismatches"]:
            print(f"  Version mismatch: {m['package']} (required {m['required']}, locked {m['locked']})")
    if result["missing_hashes"]:
        print(f"  Missing hashes: {', '.join(result['missing_hashes'])}")

    if args.check:
        if result["status"] == "ok":
            print("✓ Lockfile is valid and up-to-date")
            sys.exit(0)
        elif result["status"] == "missing_hashes" and not args.strict:
            print("⚠ Lockfile is missing hashes (warning)")
            sys.exit(0)
        else:
            print("✗ Lockfile validation failed")
            sys.exit(1)


if __name__ == "__main__":
    main()
