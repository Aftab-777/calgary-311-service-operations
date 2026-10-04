/** Download a bounded public snapshot. Node 18+; no packages or credentials. */
import {mkdir, writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {createHash} from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const endpoint='https://data.calgary.ca/resource/iahh-g8bj.json';
const start=process.env.START_DATE || '2026-01-01';
const end=process.env.END_DATE || '2026-10-01';
const where=`requested_date >= '${start}T00:00:00' AND requested_date < '${end}T00:00:00'`;
const fields=['service_request_id','requested_date','updated_date','closed_date','status_description','source','service_name','agency_responsible','comm_code','comm_name'];
async function get(params){
  const url=new URL(endpoint); for(const [k,v] of Object.entries(params)) url.searchParams.set('$'+k,v);
  for(let n=0;n<4;n++){
    try {const r=await fetch(url,{signal:AbortSignal.timeout(120000)});if(!r.ok)throw new Error(`${r.status} ${await r.text()}`);return await r.json();}
    catch(e){if(n===3)throw e;await new Promise(r=>setTimeout(r,1000*2**n));}
  }
}
const before=await (await fetch('https://data.calgary.ca/api/views/iahh-g8bj.json')).json();
const count=Number((await get({select:'count(*)',where}))[0].count);
console.log(`Selected cohort ${start} to ${end} exclusive: ${count} rows`);
if(process.argv.includes('--profile')){
 console.log(JSON.stringify(await get({select:'status_description,count(*)',where,group:'status_description',order:'count(*) DESC'})));process.exit(0);
}
let rows=[];
for(let offset=0;offset<count;offset+=10000){const batch=await get({select:fields.join(','),where,order:'service_request_id',limit:10000,offset});rows.push(...batch);console.log(`Downloaded ${rows.length}/${count}`);}
const after=await (await fetch('https://data.calgary.ca/api/views/iahh-g8bj.json')).json();
if(before.rowsUpdatedAt!==after.rowsUpdatedAt)throw new Error('Source changed during pagination; rerun for a consistent snapshot.');
if(rows.length!==count || new Set(rows.map(r=>r.service_request_id)).size!==count)throw new Error('Row count or ID uniqueness failure.');
const quote=v=>'"'+String(v??'').replaceAll('"','""')+'"';
const csv=fields.join(',')+'\n'+rows.map(r=>fields.map(f=>quote(r[f])).join(',')).join('\n')+'\n';
await mkdir(path.join(root,'data'),{recursive:true});
await writeFile(path.join(root,'data','requests.csv'),csv);
const manifest={dataset:'City of Calgary 311 Service Requests',dataset_id:'iahh-g8bj',source_url:'https://data.calgary.ca/Services-and-Amenities/311-Service-Requests/iahh-g8bj',endpoint,filter:where,cohort_start:start,cohort_end_exclusive:end,retrieved_at_utc:new Date().toISOString(),source_updated_at_utc:new Date(after.rowsUpdatedAt*1000).toISOString(),row_count:count,columns:fields,sha256:createHash('sha256').update(csv).digest('hex'),licence_url:'https://data.calgary.ca/stories/s/u45n-7awa/',attribution:'Contains information licensed under the Open Government Licence – City of Calgary.',privacy:'Street addresses, coordinates, point geometry and personal details are not requested.'};
manifest.as_of_date=new Intl.DateTimeFormat('en-CA',{timeZone:'America/Edmonton',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(after.rowsUpdatedAt*1000));
await writeFile(path.join(root,'data','manifest.json'),JSON.stringify(manifest,null,2)+'\n');
await writeFile(path.join(root,'data','source_schema.json'),JSON.stringify(after.columns.filter(c=>fields.includes(c.fieldName)).map(c=>({field:c.fieldName,type:c.dataTypeName,description:c.description})),null,2)+'\n');
console.log('Snapshot saved. Run python scripts/build.py to rebuild derived outputs.');
