"""Build portable PBIP/PBIR and TMDL with compressed embedded snapshot tables."""
import base64,csv,json,zlib
from pathlib import Path
from pbir_helpers import *

MEASURES={
 'Source Records':('COUNTROWS ( FactRequests )','#,0'),
 'Duplicate Records':('CALCULATE ( COUNTROWS ( FactRequests ), FactRequests[duplicate] = 1 )','#,0'),
 'Requests':('CALCULATE ( COUNTROWS ( FactRequests ), FactRequests[duplicate] = 0 )','#,0'),
 'Open Requests':('COALESCE ( CALCULATE ( COUNTROWS ( FactRequests ), FactRequests[is_open] = 1 ), 0 )','#,0'),
 'Closed Requests':('COALESCE ( CALCULATE ( COUNTROWS ( FactRequests ), FactRequests[is_closed] = 1 ), 0 )','#,0'),
 'Valid Closure Sample':('COUNT ( FactRequests[closure_days] )','#,0'),
 'Median Closure Days':('MEDIAN ( FactRequests[closure_days] )','0.0'),
 'P90 Closure Days':('PERCENTILEX.INC ( FILTER ( FactRequests, NOT ISBLANK ( FactRequests[closure_days] ) ), FactRequests[closure_days], 0.9 )','0.0'),
 'Median Open Age Days':('MEDIAN ( FactRequests[age_days] )','0.0'),
 'Open 30 Plus Days':('COALESCE ( CALCULATE ( COUNTROWS ( FactRequests ), FactRequests[is_open] = 1, FactRequests[age_days] >= 30 ), 0 )','#,0'),
 'Missing Closure Dates':('SUM ( FactRequests[missing_closed] )','#,0'),
 'Invalid Closure Dates':('SUM ( FactRequests[invalid_closed] )','#,0'),
 'Open With Closure Date':('SUM ( FactRequests[open_with_closed] )','#,0'),
 'Unknown Status Records':('SUM ( FactRequests[unknown_status] )','#,0'),
}

def build_model():
    tables=['FactRequests','DimService','DimChannel','DimCommunity','DimDate','Snapshot']
    write(MODEL/'definition.pbism',{'$schema':SCHEMA+'item/semanticModel/definitionProperties/1.0.0/schema.json','version':'4.0','settings':{'qnaEnabled':False}})
    write(MODEL/'definition/database.tmdl','database Calgary311Operations\n\tcompatibilityLevel: 1601\n\tcompatibilityMode: powerBI\n')
    write(MODEL/'definition/model.tmdl','model Model\n\tculture: en-CA\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-CA\n\tdiscourageImplicitMeasures\n\nannotation __PBI_TimeIntelligenceEnabled = 0\nannotation PBI_QueryOrder = '+json.dumps(tables)+'\n\n'+'\n'.join('ref table '+t for t in tables)+'\n')
    date_columns={'requested_date','closed_date','date','as_of_date','cohort_start','cohort_end_exclusive'}
    numeric={'duplicate','is_open','is_closed','closure_days','age_days','invalid_closed','missing_closed','invalid_requested','unknown_status','open_with_closed','weekday_order'}
    for table in tables:
        csv_bytes=(ROOT/'data/model'/f'{table}.csv').read_bytes()
        columns=next(csv.reader(csv_bytes.decode('utf-8').splitlines()))
        lines=['table '+table]
        if table=='Snapshot':lines.append('\tisHidden')
        if table=='FactRequests':
            for name,(expression,fmt) in MEASURES.items():lines.extend([f"\tmeasure '{name}' = {expression}",f'\t\tformatString: "{fmt}"',''])
        conversions=[]
        for col in columns:
            is_number=col in numeric or col.endswith('_key');is_date=col in date_columns
            data_type='dateTime' if is_date else 'int64' if is_number else 'string'
            m_type='type date' if is_date else 'Int64.Type' if is_number else 'type text'
            lines.extend([f'\tcolumn {col}',f'\t\tdataType: {data_type}','\t\tsummarizeBy: none',f'\t\tsourceColumn: {col}'])
            if is_date:lines.extend(['\t\tformatString: "yyyy-MM-dd"','\t\tannotation UnderlyingDateTimeDataType = Date'])
            if col.endswith('_key') or (table=='FactRequests' and col in numeric):lines.append('\t\tisHidden')
            if table=='DimDate' and col=='weekday':lines.append('\t\tsortByColumn: weekday_order')
            lines.append('');conversions.append('{"'+col+'", '+m_type+'}')
        compressed=base64.b64encode(zlib.compress(csv_bytes)[2:-4]).decode('ascii')
        # Multiple literals avoid overly long text tokens. Combines to one compressed CSV.
        chunks=[compressed[i:i+30000] for i in range(0,len(compressed),30000)]
        blob='{'+','.join('"'+c+'"' for c in chunks)+'}'
        lines.extend([f'\tpartition {table} = m','\t\tmode: import','\t\tsource =','\t\t\tlet',f'\t\t\t    Packed = Text.Combine({blob}),',f'\t\t\t    Source = Csv.Document(Binary.Decompress(Binary.FromText(Packed, BinaryEncoding.Base64), Compression.Deflate), [Delimiter=",", Columns={len(columns)}, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),','\t\t\t    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),','\t\t\t    Blanks = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),','\t\t\t    Typed = Table.TransformColumnTypes(Blanks, {'+', '.join(conversions)+'}, "en-CA")','\t\t\tin','\t\t\t    Typed'])
        write(MODEL/'definition/tables'/f'{table}.tmdl','\n'.join(lines)+'\n')
    rels=[]
    for dim,fact_col,dim_col in [('DimService','service_key','service_key'),('DimChannel','channel_key','channel_key'),('DimCommunity','community_key','community_key'),('DimDate','requested_date','date')]:
        rels.extend([f'relationship {identifier(dim)}',f'\tfromColumn: FactRequests.{fact_col}',f'\ttoColumn: {dim}.{dim_col}','\tcrossFilteringBehavior: oneDirection',''])
    write(MODEL/'definition/relationships.tmdl','\n'.join(rels))
    write(ROOT/'powerbi/MEASURES.dax','\n\n'.join(f'{name} =\n{expr}' for name,(expr,fmt) in MEASURES.items())+'\n')

def card(page,name,label,x,y,order,shade=BLUE):
    add_visual(page,name,'cardVisual',x,y,236,118,order,query(Data=[projection('Measure',FACT,name,label)]),{
      'value':object_properties({'fontSize':literal(27),'fontColor':color(shade),'bold':literal(True),'labelDisplayUnits':literal(1),'labelPrecision':literal(1 if 'Days' in name else 0)},{'id':'default'}),
      'label':object_properties({'show':literal(False)},{'id':'default'})},container(label,label+' for selected submission period and service.'))

def slicer(page,table,col,label,x,y,w,order):
    q=query(Values=[projection('Column',table,col,label)]);sort_by(q,field('Column',table,col))
    add_visual(page,label,'slicer',x,y,w,77,order,q,{'data':object_properties({'mode':literal('Dropdown')}),'selection':object_properties({'singleSelect':literal(False),'selectAllCheckboxEnabled':literal(True)}),'header':object_properties({'show':literal(False)})},container(label))

def bar_chart(page,label,table,col,measure,x,y,w,h,order):
    q=query(Category=[projection('Column',table,col)],Y=[projection('Measure',FACT,measure)])
    sort_by(q,field('Measure',FACT,measure),'Descending')
    add_visual(page,label,'clusteredBarChart',x,y,w,h,order,q,{
      'categoryAxis':object_properties({'showAxisTitle':literal(False),'fontSize':literal(10)}),
      'valueAxis':object_properties({'showAxisTitle':literal(False),'fontSize':literal(10),'start':literal(0)}),
      'dataPoint':object_properties({'defaultColor':color(BLUE)}),
      'labels':object_properties({'show':literal(True),'fontSize':literal(10)})},container(label))

def build_report():
    manifest=json.loads((ROOT/'data/manifest.json').read_text(encoding='utf-8'));as_of=manifest['as_of_date']
    pages=[(identifier('overview'),'Service overview'),(identifier('workload'),'Open workload'),(identifier('quality'),'Data quality')]
    write(PROJECT/'Calgary-311-Service-Operations.pbip',{'$schema':SCHEMA+'pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':'Operations.Report'}}],'settings':{'enableAutoRecovery':True}})
    write(REPORT/'definition.pbir',{'$schema':SCHEMA+'item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../Operations.SemanticModel'}}})
    write(REPORT/'definition/version.json',{'$schema':SCHEMA+'item/report/definition/versionMetadata/1.0.0/schema.json','version':'2.0.0'})
    version={'visual':'2.4.0','page':'2.0.0','report':'3.0.0'}
    write(REPORT/'definition/report.json',{'$schema':SCHEMA+'item/report/definition/report/3.0.0/schema.json','themeCollection':{'baseTheme':{'name':'CY24SU02','reportVersionAtImport':version,'type':'SharedResources'},'customTheme':{'name':'operations-theme.json','reportVersionAtImport':version,'type':'RegisteredResources'}},'resourcePackages':[{'name':'SharedResources','type':'SharedResources','items':[{'name':'CY24SU02','path':'BaseThemes/CY24SU02.json','type':'BaseTheme'}]},{'name':'RegisteredResources','type':'RegisteredResources','items':[{'name':'operations-theme.json','path':'operations-theme.json','type':'CustomTheme'}]}],'settings':{'useStylableVisualContainerHeader':True,'defaultFilterActionIsDataFilter':True,'allowChangeFilterTypes':True,'useEnhancedTooltips':True}})
    write(REPORT/'StaticResources/RegisteredResources/operations-theme.json',{'name':'Calgary Service Operations','dataColors':[BLUE,'#B66A22','#8BAB79','#526D89','#A18DB0'],'background':'#FFFFFF','foreground':INK,'tableAccent':BLUE})
    write(REPORT/'definition/pages/pages.json',{'$schema':SCHEMA+'item/report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':[p for p,t in pages],'activePageName':pages[0][0]})
    for p,title in pages:
        write(REPORT/'definition/pages'/p/'page.json',{'$schema':SCHEMA+'item/report/definition/page/2.0.0/schema.json','name':p,'displayName':title,'displayOption':'FitToPage','height':900,'width':1280,'objects':{'background':object_properties({'color':color('#F5F6F2'),'transparency':literal(0)})}})
        text(p,'title','Calgary 311 | '+title,24,18,1232,50,1000,25,INK)
        text(p,'scope',f'Jan–Sep 2026 submissions | Source snapshot {as_of} | Independent public-data study',24,73,1232,32,2000,12)
        slicer(p,'DimDate','month','Submission month',24,117,285,3000);slicer(p,'DimService','service_name','Service category',325,117,570,4000);slicer(p,'DimChannel','channel','Submission channel',911,117,345,5000)
        text(p,'note','Filters select the submission cohort. Status and age are measured at snapshot, not at the selected month end. Closed does not mean repaired.',24,203,1232,46,6000,11)
        text(p,'footer','Source: City of Calgary 311 open data | Explicit duplicates excluded from operational measures | Static embedded snapshot; no live refresh',24,850,1232,32,30000,10)
    p=pages[0][0]
    for i,(name,label) in enumerate([('Requests','Nonduplicate requests'),('Open Requests','Open at snapshot'),('Median Closure Days','Median closure · days'),('P90 Closure Days','90th percentile · days'),('Valid Closure Sample','Valid closure sample')]):card(p,name,label,24+i*248,260,7000+i*1000)
    q=query(Category=[projection('Column','DimDate','month')],Y=[projection('Measure',FACT,'Requests')]);sort_by(q,field('Column','DimDate','month'))
    add_visual(p,'monthly','clusteredColumnChart',24,402,738,410,13000,q,{'dataPoint':object_properties({'defaultColor':color(BLUE)}),'categoryAxis':object_properties({'showAxisTitle':literal(False)}),'valueAxis':object_properties({'showAxisTitle':literal(False),'start':literal(0)})},container('Requests by submission month'))
    bar_chart(p,'Submission channels','DimChannel','channel','Requests',782,402,474,410,14000)
    p=pages[1][0]
    for i,(name,label) in enumerate([('Open Requests','Open at snapshot'),('Open 30 Plus Days','Open 30+ days'),('Median Open Age Days','Median open age · days'),('Median Closure Days','Median closure · days'),('Valid Closure Sample','Closed sample size')]):card(p,name,label,24+i*248,260,7000+i*1000)
    q=query(Values=[projection('Column','DimService','service_name','Service'),projection('Measure',FACT,'Requests'),projection('Measure',FACT,'Open Requests'),projection('Measure',FACT,'Open 30 Plus Days'),projection('Measure',FACT,'Median Closure Days'),projection('Measure',FACT,'P90 Closure Days')]);sort_by(q,field('Measure',FACT,'Open Requests'),'Descending')
    add_visual(p,'workload-table','tableEx',24,402,1232,362,14000,q,{'columnHeaders':object_properties({'fontSize':literal(12),'wordWrap':literal(True),'backColor':color('#E9EFEB')}),'values':object_properties({'fontSize':literal(11)}),'grid':object_properties({'rowPadding':literal(7)}),'total':object_properties({'totals':literal(False)})},container('Open workload by service category'))
    text(p,'warning','Age bands are descriptive, not official service targets. Recent cohorts have had less time to close; closure percentiles exclude open records.',24,782,1232,48,15000,11)
    p=pages[2][0]
    for i,(name,label) in enumerate([('Source Records','All source records'),('Duplicate Records','Duplicates excluded'),('Missing Closure Dates','Missing closure dates'),('Invalid Closure Dates','Invalid closure dates'),('Open With Closure Date','Open with closure date')]):card(p,name,label,24+i*248,260,7000+i*1000)
    notes=[('One row per request','Six model tables: one request fact table, four related dimensions and one disconnected snapshot table. Relationships filter from dimensions to requests.'),('Closure calculations','Calendar days between submitted and closed dates. Valid nonduplicate Closed records only. Same-day closure is zero. Median and P90 are recomputed in the current filter context.'),('Open workload','Open status at extraction, limited to requests submitted January to September 2026. Does not reconstruct historical status, include older cohorts, or identify staffing needs.'),('Source quality','Missing and invalid dates are flagged. Explicit duplicate statuses are excluded from operational counts. Unknown dimension values remain visible. No street addresses or exact coordinates are included.'),('Interpretation','Closure is an administrative state, not proof of completed repair. No official SLA compliance, customer satisfaction, measured savings or City endorsement is claimed.')]
    for i,(heading,body) in enumerate(notes):
        text(p,f'h{i}',heading,24,405+i*83,300,32,14000+i*2000,14,INK);text(p,f'b{i}',body,330,405+i*83,926,67,15000+i*2000,12)
    write(PROJECT/'.gitignore','**/.pbi/\n')
    print(f'Built 3 report pages, {len(MEASURES)} measures and six embedded model tables. Native Desktop validation is still required.')

if __name__=='__main__':build_model();build_report()
