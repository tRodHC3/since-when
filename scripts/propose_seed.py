"""Turn one drafts/<brand>.json catalog into UNKNOWN seed stubs.

Not part of the app. Does not edit index.html. Does not assign a verdict.
Every proposed row is status UNKNOWN until you accept it yourself.

Usage (from the repo root):
    py scripts/propose_seed.py drafts/tillamook.json

Writes drafts/proposed/<brand>.json. Skips rows with no gtin, gtins already
on any SEED barcode, and Tillamook products whose names are clearly ice cream
or a frozen dessert. Those ice cream rows stay in the catalog file.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "index.html"
VERIFIED_ON = "2026-09-25"
OFF_SOURCE = "https://world.openfoodfacts.org/"
FROZEN_RE = re.compile(r"ice[\s-]*cream|frozen\s+desserts?", re.IGNORECASE)


def normalize_gtin(raw):
    """Same digit rule as scripts/pull_off_brand.py."""
    code = re.sub(r"\D", "", str(raw or ""))
    while len(code) > 12 and code.startswith("0"):
        code = code[1:]
    return code


def load_seed(path):
    text = path.read_text(encoding="utf-8")
    marker = "var SEED = "
    start = text.find(marker)
    if start < 0:
        raise SystemExit("SEED array not found in {}".format(path))
    data, _ = json.JSONDecoder().raw_decode(text[start + len(marker):])
    if not isinstance(data, list):
        raise SystemExit("SEED is not a list in {}".format(path))
    return data


def seed_index(seed):
    found = {}
    for row in seed:
        status = row.get("status")
        row_id = row.get("id")
        for code in row.get("barcodes") or []:
            key = normalize_gtin(code)
            if key and key not in found:
                found[key] = {"id": row_id, "status": status}
    return found


def slugify(text):
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def make_id(brand, product, gtin, used):
    brand_bit = slugify((brand or "").split(",")[0]) or "brand"
    product_bit = slugify(product) or gtin or "product"
    base = "{}-{}".format(brand_bit, product_bit)
    if len(base) > 80:
        base = base[:80].rstrip("-")
    candidate = base
    n = 2
    while candidate in used:
        suffix = gtin if n == 2 else str(n)
        candidate = "{}-{}".format(base, suffix).strip("-")
        n += 1
    used.add(candidate)
    return candidate


def is_tillamook_frozen(row, stem):
    name = row.get("name") or ""
    brand = row.get("brand") or ""
    tillamook = (
        stem.lower() == "tillamook"
        or "tillamook" in brand.lower()
        or "tillamook" in name.lower()
    )
    if not tillamook:
        return False
    return FROZEN_RE.search(name) is not None


def stub_event():
    return {
        "effective_on": None,
        "labeled_on": None,
        "verified_on": VERIFIED_ON,
        "field": "pack_inspection",
        "old_value": None,
        "new_value": "Catalog identity only. No verdict accepted.",
        "source_url": OFF_SOURCE,
        "notes": "From OFF catalog draft. Not CLEAR, not HALAL, not PORK.",
    }


def to_seed(row, gtin, used):
    brand = row.get("brand") or ""
    product = row.get("name") or ""
    return {
        "id": make_id(brand, product, gtin, used),
        "barcodes": [gtin],
        "brand": brand or None,
        "product": product,
        "status": "UNKNOWN",
        "fixture": False,
        "pack_claim": None,
        "enzyme": None,
        "events": [stub_event()],
    }


def resolve_draft(arg):
    path = Path(arg)
    if not path.is_file():
        path = ROOT / arg
    if not path.is_file():
        raise SystemExit("draft not found: {}".format(arg))
    return path


def main():
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print("usage: py scripts/propose_seed.py drafts/<brand>.json", file=sys.stderr)
        sys.exit(0 if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help") else 1)

    draft_path = resolve_draft(sys.argv[1])
    stem = draft_path.stem
    catalog = json.loads(draft_path.read_text(encoding="utf-8"))
    if not isinstance(catalog, list):
        raise SystemExit("{} is not a JSON array".format(draft_path))

    seeded = seed_index(load_seed(INDEX_PATH))
    proposed = []
    used_ids = set()
    seen = set()
    skipped_gtin = []
    skipped_seeded = []
    skipped_frozen = []
    skipped_dup = []

    for row in catalog:
        if not isinstance(row, dict):
            skipped_gtin.append("(not an object)")
            continue
        gtin = normalize_gtin(row.get("gtin"))
        name = row.get("name") or ""
        if not gtin:
            skipped_gtin.append(name or "(blank)")
            continue
        if gtin in seen:
            skipped_dup.append(gtin)
            continue
        seen.add(gtin)
        if gtin in seeded:
            hit = seeded[gtin]
            skipped_seeded.append("{} {} {}".format(gtin, hit.get("status"), hit.get("id")))
            continue
        if is_tillamook_frozen(row, stem):
            skipped_frozen.append("{} {}".format(gtin, name))
            continue
        proposed.append(to_seed(row, gtin, used_ids))

    out_path = draft_path.parent / "proposed" / "{}.json".format(stem)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(proposed, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print("draft: {}".format(draft_path))
    print("catalog: {}".format(len(catalog)))
    print("proposed: {}".format(len(proposed)))
    print("wrote: {}".format(out_path))
    print("skipped no gtin: {}".format(len(skipped_gtin)))
    for line in skipped_gtin:
        print("  {}".format(line))
    print("skipped already seeded: {}".format(len(skipped_seeded)))
    for line in skipped_seeded:
        print("  {}".format(line))
    print("skipped tillamook ice cream / frozen dessert: {}".format(len(skipped_frozen)))
    for line in skipped_frozen:
        print("  {}".format(line))
    if skipped_dup:
        print("skipped duplicate gtin: {}".format(len(skipped_dup)))
        for line in skipped_dup:
            print("  {}".format(line))


if __name__ == "__main__":
    main()
