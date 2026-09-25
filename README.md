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

## Android APK

This is a thin [Capacitor](https://capacitorjs.com) sideload wrapper around the exact same `index.html` GitHub Pages serves — no rewrite, no framework, `SEED` stays where it is. The web app itself still runs fine in any browser or via `python -m http.server` as above; this section is only for building an installable `.apk`.

`capacitor.config.json` sets `webDir: "www"`, not the repo root — Capacitor's CLI hard-rejects `.`/`./`/`..` as a webDir (it refuses to run, not a config choice). `www/index.html` is a Windows hard link to the root `index.html` (same file on disk, not a copy), created once with:

```powershell
New-Item -ItemType Directory -Path www -Force
New-Item -ItemType HardLink -Path www\index.html -Target index.html -Force
```

Hard links can silently break if an editor saves by writing a temp file and renaming it over the original, rather than writing in place. Don't assume the link is still live — the copy step below is what actually guarantees `www/index.html` is fresh before every build.

### Prerequisites

- [Node.js](https://nodejs.org) (LTS). Installed on this machine at `C:\Program Files\nodejs`, not on `PATH` — either add it to `PATH` or call `node`/`npm`/`npx` with the full path.
- A JDK (17 recommended) with `JAVA_HOME` set. **Not currently installed on this machine.**
- Android SDK command-line tools (or Android Studio, which bundles them), with `ANDROID_HOME` set and `android/local.properties` pointing at it (Capacitor/Gradle will generate `local.properties` once `ANDROID_HOME` is set, or you can write `sdk.dir=C:\\Users\\<you>\\AppData\\Local\\Android\\Sdk` by hand). **Not currently installed on this machine.**

### Build (Windows, PowerShell)

```powershell
npm install
Copy-Item index.html www\index.html -Force   # guarantee www is fresh even if the hard link broke
npx cap sync
cd android
.\gradlew.bat assembleDebug
```

Debug APK output path: `android\app\build\outputs\apk\debug\app-debug.apk`

### Sideload onto a Pixel

1. On the phone: Settings → About phone → tap "Build number" 7 times to enable Developer options.
2. Settings → System → Developer options → enable "USB debugging" (for `adb install`) or just enable "Install unknown apps" for the browser/file manager you'll use to open the APK.
3. Either:
   - `adb install android\app\build\outputs\apk\debug\app-debug.apk` with the phone connected over USB, or
   - copy `app-debug.apk` to the phone (email, cloud drive, USB file transfer) and tap it in a file manager to install.
4. First launch will prompt for camera permission — accept it for the barcode scanner to work.
