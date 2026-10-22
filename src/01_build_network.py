"""서울시 자치구별 도보 네트워크(OA-21208) CSV -> 보행 그래프(networkx) 생성.
입력: data/서울시_자치구별_도보_네트워크_공간정보.csv (cp949)
출력: net/graph_main.pkl.gz  (G, nd)  nd = 노드 좌표(EPSG:5186) DataFrame
규칙: 링크 유형 코드 첫 자리가 1(보행자 통행 가능)인 링크만 사용, 건물내 링크 유지, 가장 큰 연결요소만 사용.
"""
import os as _os
for _d in ('step2','q1','q3','fig','acc','net'): _os.makedirs(_d,exist_ok=True)
import gzip
import sys, pickle, pandas as pd, networkx as nx
from shapely import wkt
from pyproj import Transformer
src=sys.argv[1] if len(sys.argv)>1 else 'data/서울시_자치구별_도보_네트워크_공간정보.csv'
d=pd.read_csv(src,encoding='cp949',low_memory=False)
tf=Transformer.from_crs(4326,5186,always_xy=True)
nodes=d[d['노드링크 유형']=='NODE'].copy()
pts=nodes['노드 WKT'].map(wkt.loads)
x,y=tf.transform(pts.map(lambda p:p.x).values, pts.map(lambda p:p.y).values)
nd=pd.DataFrame({'x':x,'y':y},index=nodes['노드 ID'].astype(int).astype(str))
nd=nd[~nd.index.duplicated()]
L=d[(d['노드링크 유형']=='LINK')&(d['링크 유형 코드'].fillna(0)>=1000)]
G=nx.Graph()
for r in L.itertuples(index=False):
    u=str(int(r[7])); v=str(int(r[8]))
    G.add_edge(u,v,w=float(r[9]),lid=str(r[5]),gu=r[11],bld=bool(r[21]==1),cw=bool(r[19]==1),ov=bool(r[18]==1))
main=max(nx.connected_components(G),key=len); G=G.subgraph(main).copy()
nd=nd[nd.index.isin(G.nodes)]
print('nodes',G.number_of_nodes(),'edges',G.number_of_edges(),'with coords',len(nd))
pickle.dump((G,nd),gzip.open('net/graph_main.pkl.gz','wb'))
