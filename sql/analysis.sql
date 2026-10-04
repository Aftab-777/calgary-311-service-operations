-- Explicit duplicate statuses are excluded from operational metrics.
-- Counts describe the selected submission cohort at extraction time.
-- QUERY: summary
SELECT COUNT(*) AS total, SUM(duplicate) AS duplicates, SUM(1-duplicate) AS operational,
 SUM(is_open) AS open,SUM(is_closed) AS closed,COUNT(closure_days) AS closure_valid,
 SUM(CASE WHEN age_days >= 30 THEN 1 ELSE 0 END) AS open_30_plus FROM FactRequests;
-- QUERY: monthly
SELECT d.month,COUNT(*) AS requests,SUM(f.is_open) AS open_at_snapshot,SUM(f.is_closed) AS closed_at_snapshot,
 LAG(COUNT(*)) OVER (ORDER BY d.month) AS previous_month_requests
FROM FactRequests f JOIN DimDate d ON d.date=f.requested_date
WHERE f.duplicate=0 GROUP BY d.month ORDER BY d.month;
-- QUERY: services
SELECT s.service_name,s.agency,COUNT(*) AS requests,SUM(f.is_open) AS open_at_snapshot,
 COUNT(f.closure_days) AS closure_sample,ROUND(AVG(f.closure_days),2) AS mean_closure_days,
 SUM(CASE WHEN f.age_days >= 30 THEN 1 ELSE 0 END) AS open_30_plus
FROM FactRequests f JOIN DimService s ON s.service_key=f.service_key
WHERE f.duplicate=0 GROUP BY s.service_key ORDER BY requests DESC,s.service_name;
-- QUERY: channels
SELECT c.channel,COUNT(*) AS requests FROM FactRequests f JOIN DimChannel c ON c.channel_key=f.channel_key
WHERE f.duplicate=0 GROUP BY c.channel ORDER BY requests DESC;
-- QUERY: weekdays
SELECT d.weekday,d.weekday_order,COUNT(*) AS requests FROM FactRequests f JOIN DimDate d ON d.date=f.requested_date
WHERE f.duplicate=0 GROUP BY d.weekday_order ORDER BY d.weekday_order;
-- QUERY: closure_percentiles
WITH ranked AS (SELECT closure_days,ROW_NUMBER() OVER (ORDER BY closure_days) AS rn,
 COUNT(*) OVER () AS n FROM FactRequests WHERE closure_days IS NOT NULL),
 target AS (SELECT MAX(n) AS n FROM ranked),
 positions AS (SELECT 1+(n-1)*0.5 AS p50,1+(n-1)*0.9 AS p90 FROM target)
SELECT
 (SELECT closure_days FROM ranked WHERE rn=CAST(p50 AS INTEGER))+
 (p50-CAST(p50 AS INTEGER))*((SELECT closure_days FROM ranked WHERE rn=MIN(CAST(p50 AS INTEGER)+1,(SELECT n FROM target)))-(SELECT closure_days FROM ranked WHERE rn=CAST(p50 AS INTEGER))) AS median_closure,
 (SELECT closure_days FROM ranked WHERE rn=CAST(p90 AS INTEGER))+
 (p90-CAST(p90 AS INTEGER))*((SELECT closure_days FROM ranked WHERE rn=MIN(CAST(p90 AS INTEGER)+1,(SELECT n FROM target)))-(SELECT closure_days FROM ranked WHERE rn=CAST(p90 AS INTEGER))) AS p90_closure
FROM positions;
