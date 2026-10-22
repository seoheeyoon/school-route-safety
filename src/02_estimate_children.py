import os as _os
for _d in ('step2','q1','q3','fig','acc','net'): _os.makedirs(_d,exist_ok=True)
import gzip
import geopandas as gpd, pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
c=pd.read_csv('data/11_2024년_성연령별인구_1.csv.gz',header=None,names=['yr','tract','item','v'],dtype=str)
c['n']=pd.to_numeric(c.v,errors='coerce')
na_val=2.0   # 비공개(N/A)는 1~4명 가정의 중간값 근사
def get(item):
    s=c[c.item==item].copy(); s['val']=s.n.fillna(na_val); s['masked']=s.n.isna()
    return s.set_index('tract')[['val','masked']]
a=get('in_age_002'); b=get('in_age_003')
t=pd.DataFrame(index=sorted(set(c.tract)))
t['p5_9']=a.val.reindex(t.index).fillna(0); t['p10_14']=b.val.reindex(t.index).fillna(0)
t['na']=a['masked'].reindex(t.index).fillna(False)|b['masked'].reindex(t.index).fillna(False)
t['kids']=0.6*t.p5_9+0.6*t.p10_14   # 만 7~12세 추정(인구총조사 기준일 11.1): 5~9세의 3/5 + 10~14세의 3/5 (연령 내 균등 가정)
print('tracts',len(t),'N/A tracts',int(t.na.sum()),'kids total',round(t.kids.sum()),'p5_9',t.p5_9.sum(),'p10_14',t.p10_14.sum())
bd=gpd.read_file('zip://bnd/tract_2025Q2_5186.zip!tract_2025Q2_5186.gpkg').merge(t[['kids']],left_on='code',right_index=True,how='left')
print('boundary tracts w/o data',bd.kids.isna().sum()); bd['kids']=bd.kids.fillna(0)
bd['a_t']=bd.area
z=gpd.read_file('tonghak/seoul_tonghak.gpkg'); z['geometry']=z.geometry.make_valid(); z['zid']=range(len(z))
ov=gpd.overlay(bd[['code','kids','a_t','geometry']],z[['zid','HAKGUDO_NM','HAKGUDO_GB','geometry']],how='intersection',keep_geom_type=True)
ov['kids_part']=ov.kids*ov.area/ov.a_t
zk=ov.groupby('zid').kids_part.sum()
z['kids']=z.zid.map(zk).fillna(0); z['area_km2']=z.area/1e6
inz=bd.kids.sum(); print('Seoul kids (all tracts)',round(inz),'in zones',round(z.kids.sum()),'(%.1f%%)'%(z.kids.sum()/inz*100))
s=z[z.HAKGUDO_GB=='0']; print('단독구역 563: kids mean %.0f median %.0f min %.0f max %.0f'%(s.kids.mean(),s.kids.median(),s.kids.min(),s.kids.max()))
j=z[z.HAKGUDO_GB=='1']; print('공동구역 66: kids total %.0f mean %.0f'%(j.kids.sum(),j.kids.mean()))
z[['HAKGUDO_NM','HAKGUDO_GB','area_km2','kids']].round(1).to_csv('step2/zone_kids_est.csv',index=False,encoding='utf-8-sig')
z.to_file('step2/zones_with_kids.gpkg',driver='GPKG'); bd.to_file('step2/tracts_with_kids.gpkg',driver='GPKG')
print(s.sort_values('kids',ascending=False)[['HAKGUDO_NM','area_km2','kids']].head(5).round(1).to_string(index=False))
print(s.sort_values('kids')[['HAKGUDO_NM','area_km2','kids']].head(5).round(1).to_string(index=False))
print(s[s.HAKGUDO_NM.str.contains('경동')][['HAKGUDO_NM','area_km2','kids']].round(1).to_string(index=False))
# 성동구 20개교 지표
