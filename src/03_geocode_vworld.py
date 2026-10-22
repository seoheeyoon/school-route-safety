"""브이월드 지오코더로 도로명주소 -> 좌표 변환 (본인 PC에서 실행).

사용법:
  1) 같은 폴더에 schools_to_geocode.csv 를 둔다.
  2) 키를 환경변수로 넣는다 (키는 파일에 적지 않는다).
       Mac/Linux : export VWORLD_KEY="발급받은키"
       Windows   : set VWORLD_KEY=발급받은키        (PowerShell: $env:VWORLD_KEY="발급받은키")
  3) python3 geocode_vworld.py
  4) 결과: schools_geocoded.csv (학교명, 도로명주소, 경도, 위도, 상태, 사유 ...)
표준 라이브러리만 사용하므로 pip 설치가 필요 없다.
"""
import os as _os
for _d in ('step2','q1','q3','fig','acc','net'): _os.makedirs(_d,exist_ok=True)
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

KEY = os.environ.get("VWORLD_KEY", "").strip()
if not KEY:
    sys.exit("환경변수 VWORLD_KEY 가 비어 있습니다. 위 사용법 2)를 먼저 하세요.")

IN_FILE = "schools_to_geocode.csv"
OUT_FILE = "schools_geocoded.csv"
URL = "https://api.vworld.kr/req/address"


def call(address, addr_type):
    q = {
        "service": "address",
        "request": "getcoord",
        "version": "2.0",
        "crs": "epsg:4326",
        "address": address,
        "refine": "true",
        "simple": "false",
        "format": "json",
        "type": addr_type,  # road(도로명) / parcel(지번)
        "key": KEY,
    }
    url = URL + "?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def geocode(address):
    """도로명 -> 실패하면 지번 순서로 시도. (경도, 위도, 상태, 정제주소) 반환."""
    for t in ("road", "parcel"):
        try:
            j = call(address, t)
        except Exception as e:  # 네트워크 오류 등
            return None, None, f"오류:{e}", ""
        resp = j.get("response", {})
        if resp.get("status") == "OK":
            pt = resp["result"]["point"]
            refined = resp.get("refined", {}).get("text", "")
            return float(pt["x"]), float(pt["y"]), f"OK({t})", refined
    return None, None, "NOT_FOUND", ""


def main():
    with open(IN_FILE, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for i, r in enumerate(rows, 1):
        addr = r["도로명주소"].strip()
        x, y, status, refined = geocode(addr)
        out.append({**r, "경도": x, "위도": y, "상태": status, "정제주소": refined})
        print(f"[{i}/{len(rows)}] {r['학교명']}  {status}")
        time.sleep(0.15)  # 호출 간격
    cols = list(out[0].keys())
    with open(OUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)
    fail = [o["학교명"] for o in out if not o["상태"].startswith("OK")]
    print(f"\n완료: {len(out) - len(fail)}/{len(out)} 성공. 실패: {fail}")
    print(f"결과 파일: {OUT_FILE}")


if __name__ == "__main__":
    main()
