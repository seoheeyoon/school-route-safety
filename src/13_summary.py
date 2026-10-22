"""보고서 표에 들어간 요약 수치 출력: 정문 표본 31곳 비교, Q3 보도·속도 관리(학생 수 가중)."""
import os as _os
for _d in ('step2','q1','q3','fig','acc','net'): _os.makedirs(_d,exist_ok=True)
import pandas as pd, numpy as np
v=pd.read_csv('q1/q1_results_v2.csv').set_index('학교')
print('[Q1·Q2] 565개교  현재 %.1f%% (중앙값 %.1f%%)  대안 %.1f%% (중앙값 %.1f%%)  격차 +%.1f%%p'%(v.현재커버리지.mean(),v.현재커버리지.median(),v.대안_트리길이.mean(),v.대안_트리길이.median(),(v.대안_트리길이-v.현재커버리지).mean()))
print('        50%% 미만 %.1f%%  30%% 미만 %.1f%%  70%% 이상 %.1f%%  정문 300m 안 거주 %.1f%%  평균 등교거리 %.0fm'%((v.현재커버리지<50).mean()*100,(v.현재커버리지<30).mean()*100,(v.현재커버리지>=70).mean()*100,v['거주300m이내_비율'].mean(),v.평균등교거리_m.mean()))
try:
    h=pd.read_csv('q1/hand_results.csv'); p=v.loc[h.학교]
    print('[정문 31곳] 위치점 기준 %.1f→%.1f%% (격차 %.1f%%p) / 실제 정문 기준 %.1f→%.1f%% (격차 %.1f%%p) / 대안>현재 %d곳 / 학교별 차이 평균 %.1f%%p'%(
        p.현재커버리지.mean(),p.대안_트리길이.mean(),(p.대안_트리길이-p.현재커버리지).mean(),h.현재커버리지.mean(),h.대안_트리길이.mean(),(h.대안_트리길이-h.현재커버리지).mean(),
        (h.대안_트리길이>h.현재커버리지).sum(),np.abs(h.현재커버리지.values-p.현재커버리지.values).mean()))
except FileNotFoundError: print('[정문 31곳] q1/hand_results.csv 없음 (04를 정문 옵션으로 먼저 실행)')
c=pd.read_csv('q3/q3_coded.csv')
for g,s in c.groupby('지정구간'):
    w=s.추정통학학생수
    print('[Q3] 지정 구간 %s: 보도 없음·1.5m 미만 %.0f%%  30km/h 표시 %.0f%%  둘 다 양호 %.0f%%'%(g,(w*s.취약).sum()/w.sum()*100,(w*s['30표시']).sum()/w.sum()*100,(w*s.안전).sum()/w.sum()*100))
