"""Regenerate the frozen live-input inventory after a shipped pack's files change.

`tests/test_townlet/unit/oracle/test_declaration_input_drift.py` pins a sha256 for every
input file of the static-epistemic-access evidence packs in
`docs/product/evidence/static-epistemic-access/frozen-live-inputs.json`. Respelling a
shipped pack moves those digests; run this, then review the diff.

    uv run python scripts/regen_frozen_live_inputs.py
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests/test_townlet/unit/oracle"))

import test_declaration_input_drift as drift  # noqa: E402

INVENTORY = ROOT / "docs/product/evidence/static-epistemic-access/frozen-live-inputs.json"


def main() -> None:
    inventory = json.loads(INVENTORY.read_text())
    for record in inventory["packs"]:
        record["live_files"] = {name: hashlib.sha256(data).hexdigest() for name, data in drift._pack_files(ROOT / record["pack"]).items()}
        record["delta"] = drift.pack_drift(ROOT / drift.ORACLE_PACK_ROOT, ROOT, record["pack"])
    INVENTORY.write_text(json.dumps(inventory, indent=2) + "\n")
    print("inventory regenerated")


if __name__ == "__main__":
    main()
