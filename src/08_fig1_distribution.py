import os as _os
for _d in ('step2','q1','q3','fig','acc','net'): _os.makedirs(_d,exist_ok=True)
import pandas as pd, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import os
def _kfont():
    for p in [os.environ.get('KFONT',''),'/System/Library/Fonts/AppleSDGothicNeo.ttc','/System/Library/Fonts/Supplemental/AppleGothic.ttf','C:/Windows/Fonts/malgun.ttf','/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']:
        if p and os.path.exists(p): return p
    raise SystemExit('한글 폰트를 찾지 못했어요. KFONT 환경변수에 폰트 파일 경로를 넣어 주세요.')
fp=_kfont(); fm.fontManager.addfont(fp)
plt.rcParams['font.family']=fm.FontProperties(fname=fp).get_name()
r=pd.read_csv('q1/q1_results_v2.csv')
cur=r.현재커버리지; alt=r.대안_트리길이
fig,axs=plt.subplots(2,1,figsize=(7.5,4.4),dpi=220,sharex=True); fig.patch.set_facecolor('#fcfcfb')
bins=np.arange(0,102.5,5)
for ax,data,c,lab in [(axs[0],cur,'#eb6834','현재 지정 구간 (정문 300m)'),(axs[1],alt,'#2a78d6','같은 길이를 노출이 큰 길부터 배분 (대안)')]:
    ax.set_facecolor('#fcfcfb')
    ax.hist(data,bins=bins,color=c,edgecolor='#fcfcfb',linewidth=2)
    m=data.median(); ax.axvline(m,color='#52514e',lw=1.2,ls='--')
    ax.text(m+1,ax.get_ylim()[1]*0.85,f'중앙값 {m:.0f}%',fontsize=8,color='#0b0b0b')
    ax.text(1,ax.get_ylim()[1]*0.85,lab,fontsize=8.5,color='#0b0b0b')
    for s_ in ['top','right']: ax.spines[s_].set_visible(False)
    for s_ in ['left','bottom']: ax.spines[s_].set_color('#cfcfcf')
    ax.tick_params(colors='#52514e',labelsize=8); ax.grid(axis='y',color='#ececec',lw=0.6); ax.set_axisbelow(True)
    ax.set_ylabel('학교 수',fontsize=8,color='#52514e')
axs[1].set_xlim(0,100)
axs[1].set_xlabel('추정 통학 노출(학생·m) 중 해당 구간이 덮는 비율 (%)',fontsize=8.5,color='#52514e')
axs[0].set_title(f'서울 초등학교 {len(r)}곳: 지정 구간은 통학 노출의 절반 이하를 덮는다',fontsize=10,loc='left',color='#0b0b0b')
plt.tight_layout(); plt.savefig('fig/fig1_distribution.png',facecolor=fig.get_facecolor())
print(cur.median(),alt.median())
