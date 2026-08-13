"""Verify that modified files compile without errors."""
import py_compile
import sys

files_to_check = [
    "client/ui/main_window.py",
    "backend/server.py",
    "client/services/api_client.py",
]

all_ok = True
for f in files_to_check:
    try:
        py_compile.compile(f, doraise=True)
        print(f"OK: {f}")
    except py_compile.PyCompileError as e:
        print(f"FAIL: {f} - {e}")
        all_ok = False

if all_ok:
    print("\nAll files compile successfully!")
    sys.exit(0)
else:
    print("\nCompilation errors found!")
    sys.exit(1)