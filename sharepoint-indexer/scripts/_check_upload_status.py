"""Quick diagnostic: count files in a Pinecone assistant."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from pinecone import Pinecone

assistant_name = sys.argv[1] if len(sys.argv) > 1 else "ggu-techdoc-search-pdf"

pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
a = pc.assistant.Assistant(assistant_name=assistant_name)
files = a.list_files()
items = files.files if hasattr(files, "files") else files

print(f"Assistant: {assistant_name}")
print(f"Files:     {len(items)}")
print("")
for f in items:
    name = getattr(f, "name", None) or (f.get("name") if isinstance(f, dict) else "?")
    status = getattr(f, "status", None) or (f.get("status") if isinstance(f, dict) else "?")
    print(f"  [{status}] {name}")
