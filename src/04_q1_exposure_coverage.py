import os as _os
for _d in ('step2','q1','q3','fig','acc','net'): _os.makedirs(_d,exist_ok=True)
import gzip
import pandas as pd, numpy as np, geopandas as gpd, networkx as nx, pickle, re, warnings, sys, time
warnings.filterwarnings('ignore')
from scipy.spatial import cKDTree
EXC=['서울면중초등학교','서울반포초등학교','서울보광초등학교','서울천이초등학교','서울화곡초등학교']
G,nd=pickle.load(gzip.open('net/graph_main.pkl.gz','rb'))
nid=np.array(nd.index); xy=nd[['x','y']].values; tree=cKDTree(xy)
# edge midpoints for link snapping
eu=[];ev=[]
ns=set(nd.index)
for u,v in G.edges():
    if u in ns and v in ns: eu.append(u);ev.append(v)
eu=np.array(eu);ev=np.array(ev); P=nd.loc[eu][['x','y']].values; Q=nd.loc[ev][['x','y']].values
etree=cKDTree((P+Q)/2)
def snap_link(x,y,k=20):
    _,idx=etree.query([x,y],k=k); best=None
    for i in idx:
        a,b=P[i],Q[i]; d=b-a; L2=(d**2).sum()
        t=0 if L2==0 else np.clip(((np.array([x,y])-a)@d)/L2,0,1)
        pr=a+t*d; dist=np.hypot(*(pr-[x,y]))
        if best is None or dist<best[0]: best=(dist,eu[i],ev[i],t)
    return best
def norm(s):
    s=re.sub(r'\(.*?\)','',s); s=re.sub(r'(초등학교|초등통학구역|초통학구역|초교|초등|초)$','',s)
    return re.sub(r'^서울','',s)
import os,json
g=gpd.read_file(os.environ.get('GATES','gates_final.gpkg')); g=g[~g.학교명.isin(EXC)].reset_index(drop=True)
z=gpd.read_file('hakgudo_students.gpkg'); mode=pd.read_csv('corr/zone_target_kids.csv').set_index('HAKGUDO_NM')['mode']
z['mode']=z.HAKGUDO_NM.map(mode); z['joint']=z.HAKGUDO_NM.str.contains('공동통학구역')
t=gpd.read_file('step2/tracts_with_kids.gpkg'); t['a_t']=t.area
# gate -> single zone
sz=z[~z.joint]
j=gpd.sjoin(g,sz[['HAKGUDO_NM','geometry']],how='left',predicate='within'); j=j[~j.index.duplicated()]
miss=j[j.HAKGUDO_NM.isna()]
for i,r in miss.iterrows():
    d=sz.distance(r.geometry); k=d.idxmin(); print('학구밖 게이트',r.학교명,round(d.min()),sz.loc[k,'HAKGUDO_NM'])
    if d.min()<500: j.loc[i,'HAKGUDO_NM']=sz.loc[k,'HAKGUDO_NM']
g['zone']=j.HAKGUDO_NM.values; g['key']=g.학교명.map(norm)
zk={norm(n) for n in z[~z.joint].HAKGUDO_NM}
print('단일학구 키 중 게이트 없음:',sorted(zk-set(g.key)))
print('게이트 중 단일학구 키 없음:',sorted(g[~g.key.isin(zk)].학교명))
print('키 중복:',g[g.key.duplicated(keep=False)].학교명.tolist())
print('no zone:',g[g.zone.isna()].학교명.tolist())
keys=dict(zip(g.key,g.index)); ONLY=set(json.load(open(os.environ['ONLY']))) if os.environ.get('ONLY') else None
OUTP=os.environ.get('OUTP','q1/q1')

# pieces per zone
pc=gpd.overlay(t[['code','kids','a_t','geometry']],z[['HAKGUDO_NM','kids_adj','mode','geometry']],how='intersection',keep_geom_type=True)
pc['raw']=pc.kids*pc.area/pc.a_t; pc['ar']=pc.area
zs=pc.groupby('HAKGUDO_NM').agg(raw=('raw','sum'),ar=('ar','sum'))
pc=pc.join(zs,on='HAKGUDO_NM',rsuffix='_z')
pc['k']=np.where((pc['mode']=='area_only')|(pc.raw_z<1e-6),pc.kids_adj*pc.ar/pc.ar_z,pc.kids_adj*pc.raw/pc.raw_z)
pc['rp']=pc.geometry.representative_point(); pc['px']=pc.rp.x; pc['py']=pc.rp.y
pc=pc[pc.k>0]
# school -> weighted pieces
share={}   # school idx -> list of (df piece, weight)
lost_joint=0
for zn,sub in pc.groupby('HAKGUDO_NM'):
    if '공동통학구역' in zn:
        toks=re.findall(r'(서울.+?초)(?=서울|$)',zn.replace('공동통학구역',''))
        ids=[keys[norm(tk)] for tk in toks if norm(tk) in keys]
        if not ids: lost_joint+=sub.k.sum(); continue
        for i in ids: share.setdefault(i,[]).append((sub,1/len(ids)))
        lost_joint+=sub.k.sum()*(1-len(ids)/len(toks)) if len(ids)<len(toks) else 0
    else:
        k=norm(zn)
        if k in keys: share.setdefault(keys[k],[]).append((sub,1.0))
print('학교 수',len(g),'피스 보유',len(share),'공동학구 미배정 아동',round(lost_joint))
rows=[];store={}
t0=time.time()
for i,s in g.iterrows():
    if ONLY is not None and s.학교명 not in ONLY: continue
    if i not in share: print('조각없음',s.학교명); continue
    pcs=pd.concat([sb.assign(w=w) for sb,w in share[i]]); pcs['kk']=pcs.k*pcs.w
    # snap gate to link and insert virtual node
    d0,a,b,tt=snap_link(s.geometry.x,s.geometry.y); 
    dat=G[a][b]; L=dat['w']; V='V'
    G.remove_edge(a,b)
    G.add_edge(a,V,**{**dat,'w':L*tt}); G.add_edge(V,b,**{**dat,'w':L*(1-tt)})
    try:
        _,ci=tree.query(pcs[['px','py']].values); cn=nid[ci]
        w=pd.Series(pcs.kk.values,index=cn).groupby(level=0).sum()
        pred,dist=nx.dijkstra_predecessor_and_distance(G,V,weight='w',cutoff=12000)
        lost=w[~w.index.isin(dist)].sum()
        flow={k:0.0 for k in dist}
        for k,v in w.items():
            if k in flow: flow[k]+=v
        E=[]
        for k in sorted(dist,key=dist.get,reverse=True):
            if k==V: continue
            par=pred[k][0]; flow[par]+=flow[k]; E.append((k,par,flow[k],G[k][par]['w'],max(dist[k],dist[par]),G[k][par]['bld']))
        df=pd.DataFrame(E,columns=['a','b','E','len','dmax','bld'])
        # all links within 300m (incl. non-tree)
        near={n for n,dd in dist.items() if dd<=300}; L300=0.0; seen=set()
        for n in near:
            for m_,dt in G[n].items():
                if m_ in near:
                    key=(n,m_) if str(n)<str(m_) else (m_,n)
                    if key not in seen: seen.add(key); L300+=dt['w']
    finally:
        G.remove_node(V); G.add_edge(a,b,**dat)
    df=df[df.E>0]; tot=(df.E*df.len).sum()
    if len(df)==0 or tot<=0 or w[[k in dist for k in w.index]].sum()<=0:
        print('경로없음',s.학교명,round(d0)); rows.append(dict(학교=s.학교명,학구=s.zone,아동수=round(w.sum(),1),스냅거리_m=round(d0,1),경로없는아동=round(lost,1))); continue
    inz=df[df.dmax<=300]; cur=(inz.E*inz.len).sum()/tot
    d2=df.sort_values('E',ascending=False); d2['cl']=d2.len.cumsum(); alt=d2[d2.cl<=L300]; altc=(alt.E*alt.len).sum()/tot
    kids=w.sum(); near300=w[[dist.get(k,1e9)<=300 for k in w.index]].sum()/kids
    ok=[k in dist for k in w.index]; walk=np.average([dist[k] for k in w.index if k in dist],weights=w.values[ok])
    rows.append(dict(학교=s.학교명,학구=s.zone,아동수=round(kids,1),스냅거리_m=round(d0,1),지정구간연장_km=round(L300/1000,3),평균등교거리_m=round(walk),
       거주300m이내_비율=round(near300*100,1),현재커버리지=round(cur*100,2),대안커버리지=round(altc*100,2),증가_pp=round((altc-cur)*100,2),
       건물내_노출비중=round((df.E*df.len)[df.bld].sum()/tot*100,1),경로없는아동=round(lost,1),노출링크총연장_km=round(df.len.sum()/1000,2)))
    store[s.학교명]=(df[['a','b','E','len','dmax']],a,b,tt,L300)
    if len(rows)%50==0: print(len(rows),round(time.time()-t0),'s',flush=True)
r=pd.DataFrame(rows)
# 동일 연장 대안(보고서 기준): 지정 구간 중 학생이 지나는 링크 길이(B)만큼 노출 큰 링크부터 채움(마지막 링크는 비율 반영)
def _alt(df,B):
    tot=(df.E*df.len).sum(); d=df.sort_values('E',ascending=False); cum=d.len.cumsum(); prev=cum-d.len
    return (d.E*np.clip(B-prev,0,d.len)).sum()/tot*100
ext={}
for n,(df,a_,b_,tt_,L_) in store.items():
    B=df.loc[df.dmax<=300,'len'].sum()
    ext[n]=dict(대안_분수포함=round(_alt(df,L_),2),대안_트리길이=round(_alt(df,B),2),지정구간_유량링크연장_km=round(B/1000,3))
e=pd.DataFrame.from_dict(ext,orient='index'); r=r.join(e,on='학교'); r['증가_pp_분수']=(r.대안_분수포함-r.현재커버리지).round(2)
r.to_csv(OUTP+'_results.csv',index=False,encoding='utf-8-sig'); pickle.dump(store,open(OUTP+'_store.pkl','wb'))
if OUTP=='q1/q1': r.to_csv('q1/q1_results_v2.csv',index=False,encoding='utf-8-sig')
print('현재 포괄률 평균 %.1f%%, 동일 연장 대안 평균 %.1f%%'%(r.현재커버리지.mean(),r.대안_트리길이.mean()))
print(r.drop(columns=['학교','학구']).describe().round(2).to_string())
