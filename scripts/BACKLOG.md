# 시즌로드 백로그 (우선순위 낮음, 마감 요건 아님)

## 모바일 핀 밀집 개선
- 증상: 모바일 전국 줌에서 당일/1박/2박 핀이 동남권에 겹쳐 지역 구분이 어려움. 데스크탑은 정상.
- 해결안: CustomOverlay 클러스터링. 카카오 기본 MarkerClusterer는 Marker만 지원 → CustomOverlay는 못 씀.
  → 핀을 Marker로 전환하거나 클러스터링 직접 구현 필요 (IntersectionObserver tabindex·축제/반값 뱃지 렌더링 코어 건드림).
- 싼 대안(코어 무손상, ~15분): 모바일 뷰포트 시 초기 줌 레벨 축소 or 핀 CSS 크기 축소.
- 판단(2026-07-28): 기획서 요건 아님. 숙박 API·랜딩 2단계 완료 후 여유 되면 착수.

## 기타 남은 과제
- 숙박 API 미연동 (기획서 명시 기능 — 우선순위 높음)
- 랜딩 2단계: 기능 소개 카드 3종
- 연관 관광지 밀도 (contentId 불일치 + prefix 매칭 이슈로 보류 확정)
- searchKeyword1 실연동 시 keyword.normalize('NFC') 필수 (사용자 입력 IME/붙여넣기 NFD 대비)
