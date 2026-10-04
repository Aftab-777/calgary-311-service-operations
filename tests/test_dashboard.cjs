const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'..'),M=require('../dashboard/metrics.js');
const sandbox={window:{}};vm.runInNewContext(fs.readFileSync(path.join(root,'dashboard/data.js'),'utf8'),sandbox);
const D=sandbox.window.PROJECT_DATA,expected=JSON.parse(fs.readFileSync(path.join(root,'analysis/summary.json'),'utf8')).metrics,a=M.aggregate(D.cells);
for(const k of ['total','duplicates','operational','open','closed'])assert.equal(a[k],expected[k],k);
assert.equal(a.closureSample,expected.closure_valid);assert.equal(a.median,expected.median_closure);assert.equal(a.p90,expected.p90_closure);assert.equal(a.open30,expected.open_30_plus);
assert.equal(M.percentile(new Map([[0,2],[2,1],[8,1]]),.9),6.200000000000001);
assert.equal(M.aggregate([]).median,null);assert.equal(M.aggregate([]).open,0);
// Filtering must reconcile to the unfiltered population without averaging medians.
for(const grouping of ['month','service']){let sum=0;for(const key of new Set(D.cells.map(c=>c[grouping])))sum+=M.aggregate(D.cells.filter(c=>c[grouping]===key)).operational;assert.equal(sum,a.operational);}
console.log('Dashboard histogram percentiles, exclusion rules, empty states and filter reconciliation passed.');
