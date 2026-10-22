import os as _os
for _d in ('step2','q1','q3','fig','acc','net'): _os.makedirs(_d,exist_ok=True)
import gzip
import pandas as pd, numpy as np, pickle, geopandas as gpd, networkx as nx
from shapely.geometry import shape, Point, LineString
from scipy.spatial import cKDTree
import json
U='data/'
G,nd=pickle.load(gzip.open('net/graph_main.pkl.gz','rb')); st=pickle.load(open('q1/q1_store.pkl','rb'))
nid=np.array(nd.index); tree=cKDTree(nd[['x','y']].values)
# designated node set: network <=300 from each gate's snap (use edge endpoints a,b with offsets)
inside=set()
for n,(df,a,b,tt,L) in st.items():
    Lw=G[a][b]['w']
    da=nx.single_source_dijkstra_path_length(G,a,cutoff=300,weight='w'); db=nx.single_source_dijkstra_path_length(G,b,cutoff=300,weight='w')
    for k in set(da)|set(db):
        if min(da.get(k,1e9)+tt*Lw, db.get(k,1e9)+(1-tt)*Lw)<=300: inside.add(k)
# route links: max E over schools
E={}
for n,(df,a,b,tt,L) in st.items():
    for r in df.itertuples():
        if r.a=='V' or r.b=='V': continue
        k=frozenset((r.a,r.b)); E[k]=max(E.get(k,0),r.E)
ks=[k for k in E if all(x in nd.index for x in k)]
mids=np.array([nd.loc[list(k)][['x','y']].values.astype(float).mean(0) for k in ks]); ev=np.array([E[k] for k in ks])
segs=[nd.loc[list(k)][['x','y']].values.astype(float) for k in ks]; mt=cKDTree(mids)
def seg_d(p,s):
    a,b=s; d=b-a; L2=(d**2).sum(); t=0 if L2==0 else np.clip(((p-a)@d)/L2,0,1); return np.hypot(*(a+t*d-p))
rows=[]
for f,enc,typ in [('12_25_child.csv','cp949','보행어린이'),('12_25_schoolzone.csv','utf-8-sig','보호구역내어린이')]:
    d=pd.read_csv(U+f,encoding=enc); d=d[d.시도시군구명.str.startswith('서울')].copy()
    d['분석연도']=d.사고다발지id.astype(str).str[:4].astype(int)-1
    g=gpd.GeoDataFrame(d,geometry=gpd.points_from_xy(d.경도,d.위도),crs=4326).to_crs(5186)
    for _,r in g.iterrows():
        p=np.array([r.geometry.x,r.geometry.y]); _,ni=tree.query(p); node=nid[ni]
        _,idx=mt.query(p,k=10); best=min(((seg_d(p,segs[i]),i) for i in idx))
        ins=node in inside; onroute=best[0]<=30
        cat='지정구간 안' if ins else ('지정구간 밖·추정 통학경로 위' if onroute else '지정구간 밖·통학경로 아님')
        rows.append(dict(유형=typ,분석연도=r.분석연도,지점명=r.지점명,사고건수=r.사고건수,사상자수=r.사상자수,분류=cat,
          링크노출=round(float(ev[best[1]]),1) if onroute else 0, 경도=r.경도,위도=r.위도))
o=pd.DataFrame(rows); o.to_csv('acc/hotspot_overlay.csv',index=False,encoding='utf-8-sig')
for typ in o.유형.unique():
    for per,sub in [('전체',o[o.유형==typ]),('2021-2025',o[(o.유형==typ)&(o.분석연도>=2021)])]:
        print(typ,per,len(sub),sub.분류.value_counts().to_dict(),'사고건수',sub.groupby('분류').사고건수.sum().to_dict())
