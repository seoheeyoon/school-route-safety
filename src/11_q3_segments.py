import os as _os
for _d in ('step2','q1','q3','fig','acc','net'): _os.makedirs(_d,exist_ok=True)
import gzip
import pickle, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from shapely.geometry import LineString
import os
def _kfont():
    for p in [os.environ.get('KFONT',''),'/System/Library/Fonts/AppleSDGothicNeo.ttc','/System/Library/Fonts/Supplemental/AppleGothic.ttf','C:/Windows/Fonts/malgun.ttf','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']:
        if p and os.path.exists(p): return p
    raise SystemExit('한글 폰트를 찾지 못했어요. KFONT 환경변수에 폰트 파일 경로를 넣어 주세요.')
fp=_kfont(); fm.fontManager.addfont(fp); plt.rcParams['font.family']=fm.FontProperties(fname=fp).get_name()
G,nd=pickle.load(gzip.open('net/graph_main.pkl.gz','rb'))
XY0={k:v for k,v in zip(nd.index, nd[['x','y']].values.astype(float))}
hs=pickle.load(open('q1/hand_store.pkl','rb'))['경동초등학교']; df,a,b,tt,L=hs
cs=pickle.load(open('q3/case_store.pkl','rb'))
sch={'경동초등학교':(df,{'V':XY0[a]+tt*(XY0[b]-XY0[a])}),'중대초등학교':cs['중대초등학교'][:2],'봉천초등학교':cs['봉천초등학교'][:2]}
z=gpd.read_file('hakgudo_students.gpkg'); rows=[]
for nm,(df,gx) in sch.items():
    XY=dict(XY0); XY.update(gx); xy=XY.get
    d=df.copy(); d['geom']=[LineString([xy(r.a),xy(r.b)]) if xy(r.a) is not None and xy(r.b) is not None else None for r in d.itertuples()]
    d=d.dropna(subset=['geom']); d['mid']=d.geom.apply(lambda g:g.interpolate(0.5,normalized=True)); d['in']=d.dmax<=300
    picks=[]
    for inside in (True,False):
        got=0
        for i,r in d[d['in']==inside].sort_values('E',ascending=False).iterrows():
            if r.len<8: continue
            if all(r.mid.distance(d.loc[j,'mid'])>=80 for j in picks): picks.append(i); got+=1
            if got==5: break
    s=d.loc[picks].sort_values(['in','E'],ascending=[False,False]).copy(); s['번호']=range(1,len(s)+1)
    ll=gpd.GeoSeries(s.mid,crs=5186).to_crs(4326)
    for (_,r),p in zip(s.iterrows(),ll):
        rows.append(dict(학교=nm,구간번호=r.번호,지정구간='안' if r['in'] else '밖',추정통학학생수=round(r.E),링크길이_m=round(r.len),문까지_보행거리_m=round(r.dmax),
            위도=round(p.y,6),경도=round(p.x,6),로드뷰=f'https://map.kakao.com/link/roadview/{p.y:.6f},{p.x:.6f}',지도=f'https://map.kakao.com/link/map/{nm[:2]}_{r.번호},{p.y:.6f},{p.x:.6f}'))
    key=nm.replace('초등학교',''); zz=z[(z.HAKGUDO_NM==f'서울{key}초통학구역')]
    minx,miny,maxx,maxy=zz.total_bounds; pad=150
    fig,ax=plt.subplots(figsize=(7.5,7.5),dpi=180)
    ids=set(nd[(nd.x>minx-pad)&(nd.x<maxx+pad)&(nd.y>miny-pad)&(nd.y<maxy+pad)].index)
    gpd.GeoSeries([LineString([XY0[u],XY0[v]]) for u in ids for v in G[u] if v in ids and str(u)<str(v)]).plot(ax=ax,color='#e3e3e3',lw=0.5)
    zz.boundary.plot(ax=ax,color='#888',lw=0.8,ls='--')
    g=gpd.GeoDataFrame(d,geometry='geom'); mx=g.E.max()
    for inside,c in [(False,'#9aa0a6'),(True,'#eb6834')]:
        sub=g[g['in']==inside]; sub.plot(ax=ax,color=c,linewidth=0.5+4*np.sqrt(sub.E/mx))
    for p in gx.values(): ax.plot(*p,'*',ms=15,color='k',zorder=6)
    for _,r in s.iterrows():
        dx,dy=(0,0)
        ax.plot(r.mid.x,r.mid.y,'o',ms=13,color='#eb6834' if r['in'] else '#2a78d6',mec='white',mew=1.5,zorder=7)
        ax.text(r.mid.x,r.mid.y,str(r.번호),ha='center',va='center',color='white',fontsize=7.5,fontweight='bold',zorder=8)
    ax.set_xlim(minx-pad,maxx+pad); ax.set_ylim(miny-pad,maxy+pad); ax.set_aspect('equal'); ax.set_axis_off()
    ax.set_title(f'{nm} Q3 확인 구간 (주황 1~5: 지정 구간 안, 파랑 6~10: 밖)',fontsize=9.5)
    ax.text(minx-pad+5,maxy+pad-20,'선: 추정 통학 경로(굵기=학생 수), 주황 선=문 300m 지정 구간, ★=학교 문',fontsize=6.5,va='top')
    plt.tight_layout(); plt.savefig(f'q3/map3_{nm[:2]}.png'); plt.close()
o=pd.DataFrame(rows); o.to_csv('q3/segments3_recomputed.csv',index=False,encoding='utf-8-sig')
print(o[['학교','구간번호','지정구간','추정통학학생수','링크길이_m','문까지_보행거리_m']].to_string(index=False))
