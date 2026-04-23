"""Reconcile assistant state: drop duplicates, list missing PDFs, optionally fix."""
import os
import sys
import yaml
from collections import defaultdict
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from pinecone import Pinecone

DRY = "--fix" not in sys.argv

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
a = pc.assistant.Assistant(assistant_name="ggu-techdoc-search-pdf")
files = a.list_files()

by_name: dict[str, list] = defaultdict(list)
for f in files:
    by_name[f.name].append(f)

# Expected filenames (from registry, indexed=true)
reg_path = Path(__file__).parent.parent / "config" / "norms-registry.yaml"
with open(reg_path, "r", encoding="utf-8") as fh:
    registry = yaml.safe_load(fh)
expected = {
    n["sharepoint_file"]
    for n in registry.get("norms", [])
    if n.get("sharepoint_file") and n.get("indexed")
}

in_assistant = set(by_name.keys())
missing = sorted(expected - in_assistant)
extra = sorted(in_assistant - expected)
dupes = {n: entries for n, entries in by_name.items() if len(entries) > 1}

print(f"Expected (registry, indexed):  {len(expected)}")
print(f"Distinct names in assistant:   {len(in_assistant)}")
print(f"Missing from assistant:        {len(missing)}")
for n in missing:
    print(f"  - {n}")
print(f"Unexpected in assistant:       {len(extra)}")
for n in extra:
    print(f"  - {n}")

print(f"\nDuplicate names: {len(dupes)}")
for name, entries in sorted(dupes.items()):
    # Keep the first (oldest) one; drop the rest
    keep = entries[0]
    drop = entries[1:]
    print(f"  {name}")
    print(f"    keep: {keep.id} [{keep.status}]")
    for d in drop:
        action = "DELETE" if not DRY else "would delete"
        print(f"    {action}: {d.id} [{d.status}]")
        if not DRY:
            try:
                a.delete_file(file_id=d.id)
                print("      OK")
            except Exception as e:
                print(f"      FAIL: {e}")

if DRY:
    print("\n[DRY RUN] Re-run with --fix to actually delete duplicates.")
