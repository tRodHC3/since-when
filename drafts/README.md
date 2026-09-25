# Drafts

Nothing in this folder is loaded by `index.html`. The app only knows products that are pasted into the `SEED` array. These scripts do not write `index.html`. Running them promotes nothing.

## Four layers

| Layer | Where | What it means |
| --- | --- | --- |
| Catalog | `drafts/<brand>.json` | Identity only: `gtin`, `name`, `brand`, `image_url`. No verdict. |
| Proposed | `drafts/proposed/<brand>.json` | Seed-shaped UNKNOWN stubs. Not a verdict. |
| Accepted | `drafts/accepted.json` | A row you said yes to, with the status you passed on the command line. Still not live. |
| Seed | `SEED` in `index.html` | Live. Paste an accepted object here yourself when the app should use it. |

Catalog = identity. Proposed = UNKNOWN stubs. Accepted = you said yes. Seed = live.

## Commands

Run from the repo root. The pull uses the Open Food Facts brand search with a cap of 50. It does not download the world dump. A failed request writes an empty catalog file, prints the error, and does not retry.

```bash
py scripts/pull_off_brand.py "Cabot" --limit 50 --out drafts/cabot.json
py scripts/pull_off_brand.py "Coca-Cola" --limit 50 --out drafts/coca-cola.json
py scripts/propose_seed.py drafts/tillamook.json
py scripts/accept_row.py --gtin GTIN --status CLEAR --note "Pack inspected. No halal mark."
py scripts/accept_row.py --gtin GTIN --status HALAL --source-url https://www.ifanca.org/ --note "IFANCA mark on this pack."
```

`propose_seed.py` reads one catalog file and writes `drafts/proposed/<brand>.json`. Every stub is `UNKNOWN`, `fixture` false, `pack_claim` null, `enzyme` null, with one `pack_inspection` event (`verified_on` `2026-09-25`). It skips:

- a row with no gtin
- a gtin already on any `SEED` barcode (the skipped list is printed, with the live status)
- a Tillamook product whose name is clearly ice cream or a frozen dessert

Those ice cream rows stay in `drafts/tillamook.json`. They are not proposed. Tillamook's FAQ says ice cream is not halal certified. This script does not turn that into a seed status.

`accept_row.py` looks up the gtin in `drafts/*.json` (catalog files only, not `proposed/` and not `accepted.json`). It prints one seed object to stdout and appends that same object to `drafts/accepted.json`.

Allowed `--status` values: `CLEAR`, `HALAL`, `HALAL • NO MARK`, `ANIMAL RENNET`, `PORK`, `UNKNOWN`. Anything else exits 1.

`HALAL`, `HALAL • NO MARK`, `PORK`, and `ANIMAL RENNET` require `--source-url` or the script exits 1. `CLEAR` and `UNKNOWN` may omit it. The event then uses the Open Food Facts product page as a non-certifier source, plus your `--note`. That is not a certifier URL.

`CLEAR` and `UNKNOWN` use `field` `pack_inspection`. `ANIMAL RENNET` uses `rennet`. The other allowed statuses use `certification`. `pack_claim` and `enzyme` stay null. `fixture` stays false.

If the gtin is already on a `SEED` barcode, the script refuses, prints the live id and status, and does not append. Example: `072830011211` is already seeded HALAL, and `049000555318` is already seeded CLEAR.

## Data source and license

Product data is from [Open Food Facts](https://world.openfoodfacts.org/), licensed under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/). Open Food Facts contributors retain their rights. Any redistribution of this data must credit Open Food Facts and remain ODbL-compatible.

## Planned brand order

US products, roughly in the order we intend to work through them:

1. Tillamook
2. Cabot
3. Coca-Cola (sparkling)
4. One marshmallow brand (TBD)
