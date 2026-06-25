import os
import sys
import tempfile

# make the `src` package importable when running pytest from any directory
INDEXER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if INDEXER_DIR not in sys.path:
    sys.path.insert(0, INDEXER_DIR)

# minimal settings for import; tests construct storage instances explicitly
os.environ.setdefault("INDEXER_FILES_DIR", tempfile.mkdtemp())
os.environ.setdefault("INDEXER_BASE_URL", "http://localhost/builds")
os.environ.setdefault("INDEXER_TOKEN", "test-token")
os.environ.setdefault("INDEXER_ENABLED_DIRECTORIES", "busybar-firmware")
os.environ.setdefault("INDEXER_STORAGE_BACKEND", "local")
