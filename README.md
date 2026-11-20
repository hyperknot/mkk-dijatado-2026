# MKK 2026 award ceremony slides

The slide deck of the MKK 2026 award ceremony (Magyar Köztársaság Kupa, Hungarian XContest paragliding league; ceremony 2026-11-20). Plain HTML with [reveal.js](https://revealjs.com/), no server, no internet needed.

- Online: https://hyperknot.github.io/mkk-dijatado-2026/ (GitHub Pages from `main`, live about a minute after a push)
- Offline (USB stick): copy the whole folder, open `index.html` in a browser.
- Presenting: arrow keys / space / clicker, `F` full screen, `Esc` overview, `S` speaker view. `#/12` in the URL is slide 13 (0-based).

## Layout

```
index.html            GENERATED, never edit by hand
src/build.py          builds index.html: DECK (slide order), name/photo/takeoff fixes, result slide HTML
src/charts.py         the MKK charts of the budget and stats slides as inline SVG (no JS), from the two files below
src/mkk_finances.json MKK costs and income per year (2011–2026), every value with its source
src/mkk_stats.json    MKK statistics per year (2007–2026) for the stats slide chart
src/slides/*.html     hand-written slides, one or more <section> per file
src/results.json      the results data (rankings, flights, clubs, KMK), from export_results.py
src/template.html     the page around the slides (reveal.js setup)
src/export_results.py makes results.json; runs only in the private validation repo (see the file)
assets/css/style.css  all styling; slides are a 1920x1080 canvas, reveal.js scales it
assets/img/photos/    pilot photos, <xcontest username>.jpg
assets/img/logos/, assets/img/charts/, assets/img/bg.jpg, assets/fonts/ (Raleway), vendor/reveal/
```

## Workflow

1. `git pull` first; others edit too.
2. Edit `src/` (or `assets/`).
3. Run `./src/build.py` (needs only `uv`; or `python3 src/build.py`, standard library only).
4. Check the changed slides (below), then commit `src/` and `index.html` together and push.

A merge conflict in `index.html`: resolve `src/`, then rebuild instead of merging `index.html`.

Common changes:

- **Text of a hand-written slide** (title, sponsors, budget, stats, records, thanks): edit its file in `src/slides/`.
- **New slide**: add `src/slides/<name>.html` with `<section>...</section>` and put `'<name>'` into `DECK` in `src/build.py` at its place. Use the existing classes (`cover`, `panel`, `card`, `fact`, `two-col`, ...) from `style.css`.
- **Budget and stats charts**: edit the numbers in `src/mkk_finances.json` / `src/mkk_stats.json` (keep the `source`, drop a key from `estimate` / `unsure` / `missing` when it becomes final), then rebuild. The slides have `<!-- chart:NAME -->` placeholders that `build.py` fills.
- **Result slides** (categories, KMK, clubs) are generated from `src/results.json`; change the generator in `src/build.py`, not the output.
- **Pilot photo**: put `assets/img/photos/<username>.jpg` (about 1000 px, JPEG). Without a photo the slide shows the initials. If the face is cut off, add the username to `FOCUS` in `build.py` (CSS `object-position`, e.g. `'70% 30%'`).
- **Pilot name**: podium slides use `HU` in `build.py` (the names engraved on the cups, Hungarian order); everyone else keeps the XContest name.
- **Takeoff shown as "?"**: add the flight to `TAKEOFF` in `build.py`.

## Rules for content

- **Correct or red.** Every number and name that is not verified and current gets a red frame: wrap it in `<div class="stale" data-warn="RÉGI ADAT: 2025">...</div>` (the label is `data-warn`). Remove the `stale` class only after updating it from a real source. Everything without a red frame must be correct for 2026.
- Never invent facts, names, expansions of abbreviations or numbers. If there is no source, leave it out or mark it red.
- Slide text is Hungarian, short, no emojis.
- Photos: the pilot's XContest profile photo if it shows the face, else the pilot's own photo from an earlier MKK deck (2025 Google Slides "MKK 2025"; the 2026 Google Slides copy had other people's photos under new names, don't use it).

## Sources

- Results: our own validation of all flights (final, 2026-10-15; objection period closed 10-28). Names on the podium: the cup order.
- Stats slide: the XContest MKK pilot list (https://www.xcontest.org/hungary/pilotak/ and `/2025/hungary/pilotak/`), 2026-11-17. The chart: `src/mkk_stats.json` (2007–2025 mostly read off the old Excel chart image of the 2025 deck, which is in git history before the SVG charts; no source table exists). 2026 légtérsértés (KO), 100+ KO (KO flights with 100+ points) and klub (clubs in the PG Klub ranking; in the data, not drawn on the chart) come from the validation repo (`../src`, final `pont.html` and `lib/scoring.py`). táv: estimated as valid flights of at least 10 km (right axis; fits the old chart).
- Budget slide: `src/mkk_finances.json` (sources per year: Fichtinger's `MKK12_év.xlsx` 2011–2023 (`/Users/user/Documents/life/paragliding/2024/MKK/eloadas 2023/`), the 2023 deck, his ledger, invoices, the SIRESZ eTitkár Sportalap page). The Sárkányrepülésért Alapítvány paid nothing in 2026 (user, 2026-11-20). Nothing is labeled as an estimate: what is not certain is red. XContest in Ft: the EUR invoice × the ECB rate on the invoice date, exact. SIRESZ Sportalap (általános) covers the rest of every year, so it is computed. Server costs and SVB fuel are not MKK costs.
- Records and Repülés Éjszakája: https://szakbizottsag.hu/rekordok/ and https://szakbizottsag.hu/
- Route type colors follow XContest: FAI triangle blue, flat triangle green, free distance orange.

## Checking slides

Open `index.html` and go through the changed slides. Headless screenshot of one slide (macOS Chrome):

```sh
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --hide-scrollbars \
  --window-size=1920,1080 --virtual-time-budget=2500 --screenshot=/tmp/slide.png \
  "file://$PWD/index.html#/13"
```

Look for text overflowing a card, overlapping red labels, and cropped faces.
