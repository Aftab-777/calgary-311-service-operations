# Validation status

## Completed checks

- The source contains 385,723 unique request IDs within the required January–September cohort.
- Preserved CSV SHA-256 matches the extraction manifest.
- Python and independent SQLite counts, grouped totals, median and interpolated P90 reconcile.
- Ten unit fixtures pass for duplicates, zero-day closures, missing and malformed dates, future dates, open-record censoring, status contradictions, unknown statuses and empty/interpolated percentiles.
- Browser aggregation tests agree with the Python output and reconcile month/service filtered data.
- Six embedded Power BI CSV tables decode byte-for-byte to the model CSVs.
- Four dimension keys are unique and all fact references resolve.
- 59 project/report JSON files validate against 12 official Microsoft schemas. See `analysis/pbir_validation.json`.
- Overview, Open workload and Data quality browser pages were inspected. September and September plus WRS Cart Management filters produced independently checked values; reset restored full-cohort measures.
- Browser console inspection found no errors or warnings during the desktop page checks.
- A phone-sized viewport showed no document-level horizontal overflow. The title and export control were adjusted for narrow screens.
- Export summary downloaded a CSV whose unfiltered counts, median, P90 and snapshot date match the checked analysis.
- The [first GitHub Actions run](https://github.com/Aftab-777/calgary-311-service-operations/actions/runs/37180375946) passed the source checksum, unit tests, Python and SQL reconciliation, browser aggregation tests, model integrity checks, generated-file diff check, site-link validation and Pages deployment.
- The [public dashboard](https://aftab-777.github.io/calgary-311-service-operations/dashboard/) loaded with 381,923 nonduplicate requests, 25,636 Open and a two-day median. Its September plus WRS Cart Management filter produced 2,475 requests, 42 Open, 2,433 valid closures, median one day and P90 four days. Workload and quality pages, methodology and guide links loaded; browser console showed no errors or warnings during the public checks.

The evidence files under `analysis/` distinguish data, model and JSON schema validation. Passing a schema does not compile DAX or M, parse TMDL in Desktop or validate visual rendering.

## Pending

- Power BI Desktop open, refresh, measure evaluation, visual rendering and save/reopen checks. Follow `powerbi/README.md`.

No SLA compliance, causal effects, financial benefits or City endorsement have been validated or claimed.

