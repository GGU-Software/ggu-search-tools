"""Check whitelist vs output filenames for the 5 new norms."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.indexing.norm_matcher import NormMatcher

m = NormMatcher(Path(__file__).parent.parent / "config" / "norms-registry.yaml")
wl = m.generate_whitelist()

keywords = ["EAB", "EAU", "EBGEO", "Pfahle", "1997-1-1"]

print("=== WHITELIST entries ===")
for f in sorted(wl):
    if any(k in f for k in keywords):
        print(f"  {f}")

print("\n=== OUTPUT files ===")
for f in sorted(os.listdir(Path(__file__).parent.parent / "output")):
    if any(k in f for k in keywords):
        print(f"  {f}")
