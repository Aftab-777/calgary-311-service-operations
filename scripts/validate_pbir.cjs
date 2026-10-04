const fs=require('fs'),path=require('path'),Ajv=require('ajv'),formats=require('ajv-formats');
const root=path.resolve(__dirname,'..');
const cache=new Map();async function load(url){if(cache.has(url))return cache.get(url);const r=await fetch(url,{signal:AbortSignal.timeout(30000)});if(!r.ok)throw Error(`${r.status} ${url}`);const obj=await r.json();cache.set(url,obj);return obj;}
const ajv=new Ajv({strict:false,allErrors:true,inlineRefs:false,loadSchema:load});formats(ajv);
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?walk(path.join(dir,e.name)):[path.join(dir,e.name)]);}
(async()=>{let checked=0;for(const f of walk(path.join(root,'powerbi/project'))){if(!/\.(json|pbip|pbir|pbism)$/.test(f))continue;const obj=JSON.parse(fs.readFileSync(f,'utf8'));if(!obj.$schema)continue;const schema=await load(obj.$schema);if(schema.$schema?.includes('draft-07')){delete schema.$schema;}const validator=await ajv.compileAsync(schema);if(!validator(obj))throw Error(f+'\n'+JSON.stringify(validator.errors));checked++;}const report={schema_files_checked:checked,official_schemas_loaded:cache.size,result:'passed',native_runtime:'Not executed; schema validation does not compile DAX, M, TMDL or render visuals.'};fs.writeFileSync(path.join(root,'analysis/pbir_validation.json'),JSON.stringify(report,null,2)+'\n');console.log(report);})().catch(e=>{console.error(e);process.exitCode=1;});



