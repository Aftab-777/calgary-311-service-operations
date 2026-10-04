(function(root){
  function add(target,pairs){ for(const [v,n] of pairs)target.set(+v,(target.get(+v)||0)+n); }
  function percentile(hist,p){
    const values=[...hist.entries()].sort((a,b)=>a[0]-b[0]),n=values.reduce((s,a)=>s+a[1],0);
    if(!n)return null;
    const pos=(n-1)*p,lo=Math.floor(pos),hi=Math.ceil(pos);
    let used=0,low,high;
    for(const [v,count] of values){if(low===undefined&&used+count>lo)low=v;if(used+count>hi){high=v;break;}used+=count;}
    return low+(high-low)*(pos-lo);
  }
  function aggregate(cells){
    const out={total:0,duplicates:0,open:0,closed:0,other:0,closure:new Map(),ages:new Map(),weekdays:[0,0,0,0,0,0,0],channels:{},quality:{}};
    for(const c of cells){for(const k of ['total','duplicates','open','closed','other'])out[k]+=c[k];add(out.closure,c.closure);add(out.ages,c.ages);for(let i=0;i<7;i++)out.weekdays[i]+=c.weekdays[i];for(const [k,n]of Object.entries(c.channels))out.channels[k]=(out.channels[k]||0)+n;for(const [k,n]of Object.entries(c.quality))out.quality[k]=(out.quality[k]||0)+n;}
    out.operational=out.total-out.duplicates;out.median=percentile(out.closure,.5);out.p90=percentile(out.closure,.9);out.medianAge=percentile(out.ages,.5);out.closureSample=[...out.closure.values()].reduce((a,b)=>a+b,0);out.open30=[...out.ages].filter(([d])=>d>=30).reduce((s,[,n])=>s+n,0);
    return out;
  }
  const api={aggregate,percentile};root.Metrics=api;if(typeof module!=='undefined')module.exports=api;
})(typeof window==='undefined'?globalThis:window);
