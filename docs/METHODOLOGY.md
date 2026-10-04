# Methodology

## Scope and source

The unit of analysis is one service request ID. The selected cohort contains requests submitted on or after January 1, 2026 and before October 1, 2026. The dataset is [Calgary 311 Service Requests](https://data.calgary.ca/Services-and-Amenities/311-Service-Requests/iahh-g8bj), ID `iahh-g8bj`.

The source's update timestamp is October 3, 2026 at 17:01:14 UTC. The calendar date in Calgary, October 3, is the age anchor. Download completion was October 4 at 04:29:29 UTC. The manifest preserves both timestamps and the exact query. Dataset-level update time does not mean every individual request was updated at that instant.

The downloader selects ten fields, sorts by request ID and pages in blocks of 10,000. It checks that the source update timestamp remained unchanged during extraction, all request IDs are unique and the downloaded row count matches the API count. These checks reduce pagination inconsistency; the API is not a transactional historical snapshot service.

## Status and exclusions

Explicit `Duplicate (Open)` and `Duplicate (Closed)` statuses are retained for auditing but excluded from operational counts, open workload and closure durations. No additional fuzzy deduplication is attempted. Records are not assumed to represent unique residents, incidents or completed repairs.

`Open` status controls the open flag, even when a closure date is also present. There are 1,621 such records; they remain open and are excluded from closure-duration measures. `Closed` status controls the closed count. Unknown statuses would remain in nonduplicate volume and receive a quality flag. No unknown statuses occur in this snapshot.

## Dates and durations

Dates use the calendar-date part of the source timestamp. A closure on the submission date is zero days. The project measures neither elapsed hours nor working days and does not infer hours from timezone-free timestamps.

Valid closure duration requires a nonduplicate Closed record, a valid submission date and a closure date on or after submission and on or before the snapshot date. Missing, malformed, negative and future closure durations are excluded from duration statistics. Closed records with invalid dates still count as closed when their submission date is valid.

Open age equals snapshot date minus submission date for records currently Open. The 30-day threshold is descriptive, not an official service target. Open records are not assigned a closure duration of zero.

## Percentiles and filters

Median and P90 use linear interpolation with zero-based position `(n - 1) × p`, equivalent to inclusive percentiles. The browser stores counts by integer duration for every month/service combination. It merges those histograms and recomputes percentiles for the active selection. It never averages service-level medians or percentiles. Empty duration samples display a dash.

SQL independently ranks valid closed durations with `ROW_NUMBER` and calculates interpolated positions. Python calculates the same statistics from sorted durations. DAX uses `MEDIAN` and `PERCENTILEX.INC` with blank durations excluded. DAX execution is still unverified in Desktop.

Browser filters select submission month and service plus agency. Native report source also includes channel slicers; page slicers are not synchronized. A September filter means requests submitted in September with status observed at the October snapshot. It does not reconstruct September month-end backlog.

## Model

`FactRequests` has one row per request. `DimService`, `DimChannel`, `DimCommunity` and `DimDate` relate one-to-many to the fact and filter in one direction. `Snapshot` has one disconnected metadata row. Keys are deterministic for this snapshot, not permanent identifiers across future refreshes. Service labels and agencies remain as supplied; historical and NEW labels are not merged without a validated mapping.

Missing community codes, found on 24,237 records, remain represented by an Unknown code. Missing names are likewise retained as Unknown. The channel `Other` is not relabelled as phone: it contains 310,692 nonduplicate requests, alongside 71,228 App and 3 Web requests. The data does not explain the coding imbalance.

## Interpretation limits

Calgary's [311 FAQs](https://www.calgary.ca/311/faqs.html) explain that closure can follow investigation or identification of required work; work can remain scheduled for the future. Administrative closure is not proof that an issue was repaired.

Closed-only durations omit requests that are still open, which is right censoring. Open-age distribution is shown separately; this is not survival analysis. Newer cohorts have less follow-up time. Different services vary in complexity, so combined figures do not establish comparative service performance. June being the highest month in this sample is not evidence of a recurring seasonal effect.

The cohort excludes requests submitted before 2026 and after September. It cannot quantify all outstanding City requests. No SLA targets, staffing, costs, priority, repeat-contact history, satisfaction or verified repair dates are modelled. The project is an independent descriptive study.

## Reproducibility and refresh

Rebuild from the preserved CSV and manifest. The manifest SHA-256 is checked before transformation. A live redownload replaces the snapshot and may change old records. After refreshing, rebuild both dashboard and Power BI, run all checks, review findings and replace dated screenshots. The embedded Power BI tables do not call the live API when refreshed.
