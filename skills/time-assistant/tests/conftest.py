import sys
from pathlib import Path

# Make engine/ integrations/ modules/ importable as top-level packages.
SKILL_ROOT = Path(__file__).resolve().parent.parent
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))
