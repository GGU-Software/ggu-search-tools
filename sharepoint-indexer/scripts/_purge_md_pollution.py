"""Purge pollution from ggu-techdoc-search: delete files older than today.

The legacy upload path used tempfile.NamedTemporaryFile with suffix='.md',
so every markdown upload lands with a tmp*.md name regardless of vintage.
We distinguish pollution from fresh uploads by created_on timestamp.

Slow deletion (2s per call) to avoid Pinecone rate-limit 429s that truncated
the earlier clear_all_files pass.
"""
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from pinecone import Pinecone

DRY = "--fix" not in sys.argv
CUTOFF = datetime.now(timezone.utc) - timedelta(hours=6)

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
a = pc.assistant.Assistant(assistant_name="ggu-techdoc-search")
files = a.list_files()

keep = []
drop = []
for f in files:
    created = f.created_on if hasattr(f, "created_on") else None
    if isinstance(created, str):
        created = datetime.fromisoformat(created.replace("Z", "+00:00"))
    if created and created >= CUTOFF:
        keep.append(f)
    else:
        drop.append(f)

print(f"Total:       {len(files)}")
print(f"Keep (today): {len(keep)}")
print(f"Drop (pollution, older than {CUTOFF.isoformat()}): {len(drop)}")

if DRY:
    print("\n[DRY RUN] Re-run with --fix to actually delete.")
    sys.exit(0)

deleted = 0
failed = 0
for i, f in enumerate(drop, 1):
    try:
        a.delete_file(file_id=f.id)
        deleted += 1
        if i % 10 == 0 or i == len(drop):
            print(f"  {i}/{len(drop)} deleted...")
    except Exception as e:
        err = str(e)
        if "404" in err and "already deleted" in err.lower():
            deleted += 1
        else:
            failed += 1
            if failed <= 3:
                print(f"  fail {f.id}: {err.splitlines()[0]}")
    time.sleep(2.0)  # gentle — avoid 429

print(f"\nDeleted: {deleted}   Failed: {failed}")
