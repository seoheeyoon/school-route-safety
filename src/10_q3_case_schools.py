import os as _os
for _d in ('step2','q1','q3','fig','acc','net'): _os.makedirs(_d,exist_ok=True)
import gzip
import pickle, numpy as np, pandas as pd, geopandas as gpd, networkx as nx, warnings
warnings.filterwarnings('ignore')
from scipy.spatial import cKDTree
G,nd=pickle.load(gzip.open('net/graph_main.pkl.gz','rb'))
XY={k:v for k,v in zip(nd.index, nd[['x','y']].values.astype(float))}
tree=cKDTree(nd[['x','y']].values); nid=np.array(nd.index)
gates=gpd.read_file('gatecase_in2/g.gpkg')
z=gpd.read_file('hakgudo_students.gpkg'); t=gpd.read_file('step2/tracts_with_kids.gpkg'); t['a_t']=t.area
def seg_proj(p,a,b):
    d=b-a; L2=(d**2).sum(); tt=0 if L2==0 else np.clip(((p-a)@d)/L2,0,1); q=a+tt*d; return np.hypot(*(q-p)),tt
def insert_gate(p,name):
    _,idx=tree.query(p,k=30); best=None
    for i in idx:
        u=nid[i]
        if u not in G: continue
        for v in G[u]:
            if v not in XY: continue
            dd,tt=seg_proj(p,XY[u],XY[v])
            if best is None or dd<best[0]: best=(dd,u,v,tt)
    dd,u,v,tt=best; dat=dict(G[u][v]); L=dat['w']
    G.remove_edge(u,v); G.add_edge(u,name,**{**dat,'w':L*tt}); G.add_edge(name,v,**{**dat,'w':L*(1-tt)})
    XY[name]=XY[u]+tt*(XY[v]-XY[u]); return dd,(u,v,dat)
rows=[];store={}
for sch,gs in gates.groupby('학교명'):
    zr=z[z.HAKGUDO_NM==f"서울{sch.replace('초등학교','')}초통학구역"].iloc[0]
    sub=t[t.intersects(zr.geometry)][['code','kids','a_t','geometry']]
    pcs=gpd.overlay(sub,gpd.GeoDataFrame({'geometry':[zr.geometry]},crs=t.crs),how='intersection',keep_geom_type=True)
    pcs['raw']=pcs.kids*pcs.area/pcs.a_t; pcs['k']=pcs.raw/pcs.raw.sum()*zr.kids_adj
    pts=pcs.geometry.representative_point(); _,ci=tree.query(np.c_[pts.x,pts.y]); w=pd.Series(pcs.k.values,index=nid[ci]).groupby(level=0).sum()
    undo=[]; vnames=[]
    for j,(_,g) in enumerate(gs.iterrows()):
        nm=f'V{j}'; dd,info=insert_gate(np.array([g.geometry.x,g.geometry.y]),nm); undo.append((nm,info)); vnames.append((nm,round(dd,1)))
    G.add_node('S')
    for nm,_ in vnames: G.add_edge('S',nm,w=0.0,bld=False)
    pred,dist=nx.dijkstra_predecessor_and_distance(G,'S',weight='w',cutoff=12000)
    flow={k:0.0 for k in dist}
    for k,v in w.items():
        if k in flow: flow[k]+=v
    E=[]; gate_use={nm:0.0 for nm,_ in vnames}
    for k in sorted(dist,key=dist.get,reverse=True):
        if k=='S': continue
        par=pred[k][0]
        if par=='S': gate_use[k]+=flow[k]; continue
        flow[par]+=flow[k]; E.append((k,par,flow[k],G[k][par]['w'],max(dist[k],dist[par])))
    df=pd.DataFrame(E,columns=['a','b','E','len','dmax']); df=df[df.E>0]
    tot=(df.E*df.len).sum(); inz=df[df.dmax<=300]; cur=(inz.E*inz.len).sum()/tot; Lt=inz.len.sum()
    d2=df.sort_values('E',ascending=False); cl=d2.len.cumsum(); alt=(d2.E*d2.len*np.clip((Lt-(cl-d2.len))/d2.len,0,1)).sum()/tot
    near=w[[dist.get(k,1e9)<=300 for k in w.index]].sum()/w.sum()
    walk=np.average([dist[k] for k in w.index if k in dist],weights=[w[k] for k in w.index if k in dist])
    rows.append(dict(학교=sch,문수=len(gs),아동수=round(w.sum()),현재=round(cur*100,1),대안=round(alt*100,1),격차=round((alt-cur)*100,1),
        거주300m=round(near*100,1),평균등교거리=round(walk),문별이용=' / '.join(f'{k}:{v/w.sum()*100:.0f}%' for k,v in gate_use.items()),스냅=str(vnames)))
    store[sch]=(df,{nm:XY[nm].copy() for nm,_ in vnames},Lt)
    G.remove_node('S')
    for nm,(u,v,dat) in reversed(undo): G.remove_node(nm); G.add_edge(u,v,**dat)
r=pd.DataFrame(rows); print(r.to_string(index=False)); r.to_csv('q3/case_results.csv',index=False,encoding='utf-8-sig')
pickle.dump(store,open('q3/case_store.pkl','wb'))
