# Validation status

## Completed locally

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

The evidence files under `analysis/` distinguish data, model and JSON schema validation. Passing a schema does not compile DAX or M, parse TMDL in Desktop or validate visual rendering.

## Pending

- Power BI Desktop open, refresh, measure evaluation, visual rendering and save/reopen checks. Follow `powerbi/README.md`.
- Remote GitHub Actions execution and hosted-page verification after publication. The workflow is prepared but has not run remotely.

No SLA compliance, causal effects, financial benefits or City endorsement have been validated or claimed.
