import os as _os
for _d in ('step2','q1','q3','fig','acc','net'): _os.makedirs(_d,exist_ok=True)
import gzip
import pickle, numpy as np, pandas as pd, networkx as nx, random
from scipy.spatial import cKDTree
G,nd=pickle.load(gzip.open('net/graph_main.pkl.gz','rb')); st=pickle.load(open('q1/q1_store.pkl','rb'))
XY={k:v for k,v in zip(nd.index, nd[['x','y']].values.astype(float))}
random.seed(1); names=random.sample(list(st),120); rows=[]
for n in names:
    df,a,b,tt,L=st[n]; Lw=G[a][b]['w']
    da=nx.single_source_dijkstra_path_length(G,a,cutoff=300,weight='w'); db=nx.single_source_dijkstra_path_length(G,b,cutoff=300,weight='w')
    dist={k:min(da.get(k,1e9)+tt*Lw, db.get(k,1e9)+(1-tt)*Lw) for k in set(da)|set(db)}
    inn={k for k,v in dist.items() if v<=300}
    used={frozenset((e.a,e.b)) for e in df.itertuples()}
    flow=[(XY[e.a],XY[e.b]) for e in df.itertuples() if e.a in XY and e.b in XY]
    if not flow: continue
    fm=np.array([(p+q)/2 for p,q in flow]); ft=cKDTree(fm)
    zl=0; zdup=0; seen=set()
    for u in inn:
        for v,d in G[u].items():
            if v in inn and frozenset((u,v)) not in seen:
                seen.add(frozenset((u,v)))
                if frozenset((u,v)) in used or u not in XY or v not in XY: continue
                p,q=XY[u],XY[v]; m=(p+q)/2; vec=q-p; l=np.hypot(*vec); zl+=d['w']
                if l==0: continue
                for i in ft.query_ball_point(m,15):
                    fp,fq=flow[i]; fv=fq-fp; fl=np.hypot(*fv)
                    if fl==0: continue
                    cos=abs(vec@fv)/(l*fl)
                    # distance from m to flow segment
                    t=np.clip(((m-fp)@fv)/(fl**2),0,1); dd=np.hypot(*(fp+t*fv-m))
                    if cos>0.9 and dd<15: zdup+=d['w']; break
    rows.append((n,zl,zdup))
r=pd.DataFrame(rows,columns=['학교','무흐름연장','평행중복연장'])
print(len(r),'무흐름 평균 m',r.무흐름연장.mean().round(0),'그중 평행중복(15m 이내, 거의 평행) 비율', (r.평행중복연장.sum()/r.무흐름연장.sum()*100).round(1))
r.to_csv('q1/dup_check.csv',index=False,encoding='utf-8-sig')
