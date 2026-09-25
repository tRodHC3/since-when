"""Behavioral tests for the catalog pipeline.

Not part of the app. Read-only against index.html and the real drafts/ folder —
every check that could write something does so in a temp directory.

Usage (from the repo root):
    py scripts/test_pipeline.py

Prints PASS/FAIL per check. Exits 1 if any check fails.
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


propose_seed = load_module("propose_seed", SCRIPTS / "propose_seed.py")

results = []


def check(name, condition):
    results.append((name, bool(condition)))
    print("{}: {}".format("PASS" if condition else "FAIL", name))


def run():
    seed = propose_seed.load_seed(propose_seed.INDEX_PATH)
    index = propose_seed.seed_index(seed)

    mozzarella = index.get("072830011211")
    check("072830011211 is in SEED as HALAL", mozzarella is not None and mozzarella["status"] == "HALAL")

    sprite = index.get("049000555318")
    check("049000555318 is in SEED as CLEAR", sprite is not None and sprite["status"] == "CLEAR")

    with tempfile.TemporaryDirectory() as tmp:
        draft_path = Path(tmp) / "tillamook.json"
        draft_path.write_text(json.dumps([
            {"gtin": "072830011211", "name": "Farmstyle Shreds Mozzarella 8 oz", "brand": "Tillamook", "image_url": ""}
        ]), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "propose_seed.py"), str(draft_path)],
            cwd=str(ROOT), capture_output=True, text=True
        )
        out_path = draft_path.parent / "proposed" / "tillamook.json"
        proposed = json.loads(out_path.read_text(encoding="utf-8")) if out_path.is_file() else None
        check(
            "072830011211 is skipped by propose_seed.py (already seeded)",
            proc.returncode == 0 and proposed == [] and "already seeded" in proc.stdout
        )

    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "accept_row.py"), "--gtin", "072830011211", "--status", "CLEAR"],
        cwd=str(ROOT), capture_output=True, text=True
    )
    check(
        "accept_row.py refuses an already-seeded gtin",
        proc.returncode == 1 and "REFUSED" in proc.stdout and "already in SEED" in proc.stdout
    )

    with tempfile.TemporaryDirectory() as tmp:
        bad_path = Path(tmp) / "bad.json"
        bad_path.write_text(json.dumps([
            {
                "id": "bad-row",
                "barcodes": ["000000000123"],
                "brand": "Test",
                "product": "Bad status fixture",
                "status": "NOT A REAL STATUS",
                "fixture": False,
                "pack_claim": None,
                "enzyme": None,
                "events": [
                    {
                        "effective_on": None, "labeled_on": None, "verified_on": "2026-09-25",
                        "field": "pack_inspection", "old_value": None, "new_value": "x",
                        "source_url": "https://example.com/x", "notes": ""
                    }
                ]
            }
        ]), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "validate_seed.py"), str(bad_path)],
            cwd=str(ROOT), capture_output=True, text=True
        )
        check("validate_seed.py exits 1 on an invalid status", proc.returncode == 1 and "FAIL" in proc.stdout)

    failed = [name for name, ok in results if not ok]
    print()
    print("{}/{} checks passed".format(len(results) - len(failed), len(results)))
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    run()
