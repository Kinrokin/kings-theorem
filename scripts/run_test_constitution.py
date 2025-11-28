import os
import sys
import traceback

repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo not in sys.path:
    sys.path.insert(0, repo)
print("Inserted repo to sys.path:", sys.path[0])

test_path = os.path.join(repo, "tests", "test_constitution.py")
print("Executing", test_path)
try:
    with open(test_path, "r", encoding="utf-8") as f:
        code = f.read()
    exec(compile(code, test_path, "exec"), {"__name__": "__main__"})
    print("\nTest script executed successfully")
except Exception:
    print("\nTest script raised exception:")
    traceback.print_exc()
    sys.exit(1)
