# Since When

Work in progress. Most real barcodes stay UNKNOWN until a source is accepted.

A local, single-file barcode lookup. Scan or type a UPC/EAN and see one status word plus a dated source history. Seeded products win over Open Food Facts. Unseeded barcodes stay **UNKNOWN**.

## Open the app

Do not double-click `index.html` and expect the camera or last-scan cache to work.

`file://` has no real origin. Camera permission and `localStorage` are unreliable there, and an in-browser phone preview will often fail.

Serve the folder over HTTP instead:

```bash
python -m http.server 8000
```

On Windows you can also use:

```bash
py -m http.server 8000
```

Then open [http://localhost:8000](http://localhost:8000).

Typed lookup and the seven demo buttons work without a camera.

## Demo buttons

On the scan screen, these load **seed rows only**. They never call Open Food Facts.

| Button | Barcode | Status |
| --- | --- | --- |
| Tillamook cheddar | `000000000001` | HALAL • NO MARK |
| Mozzarella shreds | `072830011211` | HALAL (real UPC from the pack) |
| Sprite Chill | `049000555318` | CLEAR (this UPC is real) |
| Maker's Reserve 10-Year | `000000000002` | ANIMAL RENNET |
| Rocky Road | `000000000003` | PORK |
| Marked test fixture | `000000000004` | HALAL (TEST badge; not saved) |
| Unknown barcode | `000000000099` | UNKNOWN |

## Add one event row

1. Open `index.html` and find the product in the `SEED` array.
2. Append one object to that product's `events` array. Keep authored order; the UI renders rows in array order.
3. Every real event **must** include a `source_url`. If there is no source, the row does not exist.
4. The only exception is a row with `"fixture": true`, which may use `https://example.invalid/fixture`.
5. Fill the fields:

```js
{
  "effective_on": "2016",      // or null → shown as "Date unspecified"
  "labeled_on": null,
  "verified_on": "2026-09-18",
  "field": "rennet",
  "old_value": "unspecified / prior enzyme",
  "new_value": "fermentation-produced rennet…",
  "source_url": "https://example.com/source-page",
  "notes": "Short source note."
}
```

6. Do not invent dates or verdicts. Change `product.status` only when a source supports it. Status must be one of `HALAL`, `HALAL • NO MARK`, `CLEAR`, `ANIMAL RENNET`, `PORK`, `UNKNOWN`.
7. Add the barcode to `barcodes` only for that SKU. Do not copy another SKU's status onto a different barcode.
8. Barcodes are stored as the 12-digit UPC-A printed on the pack, because a 13-digit EAN-13 scan is normalized down to 12 before lookup.

## Submit an unknown barcode

On an UNKNOWN result, tap **Submit this code** to open a public GitHub issue (via `.github/ISSUE_TEMPLATE/unknown.yml`) pre-filled with the barcode. You'll need a GitHub account; do not attach photos with location data on.

## Lookup order

1. Seed table match → use the seed row. No network.
2. Otherwise GET `https://world.openfoodfacts.org/api/v2/product/{barcode}.json?fields=product_name,brands,ingredients_text,image_url` (5s timeout). Name/brand/ingredients/image only. Status stays UNKNOWN.

## Catalog

US products we actually handle first, roughly in this order: Tillamook, then later Cabot, Coca-Cola sparkling, one marshmallow brand.

Unverified identity pulls for these brands live in `drafts/`, one JSON file per brand, each row `{gtin, name, brand, image_url}` only — no status field. `index.html` does not load `drafts/`. `propose_seed.py` writes UNKNOWN stubs under `drafts/proposed/`. `accept_row.py` appends a row you already chose to `drafts/accepted.json`. Neither script edits `index.html`. A product only gets a verdict (CLEAR, HALAL, PORK, etc.) when someone manually pastes a sourced seed row per the rules above; see `drafts/README.md` for the pipeline, the data source, and the license.

A human accepts a row by photographing the pack, running `accept_row.py --gtin ... --status ... --source-url ... --note ...` (source URL required for anything except CLEAR/UNKNOWN), checking the printed object against the pack, then pasting it into the `SEED` array in `index.html` by hand. `scripts/validate_seed.py` can check the shape before or after pasting. Two Claudes (or two people) must not edit this repo at once — one editor at a time, one commit at a time.
