#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""demand-raw.json 픽스업: ① 전남광주 — 구코드(전남46/광주29)로 재수집
   (signguCd 생략하고 시도 단위 일괄 조회 시도) ② 타임아웃 4건 재시도
사용법: KTO_KEY='키' python scripts/fetch_demand_fix.py   (약 20콜)"""
import json, os, sys, time, urllib.request, urllib.parse

KEY = os.environ.get("KTO_KEY")
if not KEY: sys.exit("KTO_KEY 환경변수 필요")
BASE = "https://apis.data.go.kr/B551011/AreaTarDemDsService/areaTarSjrnDsList"
COMMON = {"MobileOS":"ETC","MobileApp":"seasonroad","_type":"json","numOfRows":60,"pageNo":1}
BASE_YM = "202606"
IX = ["2102","2103","2104","2105"]

def get(params):
    q = dict(COMMON); q.update(params)
    url = BASE + "?serviceKey=" + KEY + "&" + urllib.parse.urlencode(q)
    for a in range(3):
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if a == 2: print(f"  ! 실패 {params}: {e}"); return None
            time.sleep(2)

def items(resp):
    try:
        it = resp["response"]["body"]["items"]
        if not it or it == "": return []
        it = it["item"]
        return it if isinstance(it, list) else [it]
    except (KeyError, TypeError): return []

path = os.path.join(os.path.dirname(__file__), "demand-raw.json")
data = json.load(open(path, encoding="utf-8"))
sgg = data["sigungu"]

# ① 구코드 전남(46)/광주(29): signguCd 없이 시도 일괄 조회
for ac in ["46","29"]:
    for ix in IX:
        rows = items(get({"baseYm":BASE_YM,"areaCd":ac,"tarSjrnDsIxCd":ix}))
        print(f"areaCd={ac} ix={ix}: {len(rows)}행")
        for r in rows:
            code = r["signguCd"]
            e = sgg.setdefault(code, {"name":r.get("signguNm","?"),"areaCd":ac})
            e["v"+ix] = float(r["tarSjrnDsIxVal"])

# ② 타임아웃 재시도
for code, ix in [("43770","2102"),("47930","2105"),("47940","2105"),("48330","2102")]:
    rows = items(get({"baseYm":BASE_YM,"areaCd":code[:2],"signguCd":code,"tarSjrnDsIxCd":ix,"numOfRows":5}))
    if rows:
        sgg[code]["v"+ix] = float(rows[0]["tarSjrnDsIxVal"])
        print(f"재시도 OK: {code} {ix} = {rows[0]['tarSjrnDsIxVal']}")

json.dump(data, open(path,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
n = sum(1 for v in sgg.values() if v.get("v2102") is not None)
print(f"\n병합 완료: 총 {len(sgg)}개 항목, 데이터 존재 {n}개")
