"""Verify embedded snapshot bytes and dimension relationships without Desktop."""
import base64,csv,json,re,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
tables=ROOT/'powerbi/project/Operations.SemanticModel/definition/tables'
checked=[]
for path in sorted(tables.glob('*.tmdl')):
    match=re.search(r'Packed = Text.Combine\(\{(.*?)\}\)',path.read_text(encoding='utf-8'))
    assert match,path
    encoded=''.join(re.findall(r'"([A-Za-z0-9+/=]+)"',match[1]))
    decoded=zlib.decompress(base64.b64decode(encoded),-15)
    assert decoded==(ROOT/'data/model'/f'{path.stem}.csv').read_bytes(),path
    checked.append(path.stem)
assert len(checked)==6
def rows(table):
    with (ROOT/'data/model'/f'{table}.csv').open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))
fact=rows('FactRequests')
for dim,key,fact_key in [('DimService','service_key','service_key'),('DimChannel','channel_key','channel_key'),('DimCommunity','community_key','community_key'),('DimDate','date','requested_date')]:
    data=rows(dim);keys={r[key] for r in data}
    assert len(keys)==len(data),(dim,'duplicate key')
    assert all(r[fact_key] in keys for r in fact),(dim,'orphan fact')
report={'embedded_tables':checked,'embedded_csv_byte_equality':'passed','unique_dimension_keys':'passed','referential_integrity':'passed','native_M_DAX_TMDL_execution':'not tested'}
(ROOT/'analysis/model_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
