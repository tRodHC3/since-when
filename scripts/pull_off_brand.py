"""One-off local script: pull product identity rows for one brand from Open Food Facts.

Not part of the app. Not imported by index.html. Run manually, by hand, when starting
a new drafts/<brand>.json file.

Usage:
    python scripts/pull_off_brand.py "Tillamook" [--limit 50] [--out drafts/tillamook.json]

Calls the Open Food Facts brand search endpoint (not the full world data dump),
with a small page size, and writes an array of identity-only rows:
    [{"gtin": "...", "name": "...", "brand": "...", "image_url": "..."}, ...]

Rows with no barcode are skipped. Barcodes are normalized toward the same
12-digit string index.html uses for lookup (leading zeros stripped down to
12 digits), matching normalizeBarcode() in index.html. If a code can't be
reduced to 12 digits that way, the digits-only code is kept as-is.

This script does not retry on failure. A network error writes an empty
drafts/<brand>.json and prints the error, so a failed run is visible and
does not hang.
"""

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request

SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
USER_AGENT = "since-when-draft-puller/0.1 (one-off local script; contact: trodhc@proton.me)"


def normalize_gtin(raw):
    code = re.sub(r"\D", "", str(raw or ""))
    while len(code) > 12 and code.startswith("0"):
        code = code[1:]
    return code


def fetch_brand(brand, limit):
    params = {
        "search_terms": brand,
        "tagtype_0": "brands",
        "tag_contains_0": "contains",
        "tag_0": brand,
        "json": "1",
        "page_size": str(limit),
        "page": "1",
        "fields": "code,product_name,brands,image_url",
    }
    url = SEARCH_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def to_rows(payload, brand, limit):
    rows = []
    for product in payload.get("products", [])[:limit]:
        gtin = normalize_gtin(product.get("code"))
        if not gtin:
            continue
        rows.append({
            "gtin": gtin,
            "name": product.get("product_name") or "",
            "brand": product.get("brands") or brand,
            "image_url": product.get("image_url") or "",
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description="Pull identity-only rows for one brand from Open Food Facts.")
    parser.add_argument("brand", help="Brand string to search, e.g. Tillamook")
    parser.add_argument("--limit", type=int, default=50, help="Max rows to write (default 50, OFF page size stays small)")
    parser.add_argument("--out", default=None, help="Output path (default drafts/<brand>.json)")
    args = parser.parse_args()

    limit = max(1, min(args.limit, 50))
    out_path = args.out or "drafts/{}.json".format(args.brand.strip().lower().replace(" ", "-"))

    try:
        payload = fetch_brand(args.brand, limit)
        rows = to_rows(payload, args.brand, limit)
    except Exception as exc:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
            f.write("\n")
        print("ERROR: Open Food Facts request failed: {}".format(exc), file=sys.stderr)
        print("Wrote empty {}".format(out_path))
        sys.exit(1)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
        f.write("\n")

    print("Wrote {} row(s) to {}".format(len(rows), out_path))


if __name__ == "__main__":
    main()
