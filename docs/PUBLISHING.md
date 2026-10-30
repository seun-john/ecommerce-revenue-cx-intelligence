# GitHub Pages deployment

The public dashboard is a static application served from `docs/`. It needs no Python server, backend account, paid hosting or custom domain. The four-page layout is shared with the local application. `static-api.js` supplies the data-request interface and `engine.js` computes filters in the visitor's browser.

## Rebuild after source changes

```powershell
& .venv\Scripts\python.exe -m src.pipeline
& .venv\Scripts\python.exe -m src.build_pages
node scripts/check-pages.cjs
& .venv\Scripts\python.exe -m pytest -q
```

`build_pages` copies the shared UI into `docs/`, generates `analytics.json.gz` and creates aggregate-only parity fixtures in `tests/fixtures/pages-parity.json`. `check-pages.cjs` compares every KPI and all nine result tables with those direct DuckDB calculations for 11 populations. The deployment workflow runs the same reconciliation before publishing. Keep the generated website files, fixtures and analytical extract together in the same commit.

The Pages workflow uploads `docs/` as the website artifact and deploys it through GitHub Actions. The site is configured with `build_type=workflow`. Pushes to main trigger deployment; the repository's Actions tab records deployment success and the published URL. Public repository Pages hosting uses GitHub's supplied github.io address, with no purchased domain required.

## Local static preview

```powershell
& .venv\Scripts\python.exe -m http.server 8766 --bind 127.0.0.1 --directory docs
```

Open `http://127.0.0.1:8766/`. In a second terminal, run `node scripts/check-dashboard.mjs http://127.0.0.1:8766 --static` to exercise the compressed-data adapter, all page renderers and filters. This is a DOM logic test harness, not visual browser automation. Modern browsers supporting DecompressionStream are required.

## Published data boundary

The approximately 2.8 MB compressed analytical extract is derived from the original public Olist dataset and retains the CC BY-NC-SA 4.0 licence. It includes exact purchase dates, item prices/freight, payment totals, categories, states, selected review scores, delivery outcomes/durations and coded relationships needed for correct order counts and repeat analysis. It is publicly downloadable with the site; it is not a confidential dataset.

Source order, customer and seller identifiers are removed. Customer identities are replaced with extract-local integer codes for repeat analysis; seller IDs become S0001-style codes, retaining public seller city. No review text, ZIP prefixes, coordinates, secrets or credentials are included. These transformations reduce disclosure and download size but are not a formal anonymisation guarantee. Raw source CSVs, full BI row exports and DuckDB files remain excluded from Git.

The public engine sums monetary values as integer centavos before converting to BRL. Category service metrics use orders containing matching items; category item metrics use matching items only. Seller reviews/delivery outcomes remain seller-order associations, not individual seller fault. Source manifest hashes and the pipeline remain available for reproducibility.
