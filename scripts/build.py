"""Rebuild SQL results, dashboard data and Power BI inputs. Python 3.10+, stdlib."""
from __future__ import annotations
import csv, hashlib, json, sqlite3
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def parse_date(value):
    try: return date.fromisoformat(value[:10]) if value else None
    except (ValueError,TypeError): return None

def classify(row,as_of):
    requested,closed=parse_date(row.get('requested_date')),parse_date(row.get('closed_date'))
    status=row.get('status_description','').strip()
    duplicate=status in ('Duplicate (Closed)','Duplicate (Open)')
    valid_requested=requested is not None and requested<=as_of
    invalid_closed=bool(row.get('closed_date')) and (closed is None or not valid_requested or closed<requested or closed>as_of)
    closure_days=(closed-requested).days if status=='Closed' and closed and valid_requested and not invalid_closed else None
    age_days=(as_of-requested).days if status=='Open' and valid_requested else None
    return dict(duplicate=int(duplicate),is_open=int(status=='Open' and valid_requested),is_closed=int(status=='Closed' and valid_requested),closure_days=closure_days,age_days=age_days,invalid_closed=int(invalid_closed),missing_closed=int(status=='Closed' and not row.get('closed_date')),invalid_requested=int(not valid_requested),unknown_status=int(status not in ('Open','Closed','Duplicate (Open)','Duplicate (Closed)')),open_with_closed=int(status=='Open' and bool(row.get('closed_date'))))

def percentile(values,fraction):
    if not values:return None
    ordered=sorted(values);pos=(len(ordered)-1)*fraction;lo=int(pos);hi=min(lo+1,len(ordered)-1)
    return ordered[lo]+(ordered[hi]-ordered[lo])*(pos-lo)

def csv_write(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    source=ROOT/'data/requests.csv';manifest=json.loads((ROOT/'data/manifest.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['sha256'],'Source checksum mismatch'
    as_of=date.fromisoformat(manifest['as_of_date'])
    with source.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    assert len(rows)==manifest['row_count'] and len({r['service_request_id'] for r in rows})==len(rows)
    start=date.fromisoformat(manifest['cohort_start']);end=date.fromisoformat(manifest['cohort_end_exclusive'])
    assert all(start<=parse_date(r['requested_date'])<end for r in rows)
    services=sorted({(r['service_name'] or 'Unknown',r['agency_responsible'] or 'Unknown') for r in rows})
    channels=sorted({r['source'] or 'Unknown' for r in rows})
    communities=sorted({(r['comm_code'] or 'Unknown',r['comm_name'] or 'Unknown') for r in rows})
    service_keys={v:i+1 for i,v in enumerate(services)};channel_keys={v:i+1 for i,v in enumerate(channels)};community_keys={v:i+1 for i,v in enumerate(communities)}
    facts=[];cells={};quality=Counter();statuses=Counter();closed_values=[];open_values=[]
    for r in rows:
        c=classify(r,as_of);d=parse_date(r['requested_date']);month=d.strftime('%Y-%m')
        sk=service_keys[(r['service_name'] or 'Unknown',r['agency_responsible'] or 'Unknown')]
        status=r['status_description'];statuses[status]+=1
        facts.append(dict(request_id=r['service_request_id'],requested_date=d.isoformat(),closed_date=(parse_date(r['closed_date']).isoformat() if parse_date(r['closed_date']) else ''),service_key=sk,channel_key=channel_keys[r['source'] or 'Unknown'],community_key=community_keys[(r['comm_code'] or 'Unknown',r['comm_name'] or 'Unknown')],status=status,**c))
        for name in ('invalid_closed','missing_closed','invalid_requested','unknown_status','open_with_closed'):quality[name]+=c[name]
        for name in ('service_name','source','comm_code','agency_responsible'):quality['missing_'+name]+=int(not r[name])
        key=(month,sk)
        if key not in cells:cells[key]=dict(month=month,service=sk,total=0,duplicates=0,open=0,closed=0,other=0,closure=Counter(),ages=Counter(),weekdays=[0]*7,channels=Counter(),quality=Counter())
        cell=cells[key];cell['total']+=1;cell['duplicates']+=c['duplicate'];cell['open']+=c['is_open'];cell['closed']+=c['is_closed'];cell['other']+=c['unknown_status']
        for name in ('invalid_closed','missing_closed','invalid_requested','unknown_status','open_with_closed'):cell['quality'][name]+=c[name]
        cell['quality']['missing_comm_code']+=int(not r['comm_code'])
        if not c['duplicate']:cell['weekdays'][d.weekday()]+=1;cell['channels'][r['source'] or 'Unknown']+=1
        if c['closure_days'] is not None:cell['closure'][c['closure_days']]+=1;closed_values.append(c['closure_days'])
        if c['age_days'] is not None:cell['ages'][c['age_days']]+=1;open_values.append(c['age_days'])
    derived=ROOT/'data/model';csv_write(derived/'FactRequests.csv',facts,list(facts[0]))
    csv_write(derived/'DimService.csv',[dict(service_key=i+1,service_name=v[0],agency=v[1]) for i,v in enumerate(services)],['service_key','service_name','agency'])
    csv_write(derived/'DimChannel.csv',[dict(channel_key=i+1,channel=v) for i,v in enumerate(channels)],['channel_key','channel'])
    csv_write(derived/'DimCommunity.csv',[dict(community_key=i+1,community_code=v[0],community=v[1]) for i,v in enumerate(communities)],['community_key','community_code','community'])
    dates=[];d=start
    while d<=as_of:dates.append(dict(date=d.isoformat(),month=d.strftime('%Y-%m'),weekday=d.strftime('%A'),weekday_order=d.weekday()+1));d+=timedelta(days=1)
    csv_write(derived/'DimDate.csv',dates,['date','month','weekday','weekday_order'])
    csv_write(derived/'Snapshot.csv',[dict(as_of_date=as_of.isoformat(),cohort_start=start.isoformat(),cohort_end_exclusive=end.isoformat())],['as_of_date','cohort_start','cohort_end_exclusive'])
    db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row
    fields=list(facts[0]);num=set(fields)-{'request_id','requested_date','closed_date','status'}
    db.execute('CREATE TABLE FactRequests ('+','.join(f'"{k}" '+('INTEGER' if k in num else 'TEXT') for k in fields)+')')
    db.executemany('INSERT INTO FactRequests VALUES ('+','.join('?' for _ in fields)+')',[[r[k] for k in fields] for r in facts])
    for table in ('DimService','DimChannel','DimCommunity','DimDate'):
        with (derived/(table+'.csv')).open(encoding='utf-8') as f:
            dim=list(csv.DictReader(f));keys=list(dim[0]);db.execute('CREATE TABLE '+table+' ('+','.join('"'+k+'" '+('INTEGER' if k.endswith('_key') or k=='weekday_order' else 'TEXT') for k in keys)+')');db.executemany('INSERT INTO '+table+' VALUES ('+','.join('?' for _ in keys)+')',[list(r.values()) for r in dim])
    sql=(ROOT/'sql/analysis.sql').read_text(encoding='utf-8');results={}
    for part in sql.split('-- QUERY: ')[1:]:
        name,query=part.split('\n',1);results[name.strip()]=[dict(r) for r in db.execute(query)]
    metrics=dict(total=len(rows),duplicates=sum(r['duplicate'] for r in facts),operational=sum(1-r['duplicate'] for r in facts),open=len(open_values),closed=sum(r['is_closed'] for r in facts),closure_valid=len(closed_values),median_closure=percentile(closed_values,.5),p90_closure=percentile(closed_values,.9),median_open_age=percentile(open_values,.5),open_30_plus=sum(v>=30 for v in open_values))
    for k in ('total','duplicates','operational','open','closed','closure_valid','open_30_plus'):assert results['summary'][0][k]==metrics[k],k
    for k in ('median_closure','p90_closure'):assert abs(results['closure_percentiles'][0][k]-metrics[k])<1e-8,k
    for k in ('monthly','services','channels'):assert sum(r['requests'] for r in results[k])==metrics['operational']
    write_json(ROOT/'analysis/summary.json',dict(manifest=manifest,metrics=metrics,status_counts=statuses,quality=quality,sql_results=results))
    for name,result in results.items():
        if result:csv_write(ROOT/'analysis'/(name+'.csv'),result,list(result[0]))
    packed=[]
    for cell in cells.values():
        for name in ('closure','ages'):cell[name]=sorted(cell[name].items())
        cell['channels']=dict(cell['channels']);cell['quality']=dict(cell['quality']);packed.append(cell)
    dashboard=dict(manifest=manifest,metrics=metrics,quality=quality,statuses=statuses,services=[dict(id=i+1,name=v[0],agency=v[1]) for i,v in enumerate(services)],cells=packed)
    (ROOT/'dashboard').mkdir(exist_ok=True)
    (ROOT/'dashboard/data.js').write_text('window.PROJECT_DATA='+json.dumps(dashboard,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')+';\n',encoding='utf-8')
    write_json(ROOT/'analysis/validation.json',{'source_checksum':'passed','source_row_count':'passed','unique_request_ids':'passed','cohort_dates':'passed','sql_python_counts':'passed','sql_python_percentiles':'passed','sql_dimension_reconciliation':'passed','fact_rows':len(facts),'model_tables':6,'as_of_date':as_of.isoformat(),'native_power_bi_runtime':'not executed in Power BI Desktop'})
    print(json.dumps(dict(metrics=metrics,quality=quality,statuses=statuses,services=len(services),dashboard_cells=len(packed)),indent=2))
if __name__=='__main__':main()
