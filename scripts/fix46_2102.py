#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""전남(46) 숙박비중(2102)만 채우는 미니 픽스업. 사용법: KTO_KEY='키' python scripts/fix46_2102.py"""
import json, os, sys, time, urllib.request, urllib.parse
KEY = os.environ.get("KTO_KEY") or sys.exit("KTO_KEY 환경변수 필요")
BASE = "https://apis.data.go.kr/B551011/AreaTarDemDsService/areaTarSjrnDsList"
def get(params, timeout):
    q = {"MobileOS":"ETC","MobileApp":"seasonroad","_type":"json","pageNo":1,
         "baseYm":"202606","tarSjrnDsIxCd":"2102"}; q.update(params)
    url = BASE + "?serviceKey=" + KEY + "&" + urllib.parse.urlencode(q)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            it = json.loads(r.read().decode())["response"]["body"]["items"]
            if not it or it == "": return []
            it = it["item"]
            return it if isinstance(it, list) else [it]
    except Exception as e:
        print(f"  ! {params}: {e}"); return None

path = os.path.join(os.path.dirname(__file__), "demand-raw.json")
data = json.load(open(path, encoding="utf-8")); sgg = data["sigungu"]
rows = get({"areaCd":"46","numOfRows":60}, 30)  # 1차: 일괄, 타임아웃 30초
if rows:
    print(f"일괄 성공: {len(rows)}행")
    for r in rows: sgg[r["signguCd"]]["v2102"] = float(r["tarSjrnDsIxVal"])
else:  # 2차: 개별 폴백
    targets = [k for k in sgg if k.startswith("46") and sgg[k].get("v2102") is None]
    print(f"개별 폴백: {len(targets)}건")
    for code in targets:
        rows = get({"areaCd":"46","signguCd":code,"numOfRows":5}, 10)
        if rows: sgg[code]["v2102"] = float(rows[0]["tarSjrnDsIxVal"]); print(f"  {code} OK")
        time.sleep(0.3)
json.dump(data, open(path,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
miss = [k for k in sgg if k.startswith("46") and sgg[k].get("v2102") is None]
print(f"남은 결측: {len(miss)}건 {miss if miss else ''}")
