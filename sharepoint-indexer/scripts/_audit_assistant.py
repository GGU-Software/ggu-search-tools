"""Audit: distinct filenames, duplicates, status breakdown."""
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from pinecone import Pinecone

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
a = pc.assistant.Assistant(assistant_name="ggu-techdoc-search-pdf")
files = a.list_files()

print(f"Total entries: {len(files)}\n")

by_name: dict[str, list] = defaultdict(list)
for f in files:
    by_name[f.name].append(f)

status_counts = Counter(f.status for f in files)
print(f"Status breakdown:")
for s, n in status_counts.most_common():
    print(f"  {s}: {n}")

dupes = {n: entries for n, entries in by_name.items() if len(entries) > 1}
print(f"\nDistinct names: {len(by_name)}")
print(f"Names with duplicates: {len(dupes)}")
if dupes:
    print("\nDuplicate entries:")
    for name, entries in sorted(dupes.items()):
        print(f"  {len(entries)}x {name}")
        for e in entries:
            print(f"    [{e.status}] id={e.id}")
