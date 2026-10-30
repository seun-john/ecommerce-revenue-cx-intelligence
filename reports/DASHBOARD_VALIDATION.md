# Local dashboard validation

Validation performed on 30 October 2026 using the original downloaded Olist model.

| Check | Result |
|---|---|
| Python suite | 28 passed; includes 17 original pipeline tests and 11 dashboard/API test cases |
| JavaScript syntax | `node --check dashboard/app.js` passed |
| Live server | HTTP 200 for the dashboard and API metadata |
| All-source count | 99,441 orders, matching pipeline metrics |
| Delivered population | 96,478 orders; delivered GMV and AOV match pipeline metrics |
| Category/state/date filters | Selected item GMV and distinct order count reconcile to direct SQL |
| Missing outcomes | Canceled orders have no eligible delivery rate; empty selections retain null averages |
| Order multiplication | Category selection uses EXISTS; item and order populations remain distinct |
| CSV export | Correct filtered data, content type and download headers |
| Static paths | Data, Git configuration and traversal paths return 404 |
| Four page render functions | Passed live API test harness with populated and empty selections |
| Date validation | Reversed dates rejected by the UI logic and API |
| GitHub Pages engine | All KPIs and nine analytical tables match DuckDB across 11 filter populations |
| Public data pack | 99,441 coded orders and 112,650 coded item records; approximately 2.8 MB compressed; no source identifiers or review text |

The Node render test uses a minimal in-memory DOM harness. During initial local development, browser automation was unavailable. After publication, the live Executive Overview and Customer Experience pages were checked in the in-app browser; clicking the SP chart bar correctly selected 41,746 orders, and Reset restored 99,441. A clipped currency value was corrected and verified visually after deploying versioned assets. `figures/live-dashboard.png` is a real screenshot of the final published Executive Overview. Full responsive, keyboard and browser download audits remain unverified. No native Power BI report has been created.

GitHub Actions successfully deployed the static application. The public site returned HTTP 200, and its served analytical data passed the four-page render/filter harness. The Python validation workflow also passed in GitHub; data-dependent Python tests skip there because raw files and the local database are intentionally excluded. All 28 tests passed locally against the real model.

Reproduce with `python -m pytest -q` using the project virtual environment, then start `python -m src.dashboard` and run `node scripts/check-dashboard.mjs`. Test results are recorded in `test-results.xml`. For usage see `dashboard/README.md`.
