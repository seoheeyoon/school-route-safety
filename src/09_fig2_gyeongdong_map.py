import os as _os
for _d in ('step2','q1','q3','fig','acc','net'): _os.makedirs(_d,exist_ok=True)
import gzip
import pandas as pd, numpy as np, pickle, geopandas as gpd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from shapely.geometry import LineString, Point
import os
def _kfont():
    for p in [os.environ.get('KFONT',''),'/System/Library/Fonts/AppleSDGothicNeo.ttc','/System/Library/Fonts/Supplemental/AppleGothic.ttf','C:/Windows/Fonts/malgun.ttf','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']:
        if p and os.path.exists(p): return p
    raise SystemExit('한글 폰트를 찾지 못했어요. KFONT 환경변수에 폰트 파일 경로를 넣어 주세요.')
fp=_kfont()
fm.fontManager.addfont(fp); plt.rcParams['font.family']=fm.FontProperties(fname=fp).get_name()
G,nd=pickle.load(gzip.open('net/graph_main.pkl.gz','rb'))
st=pickle.load(open('q1/hand_store.pkl','rb')); df,a,b,tt,L300=st['경동초등학교']
pa=nd.loc[a][['x','y']].values.astype(float); pb=nd.loc[b][['x','y']].values.astype(float); V=pa+tt*(pb-pa)
def xy(n): return V if n=='V' else (nd.loc[n][['x','y']].values.astype(float) if n in nd.index else None)
geoms=[]
for _,e in df.iterrows():
    p,q=xy(e.a),xy(e.b); geoms.append(LineString([p,q]) if p is not None and q is not None else None)
g=gpd.GeoDataFrame(df.assign(geometry=geoms),geometry='geometry',crs=5186)
g['지정구간']=g.dmax<=300
Lt=g[g.지정구간].len.sum(); d=g.sort_values('E',ascending=False); d['cl']=d.len.cumsum()
sel=d[d.cl-d.len<Lt].index; g['대안구간']=g.index.isin(sel)
tot=(g.E*g.len).sum(); cur=(g[g.지정구간].E*g[g.지정구간].len).sum()/tot
tk=np.clip((Lt-(d.cl-d.len))/d.len,0,1); alt=(d.E*d.len*tk).sum()/tot
print('누락좌표 링크',g.geometry.isna().sum(),'노출비중',round((g[g.geometry.isna()].E*g[g.geometry.isna()].len).sum()/tot*100,2))
g=g.dropna(subset=['geometry'])
g['구분']=np.select([g.지정구간&g.대안구간,g.지정구간,g.대안구간],['둘다','현재만','대안만'],'그외')
g[['E','len','dmax','지정구간','대안구간','구분','geometry']].to_file('fig/gyeongdong_links_gate.gpkg',driver='GPKG',layer='links')
gpd.GeoDataFrame({'이름':['경동초 정문']},geometry=[Point(V)],crs=5186).to_file('fig/gyeongdong_links_gate.gpkg',driver='GPKG',layer='gate')
z=gpd.read_file('hakgudo_students.gpkg'); zz=z[z.HAKGUDO_NM.str.contains('경동')]
print('현재',round(cur*100,1),'대안',round(alt*100,1), g.구분.value_counts().to_dict())
# 학생이 지나는 길만 표시(E>0)지만, 지정구간 중 E=0 길도 보여주기 위해 300m 내 전체 링크 추가
near=set(); 
fig,ax=plt.subplots(figsize=(7.5,7.5),dpi=200)
zz.boundary.plot(ax=ax,color='#888',lw=0.8,ls='--')
# 300m 내 전체 링크(학생 0 포함) 회색
import networkx as nx
# background: all graph edges in bbox
minx,miny,maxx,maxy=zz.total_bounds; pad=150
bb=nd[(nd.x>minx-pad)&(nd.x<maxx+pad)&(nd.y>miny-pad)&(nd.y<maxy+pad)]
ids=set(bb.index); bg=[]
for u in ids:
    for v in G[u]:
        if v in ids and u<v: bg.append(LineString([nd.loc[u][['x','y']].values.astype(float),nd.loc[v][['x','y']].values.astype(float)]))
BLD='data/AL_D010_11_20261009.shp'  # 건물 바탕(선택)
if os.path.exists(BLD):
    gpd.read_file(BLD,bbox=(minx-pad,miny-pad,maxx+pad,maxy+pad)).plot(ax=ax,facecolor='#e9e9e9',edgecolor='none',zorder=0)
gpd.GeoSeries(bg,crs=5186).plot(ax=ax,color='#d4d4d4',lw=0.5,zorder=1)
w=lambda s: 0.6+3.5*np.sqrt(s/g.E.max())
col={'둘다':'#7b3294','현재만':'#f1a340','대안만':'#2c7bb6','그외':'#bbbbbb'}
lab={'둘다':'현재 지정 구간이면서 대안에도 포함','현재만':'현재 지정 구간에만 포함','대안만':'대안 구간에만 포함 (지정 밖)','그외':'그 밖의 통학 경로'}
for k in ['그외','현재만','대안만','둘다']:
    s=g[g.구분==k]
    if len(s): s.plot(ax=ax,color=col[k],linewidth=w(s.E),label=lab[k])
# 300m 지정 구간 중 학생 0인 링크 (dmax<=300 not in tree flows) -> compute via dijkstra
L=G[a][b]['w']; da=nx.single_source_dijkstra_path_length(G,a,cutoff=400,weight='w'); db=nx.single_source_dijkstra_path_length(G,b,cutoff=400,weight='w')
dist={n:min(da.get(n,1e9)+tt*L, db.get(n,1e9)+(1-tt)*L) for n in set(da)|set(db)}
inn={n for n,v in dist.items() if v<=300}
used={frozenset((e.a,e.b)) for e in df.itertuples()}
zero=[]
for u in inn:
    for v in G[u]:
        if v in inn and str(u)<str(v) and frozenset((u,v)) not in used and u in nd.index and v in nd.index:
            zero.append(LineString([nd.loc[u][['x','y']].values.astype(float),nd.loc[v][['x','y']].values.astype(float)]))
print('지정구간 내 학생 없는 링크',len(zero), round(sum(l.length for l in zero)))
gpd.GeoSeries(zero,crs=5186).plot(ax=ax,color='#f1a340',lw=0.9,ls='--',label='현재 지정 구간 중 추정 통학 학생이 없는 길')
ax.plot(*V,marker='*',ms=14,color='k',zorder=5,label='정문')
ax.set_xlim(minx-pad,maxx+pad); ax.set_ylim(miny-pad,maxy+pad); ax.set_axis_off(); ax.set_aspect('equal')
ax.legend(loc='lower left',fontsize=7,frameon=True)
ax.set_title(f'경동초 통학 노출과 지정 구간 (현재 {cur*100:.0f}% → 같은 길이 대안 {alt*100:.0f}%)',fontsize=10)
# scale bar 200m
x0=maxx+pad-260; y0=miny-pad+40; ax.plot([x0,x0+200],[y0,y0],'k-',lw=2); ax.text(x0+100,y0+15,'200m',ha='center',fontsize=7)
ax.text(minx-pad+5,maxy+pad-25,'선 굵기 = 추정 통학 학생 수 (학구 내 추정 아동, 최단경로 가정)\n바탕: 건물(GIS건물통합정보), 보행망(서울시 도보 네트워크)',fontsize=6.5,va='top')
plt.tight_layout(); plt.savefig('fig/fig2_gyeongdong.png'); print('ok')
