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

The Node render test uses a minimal in-memory DOM harness. Browser automation was disabled in this environment, so it does not establish screenshot appearance, actual responsive layout, keyboard behavior or download UI behavior. Those checks remain manual in Edge, Chrome or Firefox. No native Power BI report or browser screenshot is represented as having been created.

Reproduce with `python -m pytest -q` using the project virtual environment, then start `python -m src.dashboard` and run `node scripts/check-dashboard.mjs`. Test results are recorded in `test-results.xml`. For usage see `dashboard/README.md`.
