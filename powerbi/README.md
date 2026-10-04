# Power BI project source

Open `project/Calgary-311-Service-Operations.pbip` in a current Power BI Desktop version that supports Power BI projects and PBIR. If your version exposes Power BI Project save support as a preview feature, enable it and restart Desktop. Keep the Report and SemanticModel folders alongside the PBIP file.

The project has three pages: Service overview, Open workload and Data quality. It includes six tables, four one-direction relationships and 14 explicit measures. CSV snapshots are compressed and embedded in M expressions, so no machine-specific input paths or API credentials are required.

**Native validation remains pending.** The project has not been opened, compiled, refreshed or visually inspected in Power BI Desktop. JSON schemas and compressed data round trips have been validated separately. The browser dashboard screenshots do not demonstrate native report rendering.

## Desktop acceptance checks

1. Open the PBIP and confirm that no model or visual errors appear.
2. Refresh. Confirm all six tables load and the fact contains 385,723 rows.
3. Compare unfiltered cards with 381,923 Requests, 25,636 Open Requests, 356,287 Valid Closure Sample, median 2 and P90 21.
4. Select September. Expect 40,697 Requests, 8,526 Open Requests, 32,171 valid closures, median 1 and P90 9.
5. On each page, inspect chart labels, cards, table scrolling and slicer behavior. Slicers are independent between pages.
6. Save, close and reopen the project. Record the Desktop version and results in `docs/VALIDATION.md` before describing it as Desktop-tested.

`MEASURES.dax` contains readable measure definitions. `scripts/build_powerbi.py` is the source generator; editing generated report files and running the generator will overwrite those edits.

## Cost and sharing

Power BI Desktop is a free download for Windows. A paid Power BI service licence is not required for this local project or its HTML demonstration. Publishing and sharing through the Power BI service can have separate licence requirements. No paid cloud services, service workspace or Publish to web link have been configured.

The snapshot is static. Refreshing the model rereads embedded data rather than downloading new City records. To update the snapshot, run the extraction and both build scripts, update narrative evidence and repeat native acceptance checks.
