# Drafts

Unverified product identity pulled from [Open Food Facts](https://world.openfoodfacts.org/). Nothing here is loaded by the app.

## What this is

- One JSON file per brand: `drafts/<brand>.json`.
- Each row is identity only: `gtin`, `name`, `brand`, `image_url`.
- **No status field.** These rows do not say HALAL, CLEAR, PORK, or anything else. Verdicts only ever come from the seed table in `index.html`, sourced by hand per the rules in the top-level `README.md`.
- `index.html` does not read this folder. Promoting a row into the app means manually adding a seed entry with real sources, exactly like any other product.

## How rows get here

`scripts/pull_off_brand.py <brand>` calls the Open Food Facts brand search (small page size, not the full data dump) and writes `drafts/<brand>.json`.

## Data source and license

Product data is from Open Food Facts, licensed under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/). Open Food Facts contributors retain their rights; any redistribution of this data must credit Open Food Facts and remain ODbL-compatible.

## Planned brand order

US products, roughly in the order we intend to work through them:

1. Tillamook
2. Cabot
3. Coca-Cola (sparkling)
4. One marshmallow brand (TBD)
