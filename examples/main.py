# examples/example.py

"""
MASTER EXAMPLE RUNNER

Dynamically discovers and runs all example modules in this directory.
Modules must:
  - Be named like: *_demo.py, *_example.py, etc.
  - Define a `main()` function.
  - Not be this file (example.py).

Runs in sorted filename order.
"""

import os
import sys
import importlib.util
from pathlib import Path

def discover_and_run_examples():
    """Discover and run all example modules in this directory."""
    # Get directory of this file
    examples_dir = Path(__file__).parent.resolve()
    print(f"Scanning for examples in: {examples_dir}\n")

    # Find all Python files matching pattern (exclude this file)
    example_files = sorted([
        f for f in examples_dir.glob("*.py")
        if f.name != "example.py" and not f.name.startswith("__")
        and ("demo" in f.name or "example" in f.name)
    ])

    if not example_files:
        print("No example files found.")
        return

    print(f"Found {len(example_files)} example(s):\n")

    for i, example_path in enumerate(example_files, 1):
        module_name = example_path.stem

        print("=" * 80)
        print(f"🚀 RUNNING EXAMPLE {i}: {module_name}")
        print("=" * 80)

        try:
            # Dynamically import the module
            spec = importlib.util.spec_from_file_location(module_name, example_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Run main() if it exists
            if hasattr(module, "main") and callable(module.main):
                module.main()
            else:
                print(f"⚠️  Module {module_name} has no main() function — skipping.")

            print(f"✅ EXAMPLE {i} COMPLETED: {module_name}\n")

        except Exception as e:
            print(f"❌ FAILED EXAMPLE {i}: {module_name}")
            print(f"   Error: {e}\n")
            continue

    print("=" * 80)
    print("🏁 ALL EXAMPLES COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    discover_and_run_examples()
