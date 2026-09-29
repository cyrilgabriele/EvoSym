"""Build facts from cached SBB exports; --refresh explicitly downloads new snapshots."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.adapters.sbb.ingest import main


if __name__ == "__main__":
    raise SystemExit(main())
