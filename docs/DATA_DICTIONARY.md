# Data dictionary

## Selected source columns

| Field | Meaning and treatment |
|---|---|
| `service_request_id` | Source request identifier; asserted unique in this cohort; retained as text |
| `requested_date` | Submission timestamp; calendar date drives cohort, date dimension and duration start |
| `updated_date` | Source record update timestamp; preserved in raw input, not used as a closure proxy |
| `closed_date` | Administrative closure timestamp; may be blank or contradict Open status |
| `status_description` | Open, Closed or explicit duplicate status; determines flags |
| `source` | Submission channel as supplied; Other is not interpreted as phone |
| `service_name` | Source category label; preserved without speculative consolidation |
| `agency_responsible` | Source agency; paired with service label to define service dimension grain |
| `comm_code` | Community code; missing values become Unknown in model |
| `comm_name` | Community name; paired with code; missing values become Unknown |

The selected official metadata is saved in `data/source_schema.json`. Additional source fields, including addresses and exact coordinates, are not downloaded.

## Fact table columns

| Column | Type | Definition |
|---|---|---|
| `request_id` | Text | Source request ID |
| `requested_date`, `closed_date` | Date | Parsed calendar dates; closure can be blank |
| `service_key`, `channel_key`, `community_key` | Integer | Keys to related dimensions |
| `status` | Text | Source status |
| `duplicate` | 0 or 1 | Explicit duplicate status |
| `is_open`, `is_closed` | 0 or 1 | Respective nonduplicate status with valid submission date |
| `closure_days` | Nullable integer | Valid closed duration; null for Open and duplicate records |
| `age_days` | Nullable integer | Snapshot age for Open records only |
| `invalid_closed` | 0 or 1 | Closure before submission, after snapshot or unreadable |
| `missing_closed` | 0 or 1 | Closed status without closure date |
| `invalid_requested` | 0 or 1 | Submission unreadable or after snapshot |
| `unknown_status` | 0 or 1 | Status outside four expected values |
| `open_with_closed` | 0 or 1 | Open record also contains a closure-date field |

Blank CSV values are converted to null before native model type conversion. Counts and flags have no implicit summarization in model metadata; explicit measures control aggregation.

## Dimensions and metadata

| Table | Grain | Join |
|---|---|---|
| `DimService` | Service label and agency | service_key |
| `DimChannel` | Source channel label | channel_key |
| `DimCommunity` | Community code and name | community_key |
| `DimDate` | Every calendar day in submission cohort | date to requested_date |
| `Snapshot` | One snapshot metadata row | Disconnected |

`DimDate` also contains year-month text, weekday name and Monday-based weekday order. `Snapshot` records as-of date, cohort start and exclusive end. `data/manifest.json` contains provenance, exact query, selected columns, timestamps, checksum and licence.
