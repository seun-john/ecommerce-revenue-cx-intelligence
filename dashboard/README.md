# Local commerce intelligence dashboard

Four interactive pages query the existing real Olist DuckDB model. No account, cloud service, JavaScript package installation or Power BI licence is needed. The Python environment already contains the only analytical dependency used by the server: DuckDB. Assets and queries run locally; there are no external fonts, scripts or telemetry calls.

## Open

From PowerShell in the project root:

```powershell
& .venv\Scripts\python.exe -m src.dashboard
```

Open **http://127.0.0.1:8765** in Edge, Chrome or Firefox. Keep the terminal open. Stop with Ctrl+C. Alternatively run `powershell -ExecutionPolicy Bypass -File scripts\dashboard.ps1`.

If the project environment or database is missing, run `scripts\run.ps1` first. If port 8765 is in use, run `python -m src.dashboard --port 8766` using the virtual environment executable, then open that port. Binding is restricted to the computer's loopback interface; this is a local single-user dashboard, not a hosted application. Do not expose it on a public network.

## Explore

- **Executive overview:** item GMV, orders, AOV, delivery promise misses, monthly trends and regional detail.
- **Sales & products:** category contribution, shipping-charge burden and a complete category table.
- **Delivery & operations:** late rate, delivery durations, regional exceptions, seller review table and order statuses.
- **Customer experience:** review distribution, low-score share, delivery/review comparison and observed repeat purchasing.

Set purchase dates, destination state, order status and category, then click **Apply filters**. Filters persist when switching pages. The message and footer show the applied population. Changes remain pending until applied. **Full extract** and **Jan 2017–Aug 2018** presets change dates; **Reset** also clears other filters. Click category or state bars/table labels to filter. Every data panel responds to the applied filters.

**Category semantics:** item GMV and freight use only items in the chosen category. Order, service, payment and repeat metrics use whole orders containing that category, selected through EXISTS rather than a multiplying join. Therefore category-filtered payment totals are not payments allocated to category items. The interface explains this distinction. Canceled/undated orders do not become eligible delivered orders.

**Export current table** downloads the main aggregate table for the current page with applied filters: regions, categories, sellers or delivery/review comparison. All endpoints are read-only and monetary amounts are denominated in BRL. For other aggregate tables, use `/api/export?table=monthly` or `categories`, `regions`, `reviews`, `comparison`, `sellers`, `statuses`, `repeats`, `durations` with the same query filters. No raw order/customer export endpoint is exposed.

**Metric definitions** explains populations and limitations. Browser print/PDF can print the current page. The native Power BI report remains a separate artifact; this dashboard is a functional local alternative, not a PBIX or a DAX runtime.

## Validation

```powershell
& .venv\Scripts\python.exe -m pytest -q
node --check dashboard/app.js
node scripts/check-dashboard.mjs
```

The final command requires the local server to be running and Node.js installed; it uses a minimal DOM test harness with live API results. It exercises all four render functions, applied filters, empty results and date validation. It does not launch a browser or establish visual correctness.

The Python tests reconcile unfiltered and delivered dashboard totals against the original pipeline, check category/state/date intersections, unknown delivery outcomes, empty selections, parameter validation, HTTP responses, CSV downloads and static-file restrictions. SQL filter values are bound parameters. Static routes are allowlisted; the server does not expose the project directory, database or credentials. All data values are HTML-escaped in chart/table labels.

Browser automation was unavailable during the initial local build. After publication, the Executive Overview and Customer Experience pages and chart-based state filtering were checked in the in-app browser. `reports/figures/live-dashboard.png` is a real screenshot of the published dashboard. The other PNGs in reports/figures are Python analytical outputs. Full responsive, keyboard-navigation and CSV download UI checks remain unverified; the API/download data and render logic have automated coverage.

## Refresh and portability

Stop the server before rebuilding `src.pipeline`, then restart. Each API request opens the database read-only, uses connection-local temporary tables and closes the connection. The source and dashboard result populations remain aligned. The app loads the latest build status on opening; refresh the page after rebuilding. The files are plain HTML/CSS/JS plus Python standard-library HTTP serving and DuckDB, compatible with Windows 11.
