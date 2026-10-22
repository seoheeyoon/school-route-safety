import os as _os
for _d in ('step2','q1','q3','fig','acc','net'): _os.makedirs(_d,exist_ok=True)
import gzip
import pandas as pd, numpy as np, pickle, geopandas as gpd
from shapely.geometry import LineString
st=pickle.load(open('q1/q1_store.pkl','rb')); r=pd.read_csv('q1/q1_results_v2.csv')
G,nd=pickle.load(gzip.open('net/graph_main.pkl.gz','rb'))
def altc(df,L):
    d=df.sort_values('E',ascending=False); cl=d.len.cumsum(); prev=cl-d.len
    take=np.clip((L-prev)/d.len,0,1); return (d.E*d.len*take).sum()/(d.E*d.len).sum()
out=[]
for n in r.학교:
    df=st[n][0]; tot=(df.E*df.len).sum(); row={'학교':n}
    for R in (300,500):
        inz=df[df.dmax<=R]; row[f'현재_{R}']=(inz.E*inz.len).sum()/tot*100; row[f'대안_{R}']=altc(df,inz.len.sum())*100
    # connectivity check: top-E prefix connected to gate? child E<=parent E
    d=df.sort_values('E',ascending=False); L=df[df.dmax<=300].len.sum()
    cl=d.len.cumsum(); sel=d[cl-d.len<L]
    par=set(df.b); nodes=set(sel.a)|set(sel.b)
    # each selected edge's parent edge (edge whose child == this b) must be selected unless b is gate node
    child2={a:i for i,a in zip(df.index,df.a)}
    selidx=set(sel.index); miss=0
    for b in sel.b:
        if b in child2 and child2[b] not in selidx: miss+=1
    row['비연결_링크수']=miss; row['선택링크수']=len(sel)
    out.append(row)
s=pd.DataFrame(out); s.to_csv('q1/sens.csv',index=False,encoding='utf-8-sig')
w=r.아동수.values
for c in s.columns[1:5]: print(c,round(s[c].mean(),1),round(s[c].median(),1))
print('비연결 링크가 있는 학교',(s.비연결_링크수>0).sum(),'전체 선택링크 대비',s.비연결_링크수.sum()/s.선택링크수.sum())
# gu summary
res=r.merge(s,on='학교'); import re
g=gpd.read_file('gates_final.gpkg')[['학교명']]
# case candidates
res['정규']=res.증가_pp_분수
cand=res[(res.아동수>=500)].sort_values('현재커버리지').head(12)[['학교','아동수','현재커버리지','대안_분수포함','대안_트리길이','거주300m이내_비율']]
print(cand.to_string())
# gyeongdong layer
df,a,b,t,L=st['경동초등학교']
lines=[];
for _,e in df.iterrows():
    if e.a in nd.index and e.b in nd.index:
        lines.append(LineString([tuple(nd.loc[e.a][['x','y']]),tuple(nd.loc[e.b][['x','y']])]))
    else: lines.append(None)
df=df.assign(geometry=lines).dropna(subset=['geometry'])
gdf=gpd.GeoDataFrame(df,geometry='geometry',crs='EPSG:5186')
gdf['지정구간']=(gdf.dmax<=300)
d=gdf.sort_values('E',ascending=False); Lt=gdf[gdf.지정구간].len.sum(); d['cl']=d.len.cumsum(); gdf['대안구간']=gdf.index.isin(d[d.cl-d.len<Lt].index)
gdf['구분']=np.select([gdf.지정구간&gdf.대안구간,gdf.지정구간,gdf.대안구간],['둘다','현재만','대안만'],'그외')
gdf['아동수_E']=gdf.E.round(1)
gdf[['E','len','dmax','지정구간','대안구간','구분','geometry']].to_file('q1/gyeongdong_links.gpkg',driver='GPKG')
print(gdf.구분.value_counts())
