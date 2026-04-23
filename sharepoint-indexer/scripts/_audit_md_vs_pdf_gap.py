"""Show which norms are in the markdown set but missing from the PDF set."""
from pathlib import Path
import yaml

reg = yaml.safe_load(Path(__file__).parent.parent.joinpath("config/norms-registry.yaml").read_text(encoding="utf-8"))

# PDF upload filter: indexed=true AND item_id set
pdf_set = set()
# Markdown upload filter: status in (found, withdrawn_only)
md_set = set()

for n in reg.get("norms", []):
    fname = n.get("sharepoint_file")
    if not fname:
        continue
    status = n.get("status", "pending")
    indexed = n.get("indexed", False)
    item_id = n.get("item_id")

    if status in ("found", "withdrawn_only"):
        md_set.add((n["id"], fname, status, indexed, bool(item_id)))
    if indexed and item_id:
        pdf_set.add((n["id"], fname, status, indexed, bool(item_id)))

gap = sorted(md_set - pdf_set)
print(f"MD-only count: {len(gap)}\n")
print(f"{'Norm':<35} {'Status':<18} indexed item_id  withdrawn?")
print("-" * 100)
for nid, fname, status, idx, has_iid in gap:
    withdrawn = "WITHDRAWN" if "zur" in fname.lower() or status == "withdrawn_only" else ""
    print(f"{nid:<35} {status:<18} {str(idx):<7} {str(has_iid):<8} {withdrawn}")
