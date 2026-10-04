"""Meaningful fixtures for exclusions, same-day events, censoring and percentiles."""
import sys,unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build import classify,percentile
class MetricsTests(unittest.TestCase):
    def row(self,status='Closed',requested='2026-01-01',closed='2026-01-03'):
        return classify(dict(status_description=status,requested_date=requested,closed_date=closed),date(2026,10,2))
    def test_same_day_is_zero(self):self.assertEqual(self.row(closed='2026-01-01')['closure_days'],0)
    def test_duplicates_are_not_closures(self):
        for status in ['Duplicate (Open)','Duplicate (Closed)']:
            r=self.row(status);self.assertEqual(r['duplicate'],1);self.assertEqual(r['is_open'],0);self.assertIsNone(r['closure_days'])
    def test_open_excluded_from_closure_distribution(self):
        r=self.row('Open',closed='');self.assertEqual(r['age_days'],274);self.assertIsNone(r['closure_days'])
    def test_open_with_date_flagged(self):self.assertEqual(self.row('Open')['open_with_closed'],1)
    def test_missing_closure(self):
        r=self.row(closed='');self.assertEqual(r['missing_closed'],1);self.assertIsNone(r['closure_days']);self.assertEqual(r['is_closed'],1)
    def test_invalid_closure(self):
        for v in ['2025-12-31','2026-10-03','bad-date']:
            r=self.row(closed=v);self.assertEqual(r['invalid_closed'],1);self.assertIsNone(r['closure_days'])
    def test_unknown_status_retained(self):self.assertEqual(self.row('Pending')['unknown_status'],1)
    def test_future_request_not_aged(self):self.assertIsNone(self.row('Open','2026-10-04','')['age_days'])
    def test_percentile_interpolation(self):self.assertEqual(percentile([0,0,2,8],.9),6.200000000000001)
    def test_empty_and_singleton(self):self.assertIsNone(percentile([],.5));self.assertEqual(percentile([4],.9),4)
if __name__=='__main__':unittest.main()
