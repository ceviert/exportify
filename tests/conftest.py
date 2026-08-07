import sys
from pathlib import Path

# The app uses top-level imports (from config import ..., from utils.logger import ...)
# that assume the app directory is on sys.path, as it is when run via Docker
# (python app/main.py). Add it here so tests can import the same way.
APP_DIR = Path(__file__).resolve().parent.parent / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
