# Changelog

## Unreleased

## 0.5.1 — 2026-09-25
- UNKNOWN result: new "Submit this code" button opens a public GitHub issue (`.github/ISSUE_TEMPLATE/unknown.yml`) in a new tab, barcode pre-filled in the title and form field. No token in the page.
- Footer added to Scan, Result, and Learn screens: "Not a ruling. Sources linked. Product names may come from Open Food Facts (ODbL)." with a credit link to https://openfoodfacts.org
- README: one line on how to submit an unknown barcode
- Decisions recorded (not yet implemented):
  - A photographed pack counts as accepted evidence for a seed row, alongside a `source_url`
  - v1.1: an APK build will fetch seed data remotely with a local seed fallback if the fetch fails
  - Seed rows get re-checked on a 12/6-month cadence; an overdue banner will show once a row's `verified_on` ages past that window

## 0.5.0 — 2026-09-25
- Result screen: short tagline under the product name per status (HALAL/HALAL • NO MARK/CLEAR/PORK/ANIMAL RENNET/UNKNOWN); giant status word unchanged
- Why panel: Enzyme type row hidden when enzyme is null, instead of printing "unknown"
- Learn tab: trimmed ANIMAL RENNET card under 60 words; other cards unchanged
- New scripts/validate_seed.py: validates index.html SEED or any drafts JSON file (source_url, barcode types, allowed status, no bullet in CSS class, no duplicate barcodes, no fixture:true in accepted.json)
- New scripts/test_pipeline.py: 5 behavioral checks against the live pipeline, all passing
- drafts/NOTES.md added
- Haribo and Jet-Puffed identity pulls attempted (drafts/haribo.json, drafts/jet-puffed.json) — Open Food Facts returned 503 both times, so both files are empty and drafts/proposed/{haribo,jet-puffed}.json are empty too. Not finished: no real Haribo/Jet-Puffed rows exist yet; rerun scripts/pull_off_brand.py for these brands once OFF is reachable.

## 0.4.2 — 2026-09-25
- Pipeline scripts + Cabot/Coke draft pulls. App runtime unchanged.

## 0.4.1 — 2026-09-25
- Drafts catalog started; Tillamook identity pull; app runtime unchanged

## 0.4.0 — 2026-09-24
- Inverted colors; HALAL/NO MARK are warnings; CLEAR is inspected with no cert; Sprite moved to CLEAR

## 0.3.1 — 2026-09-24
- Sprite Chill Cherry Lime `049000555318` UNKNOWN from pack; no halal mark

## 0.3.0 — 2026-09-23
- First real pack UPC: Tillamook Farmstyle Shreds Mozzarella 8 oz `072830011211`
- Status HALAL from IFANCA mark photographed on this bag
- labeled_on left unspecified; verified_on 2026-09-23
- Demo button: Mozzarella shreds
- Cheddar demo code unchanged (HALAL • NO MARK)

## 0.2.0 — 2026-09-22
- Public repo and GitHub Pages https://trodhc3.github.io/since-when/
- Phone camera works over HTTPS
- Last-scan chip, v2 cache, OFF race guard
- Why labels: Recipe changed / Box said so / Source checked

## 0.1.0 — 2026-09-19
- First demo buttons and Learn tab
- Statuses: HALAL, HALAL • NO MARK, ANIMAL RENNET, PORK, UNKNOWN
