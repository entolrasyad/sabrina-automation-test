"""
bump_version.py — Increment patch version in version.txt
v2.6 → v2.7 → ... → v2.9 → v3.0
"""
import re
import os
import sys

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.txt")

try:
    current = open(path, encoding="utf-8").read().strip()
except FileNotFoundError:
    current = "v1.0"

m = re.match(r"v?(\d+)\.(\d+)", current)
if not m:
    print(f"ERROR: format version tidak dikenali: '{current}'")
    sys.exit(1)

major, minor = int(m.group(1)), int(m.group(2))
minor += 1
if minor >= 10:
    major += 1
    minor = 0

new_version = f"v{major}.{minor}"
with open(path, "w", encoding="utf-8") as f:
    f.write(new_version)

print(f"{current} → {new_version}")
