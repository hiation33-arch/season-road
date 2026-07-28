#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""체류 강도 배치 수집 (B~C단계 빌드타임 스크립트)
서비스 대상 9개 시도의 전 시군구에 대해 체류강도 지표 2102~2105를 수집,
scripts/demand-raw.json 으로 저장한다. 임계값 분석은 이 결과로 별도 수행.

사용법 (Git Bash):  KTO_KEY='인코딩된_키' python scripts/fetch_demand.py
- 모든 요청 timeout 10초 (무한 대기 방지)
- 예상 호출 수: 시군구 목록 9콜 + 시군구(~165) x 지표 4 = 약 670콜, 4~8분
"""
import json, os, sys, time, urllib.request, urllib.parse

KEY = os.environ.get("KTO_KEY")
if not KEY:
    sys.exit("KTO_KEY 환경변수에 API 키를 넣고 실행하세요")

LDONG_BASE  = "https://apis.data.go.kr/B551011/KorService2/ldongCode2"
DEMAND_BASE = "https://apis.data.go.kr/B551011/AreaTarDemDsService/areaTarSjrnDsList"
COMMON = {"MobileOS": "ETC", "MobileApp": "seasonroad", "_type": "json"}
BASE_YM = "202606"          # 실측 확인된 최신 기준월 (2026-07-28)
IX_CODES = ["2102", "2103", "2104", "2105"]  # 숙박비중 / 1박 / 2박 / 3박
SIDOS = ["11", "26", "12", "43", "47", "48", "50", "51", "52"]
# 서울, 부산, 전남광주, 충북, 경북, 경남, 제주, 강원, 전북

def get(url, params):
    q = dict(COMMON); q.update(params)
    full = url + "?serviceKey=" + KEY + "&" + urllib.parse.urlencode(q)
    for attempt in range(2):  # 1회 재시도
        try:
            with urllib.request.urlopen(full, timeout=10) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if attempt: 
                print(f"  ! 실패: {params} ({e})")
                return None
            time.sleep(1)

def items(resp):
    try:
        it = resp["response"]["body"]["items"]
        if not it or it == "": return []
        it = it["item"]
        return it if isinstance(it, list) else [it]
    except (KeyError, TypeError):
        return []

result = {}
for sido in SIDOS:
    resp = get(LDONG_BASE, {"lDongRegnCd": sido, "numOfRows": 60})
    sgg_list = items(resp)
    print(f"시도 {sido}: 시군구 {len(sgg_list)}개")
    for sgg in sgg_list:
        code = sido + sgg["code"]          # 예: 26 + 350 = 26350
        entry = {"name": sgg["name"], "areaCd": sido}
        for ix in IX_CODES:
            resp = get(DEMAND_BASE, {"baseYm": BASE_YM, "areaCd": sido,
                                     "signguCd": code, "tarSjrnDsIxCd": ix,
                                     "numOfRows": 5, "pageNo": 1})
            rows = items(resp)
            entry["v" + ix] = float(rows[0]["tarSjrnDsIxVal"]) if rows else None
        result[code] = entry
        got = sum(1 for ix in IX_CODES if entry["v"+ix] is not None)
        print(f"  {code} {sgg['name']}: {got}/4")

out = os.path.join(os.path.dirname(__file__), "demand-raw.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"baseYm": BASE_YM, "fetched": time.strftime("%Y-%m-%d"), "sigungu": result},
              f, ensure_ascii=False, indent=1)
n_ok = sum(1 for v in result.values() if v.get("v2102") is not None)
print(f"\n완료: {len(result)}개 시군구 중 데이터 존재 {n_ok}개 → {out}")
