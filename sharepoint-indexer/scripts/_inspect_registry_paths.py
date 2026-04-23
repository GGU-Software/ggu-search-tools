"""Show sharepoint_path + file for the DGGT books and related gaps."""
import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
reg = yaml.safe_load(Path(__file__).parent.parent.joinpath("config/norms-registry.yaml").read_text(encoding="utf-8"))

targets = {"EAB", "EAU", "EBGEO", "EA-Pfähle", "OENORM EN 1997-1"}
for n in reg["norms"]:
    if n["id"] in targets:
        print(
            f"{n['id']:20s}  indexed={str(n.get('indexed', False)):5s}  "
            f"item_id={'SET' if n.get('item_id') else 'null'}  "
            f"path={n.get('sharepoint_path', '-')!r}  "
            f"file={n.get('sharepoint_file', '-')!r}"
        )
