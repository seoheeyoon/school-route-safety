import os as _os
for _d in ('step2','q1','q3','fig','acc','net'): _os.makedirs(_d,exist_ok=True)
import gzip
import pickle, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
from shapely.geometry import LineString
import os
def _kfont():
    for p in [os.environ.get('KFONT',''),'/System/Library/Fonts/AppleSDGothicNeo.ttc','/System/Library/Fonts/Supplemental/AppleGothic.ttf','C:/Windows/Fonts/malgun.ttf','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']:
        if p and os.path.exists(p): return p
    raise SystemExit('한글 폰트를 찾지 못했어요. KFONT 환경변수에 폰트 파일 경로를 넣어 주세요.')
fp=_kfont(); fm.fontManager.addfont(fp); plt.rcParams['font.family']=fm.FontProperties(fname=fp).get_name()
G,nd=pickle.load(gzip.open('net/graph_main.pkl.gz','rb')); XY0={k:v for k,v in zip(nd.index, nd[['x','y']].values.astype(float))}
hs=pickle.load(open('q1/hand_store.pkl','rb'))['경동초등학교']; df0,a,b,tt,L=hs; cs=pickle.load(open('q3/case_store.pkl','rb'))
sch={'경동초등학교':(df0,{'V':XY0[a]+tt*(XY0[b]-XY0[a])}),'중대초등학교':cs['중대초등학교'][:2],'봉천초등학교':cs['봉천초등학교'][:2]}
cov={'경동초등학교':(43,61),'중대초등학교':(36,70),'봉천초등학교':(37,87)}
BLD='data/AL_D010_11_20261009.shp'  # 건물 바탕(선택)
q=pd.read_csv('q3/q3_coded.csv'); s3=pd.read_csv('q3/segments3.csv')
q=q.merge(s3[['학교','구간번호','위도','경도']],on=['학교','구간번호'])
pts=gpd.GeoSeries(gpd.points_from_xy(q.경도,q.위도),crs=4326).to_crs(5186); q['x']=pts.x.values; q['y']=pts.y.values
z=gpd.read_file('hakgudo_students.gpkg')
col={'1.5m 이상':'#2a78d6','1.5m 미만':'#eda100','없음':'#e34948'}
fig,axs=plt.subplots(1,3,figsize=(15,6.2),dpi=200)
for ax,(nm,(df,gx)) in zip(axs,sch.items()):
    XY=dict(XY0); XY.update(gx)
    d=df[[XY.get(r.a) is not None and XY.get(r.b) is not None for r in df.itertuples()]].copy()
    d['geom']=[LineString([XY[r.a],XY[r.b]]) for r in d.itertuples()]
    zz=z[z.HAKGUDO_NM==f"서울{nm.replace('초등학교','')}초통학구역"]; minx,miny,maxx,maxy=zz.total_bounds; pad=120
    ids=set(nd[(nd.x>minx-pad)&(nd.x<maxx+pad)&(nd.y>miny-pad)&(nd.y<maxy+pad)].index)
    if os.path.exists(BLD):  # 건물 바탕(선택): data/AL_D010_11_20261009.shp
        gpd.read_file(BLD,bbox=(minx-pad,miny-pad,maxx+pad,maxy+pad)).plot(ax=ax,facecolor='#e9e9e9',edgecolor='none',zorder=0)
    gpd.GeoSeries([LineString([XY0[u],XY0[v]]) for u in ids for v in G[u] if v in ids and str(u)<str(v)]).plot(ax=ax,color='#d4d4d4',lw=0.45,zorder=1)
    zz.boundary.plot(ax=ax,color='#999',lw=0.7,ls='--')
    g=gpd.GeoDataFrame(d,geometry='geom'); mx=g.E.max()
    for inside,c in [(False,'#a9adb2'),(True,'#eb6834')]:
        sub=g[(g.dmax<=300)==inside]; sub.plot(ax=ax,color=c,linewidth=0.4+3.6*np.sqrt(sub.E/mx))
    for p in gx.values(): ax.plot(*p,'*',ms=13,color='k',zorder=6)
    for _,r in q[q.학교==nm].iterrows():
        ax.plot(r.x,r.y,'o' if r['30표시'] else '^',ms=12,color=col[r.보도],mec='white',mew=1.3,zorder=7)
        ax.text(r.x,r.y-1,str(int(r.구간번호)),ha='center',va='center',color='white',fontsize=6.5,fontweight='bold',zorder=8)
    ax.set_xlim(minx-pad,maxx+pad); ax.set_ylim(miny-pad,maxy+pad); ax.set_aspect('equal'); ax.set_axis_off()
    c0,c1=cov[nm]; ax.text(0.0,1.01,f"{nm.replace('등학교','')}  포괄률 {c0}% → 동일 연장 대안 {c1}%",transform=ax.transAxes,fontsize=10.5)
h=[Line2D([],[],color='#eb6834',lw=3,label='지정 구간(문 300m) 안 통학 경로'),Line2D([],[],color='#a9adb2',lw=3,label='지정 구간 밖 통학 경로 (굵기=추정 학생 수)'),
   Line2D([],[],marker='*',ls='',color='k',ms=11,label='학교 문'),Line2D([],[],marker='s',ls='',color='#e0e0e0',ms=10,label='건물'),
   Line2D([],[],marker='o',ls='',color=col['1.5m 이상'],ms=10,label='보도 1.5m 이상'),Line2D([],[],marker='o',ls='',color=col['1.5m 미만'],ms=10,label='보도 1.5m 미만'),
   Line2D([],[],marker='o',ls='',color=col['없음'],ms=10,label='보도 없음(차·보행 혼용)'),
   Line2D([],[],marker='o',ls='',color='#777',ms=10,label='30km/h 표지·노면표시 있음'),Line2D([],[],marker='^',ls='',color='#777',ms=10,label='30km/h 표지 확인 안 됨')]
fig.legend(handles=h,loc='lower center',ncol=4,fontsize=8.5,frameon=False)
fig.suptitle('그림 3. 사례교 노출 상위 30구간의 보도·속도 관리 현황 (1~5: 지정 구간 안, 6~10: 밖, 로드뷰 확인)',fontsize=12,x=0.01,ha='left')
plt.tight_layout(rect=[0,0.08,1,0.95]); plt.savefig('q3/fig3_cases.png'); print('ok')
