"""Validate SEED-shaped rows: the live SEED array in index.html, or a JSON file.

Not part of the app. Read-only — never writes index.html or drafts/.

Usage (from the repo root):
    py scripts/validate_seed.py                    # validates index.html SEED
    py scripts/validate_seed.py drafts/accepted.json
    py scripts/validate_seed.py drafts/proposed/tillamook.json

Checks:
    - every event has a source_url (fixture rows may use https://example.invalid/fixture)
    - every barcode is a string
    - status is one of the allowed values
    - the status's CSS class (same rule as toKebab() in index.html) has no bullet left in it
    - no barcode repeats across rows
    - drafts/accepted.json never contains a row with fixture: true

Prints a report. Exits 1 if any row fails a check.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "index.html"

ALLOWED_STATUS = (
    "HALAL",
    "HALAL • NO MARK",
    "CLEAR",
    "ANIMAL RENNET",
    "PORK",
    "UNKNOWN",
)

def load_seed_from_index(path):
    text = path.read_text(encoding="utf-8")
    marker = "var SEED = "
    start = text.find(marker)
    if start < 0:
        raise SystemExit("SEED array not found in {}".format(path))
    data, _ = json.JSONDecoder().raw_decode(text[start + len(marker):])
    if not isinstance(data, list):
        raise SystemExit("SEED is not a list in {}".format(path))
    return data


def load_seed_from_json(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("{} is not a JSON array".format(path))
    return data


def to_kebab(status):
    """Mirrors toKebab()/normalizeStatus() in index.html for the status strings this
    script cares about (it does not replicate the MARKED/COMPATIBLE aliasing)."""
    return re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-", str(status).lower()))


def validate(rows, is_accepted_file):
    errors = []
    seen_barcodes = {}

    for i, row in enumerate(rows):
        label = None
        if isinstance(row, dict):
            label = row.get("id")
        label = label or "row[{}]".format(i)

        if not isinstance(row, dict):
            errors.append("{}: not an object".format(label))
            continue

        is_fixture = row.get("fixture") is True

        if is_accepted_file and is_fixture:
            errors.append("{}: fixture:true is never allowed in accepted.json".format(label))

        barcodes = row.get("barcodes")
        if not isinstance(barcodes, list) or not barcodes:
            errors.append("{}: barcodes must be a non-empty list".format(label))
            barcodes = []
        for code in barcodes:
            if not isinstance(code, str):
                errors.append("{}: barcode {!r} is not a string".format(label, code))
                continue
            if code in seen_barcodes:
                errors.append("{}: duplicate barcode {} (also on {})".format(label, code, seen_barcodes[code]))
            else:
                seen_barcodes[code] = label

        status = row.get("status")
        if status not in ALLOWED_STATUS:
            errors.append("{}: status {!r} not in allowed set {}".format(label, status, ALLOWED_STATUS))
        else:
            kebab = to_kebab(status)
            if "•" in kebab:
                errors.append("{}: status {!r} leaves a bullet in its CSS class ({!r})".format(label, status, kebab))

        events = row.get("events")
        if events is None:
            events = []
        if not isinstance(events, list):
            errors.append("{}: events must be a list".format(label))
            events = []
        for j, ev in enumerate(events):
            ev_label = "{} event[{}]".format(label, j)
            if not isinstance(ev, dict):
                errors.append("{}: not an object".format(ev_label))
                continue
            if not ev.get("source_url"):
                errors.append("{}: missing source_url".format(ev_label))

    return errors


def main():
    if len(sys.argv) > 2:
        print("usage: py scripts/validate_seed.py [path-to-json]", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) == 2:
        arg = sys.argv[1]
        path = Path(arg)
        if not path.is_file():
            path = ROOT / arg
        if not path.is_file():
            raise SystemExit("file not found: {}".format(arg))
        rows = load_seed_from_json(path)
        label = str(path)
    else:
        path = INDEX_PATH
        rows = load_seed_from_index(path)
        label = "index.html SEED (live)"

    is_accepted_file = path.name == "accepted.json"
    errors = validate(rows, is_accepted_file)

    print("validating: {} ({} rows)".format(label, len(rows)))
    if errors:
        print("FAIL: {} issue(s)".format(len(errors)))
        for e in errors:
            print("  - {}".format(e))
        sys.exit(1)

    print("PASS: no issues found")


if __name__ == "__main__":
    main()
