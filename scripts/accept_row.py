"""Print one seed object for a catalog gtin and append it to drafts/accepted.json.

Not part of the app. Does not edit index.html. You paste into SEED yourself.

Usage (from the repo root):
    py scripts/accept_row.py --gtin GTIN --status CLEAR --note "Pack inspected."
    py scripts/accept_row.py --gtin GTIN --status HALAL --source-url https://example.com/source --note "Mark on this pack."

HALAL, HALAL • NO MARK, PORK, and ANIMAL RENNET require --source-url.
CLEAR and UNKNOWN may omit it. A gtin already on any SEED barcode is refused.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "index.html"
DRAFTS = ROOT / "drafts"
ACCEPTED_PATH = DRAFTS / "accepted.json"
VERIFIED_ON = "2026-09-25"
OFF_PRODUCT = "https://world.openfoodfacts.org/product/{}"

ALLOWED = (
    "CLEAR",
    "HALAL",
    "HALAL • NO MARK",
    "ANIMAL RENNET",
    "PORK",
    "UNKNOWN",
)
NEEDS_URL = ("HALAL", "HALAL • NO MARK", "PORK", "ANIMAL RENNET")


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


def seed_hit(seed, gtin):
    for row in seed:
        for code in row.get("barcodes") or []:
            if normalize_gtin(code) == gtin:
                return row
    return None


def catalog_files():
    files = []
    for path in sorted(DRAFTS.glob("*.json")):
        if path.name == "accepted.json":
            continue
        files.append(path)
    return files


def find_in_catalog(gtin):
    matches = []
    for path in catalog_files():
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print("ERROR: could not read {}: {}".format(path, exc), file=sys.stderr)
            sys.exit(1)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if isinstance(row, dict) and normalize_gtin(row.get("gtin")) == gtin:
                matches.append((path, row))
    return matches


def load_accepted():
    if not ACCEPTED_PATH.is_file():
        return []
    data = json.loads(ACCEPTED_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("{} is not a JSON array".format(ACCEPTED_PATH))
    return data


def already_accepted(rows, gtin):
    for row in rows:
        for code in row.get("barcodes") or []:
            if normalize_gtin(code) == gtin:
                return row
    return None


def slugify(text):
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def make_id(brand, product, gtin):
    brand_bit = slugify((brand or "").split(",")[0]) or "brand"
    product_bit = slugify(product) or gtin or "product"
    base = "{}-{}".format(brand_bit, product_bit)
    if len(base) > 80:
        base = base[:80].rstrip("-")
    return base


def event_field(status):
    if status in ("CLEAR", "UNKNOWN"):
        return "pack_inspection"
    if status == "ANIMAL RENNET":
        return "rennet"
    return "certification"


def build_object(row, gtin, status, source_url, note):
    brand = row.get("brand") or ""
    product = row.get("name") or ""
    url = source_url or OFF_PRODUCT.format(gtin)
    new_value = note or "Accepted as {}.".format(status)
    return {
        "id": make_id(brand, product, gtin),
        "barcodes": [gtin],
        "brand": brand or None,
        "product": product,
        "status": status,
        "fixture": False,
        "pack_claim": None,
        "enzyme": None,
        "events": [
            {
                "effective_on": None,
                "labeled_on": None,
                "verified_on": VERIFIED_ON,
                "field": event_field(status),
                "old_value": None,
                "new_value": new_value,
                "source_url": url,
                "notes": note or "",
            }
        ],
    }


def refuse(message):
    print(message)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Append one accepted seed object. Does not edit index.html.")
    parser.add_argument("--gtin", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--source-url", default=None)
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    status = args.status.strip()
    if status not in ALLOWED:
        refuse("ERROR: --status must be one of: {}. Got: {}".format(", ".join(ALLOWED), args.status))

    source_url = (args.source_url or "").strip()
    if status in NEEDS_URL and not source_url:
        refuse("ERROR: --status {} requires --source-url".format(status))
    if source_url and not (source_url.startswith("https://") or source_url.startswith("http://")):
        refuse("ERROR: --source-url must start with http:// or https://")

    gtin = normalize_gtin(args.gtin)
    if not gtin:
        refuse("ERROR: --gtin is empty")

    hit = seed_hit(load_seed(INDEX_PATH), gtin)
    if hit is not None:
        refuse(
            "REFUSED: {} is already in SEED as {} ({}). "
            "Did not append to drafts/accepted.json. Did not write index.html.".format(
                gtin, hit.get("status"), hit.get("id")
            )
        )

    matches = find_in_catalog(gtin)
    if not matches:
        refuse("ERROR: {} not found in drafts/*.json. Nothing written.".format(gtin))

    path, row = matches[0]
    if len(matches) > 1:
        print("using {} ({} catalog matches)".format(path, len(matches)), file=sys.stderr)

    accepted = load_accepted()
    prior = already_accepted(accepted, gtin)
    if prior is not None:
        refuse(
            "REFUSED: {} is already in drafts/accepted.json as {} ({}). "
            "Did not append again. Did not write index.html.".format(
                gtin, prior.get("status"), prior.get("id")
            )
        )

    obj = build_object(row, gtin, status, source_url, args.note.strip())
    accepted.append(obj)
    ACCEPTED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ACCEPTED_PATH, "w", encoding="utf-8") as handle:
        json.dump(accepted, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print("appended {} to {}".format(gtin, ACCEPTED_PATH), file=sys.stderr)
    json.dump(obj, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
