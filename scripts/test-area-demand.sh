#!/usr/bin/env bash
# 수요 강도 API 확정 실측 v6 — 어제 성공 조합 기반
# 사용법: KTO_KEY='키' bash scripts/test-area-demand.sh
set -u
: "${KTO_KEY:?KTO_KEY 환경변수에 API 키를 넣고 실행하세요}"

BASE="https://apis.data.go.kr/B551011/AreaTarDemDsService"
COMMON="MobileOS=ETC&MobileApp=seasonroad&_type=json&pageNo=1&numOfRows=10"

t() { # $1=라벨 $2=쿼리
  R=$(curl -s --max-time 10 "${BASE}/areaTarSjrnDsList?serviceKey=${KTO_KEY}&${COMMON}&$2")
  TC=$(echo "$R" | grep -o '"totalCount":[0-9]*')
  echo "[$1] -> ${TC:-$(echo "$R" | head -c 100)}"
  [ -n "${3:-}" ] && { echo "$R" | head -c 1800; echo; }
}

echo "── 1) 어제 성공 조합 재현 (새 키 정상 여부 확인) ──"
t "재현: 202509/11/11530/2101" "baseYm=202509&areaCd=11&signguCd=11530&tarSjrnDsIxCd=2101" dump

echo "── 2) 해운대구로 검증 (법정동 26/26350) ──"
t "해운대: 202509/26/26350/2101" "baseYm=202509&areaCd=26&signguCd=26350&tarSjrnDsIxCd=2101" dump

echo "── 3) 지표코드 생략하면 전체 하위코드가 오는가 ──"
t "IxCd 생략: 202509/26/26350" "baseYm=202509&areaCd=26&signguCd=26350" dump

echo "── 4) 최신 기준월 탐색 (11/11530/2101 고정) ──"
for YM in 202606 202605 202604 202603 202602 202601 202512 202511 202510 202509; do
  t "baseYm=$YM" "baseYm=${YM}&areaCd=11&signguCd=11530&tarSjrnDsIxCd=2101"
done
