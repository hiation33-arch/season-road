# 계절 전환 로딩 지연 — 단계 1 진단 결과

측정일: 2026-08-20
측정 대상: https://hiation33-arch.github.io/season-road (실배포, GitHub Pages)
측정 방법: Chrome DevTools Resource Timing API + MutationObserver를 코드 실행(javascript_tool)으로 주입해 실측. (재현: 계절 탭 클릭 → `_seasonCache` 미스 시나리오)

## 결론 (요약)

**원인은 가설 E(Worker 프록시 병목) + 탭 락 UX 버그의 조합이지, 가설 A(시트 경쟁)·C(마커 누적)는 아니다.**

- 계절 탭 전환 시 `.tab[data-s]` 요소가 **`aria-disabled="true"`(= `pointer-events:none`)로 약 5.6초간 잠김**을 실측 확인. 이 구간 동안 사용자는 탭을 눌러도 아무 반응이 없다 — "느리다"고 체감되는 정체가 바로 이 구간이다.
- 잠금 구간은 `refreshSeasonTop5()` 내부에서 시군구(district)별 `/rlte/areaBasedList1` 호출을 **동시성 6로 26~41건 순차 배치 실행**하는 데서 발생. 실측 기준 계절 하나당 rlte 호출 61건, 소요 시간 약 3.95초(구간 시작~종료).
- Worker(`worker/index.js`)는 `/ko|en|zh|ja|bf/*` 및 `/demand`, `/rlte` 라우트에 **캐싱이 전혀 없다**. `/naver/datalab`만 Cloudflare Cache API로 계절+날짜 단위 캐싱이 되어 있고, 나머지는 매 요청마다 한국관광공사 API를 그대로 재호출한다(가설 E 확정).
- 가설 A(시트가 안 닫혀 렌더링 경쟁)·C(마커 누적)는 코드 검토 결과 배제: `exitHallyuMode()` → `resetSheet()`가 매 탭 클릭마다 시트를 확실히 닫고, `refreshPins()`는 `clearOverlays()`로 이전 마커를 `setMap(null)` 후 배열 초기화하고 나서 새로 그린다.
- 사용자가 보고한 "상세 시트를 연 뒤에만 느려진다"는 재현 조건은 **원인이 아니라 우연한 동반 조건**으로 보인다: 상세 시트를 전혀 열지 않고 여름→가을로 바로 전환했을 때도 동일하게 ~5.6초 탭 잠금이 재현됨(아래 측정 2). 다만 `openPlace()`가 여는 `loadNearbyStays`/`loadPlaceDetail` 백그라운드 요청이 같은 Worker 오리진에 몰려 있어 가설 D(취소되지 않은 상세 요청)가 미세하게 지연을 더할 가능성은 남아있음(연결 풀 경합) — 기여도는 작다고 판단.

## 실측 데이터

### 측정 1 — spring(초기 로드, 상세 시트 오픈 포함) → summer 전환

Resource Timing으로 잡힌 API 호출(도메인: `seasonroad-api.hiation33.workers.dev`), season 전환 시점 기준 상대 시각(ms):

| 구간 | 호출 수 | 시작~종료 |
|---|---|---|
| `areaBasedList2`/`searchFestival2` (관광지+축제) | 4 | 0 ~ 428 |
| `/demand/areaTarSjrnDsList` (도 단위 수요) | ~21 | 938 ~ 1218 |
| `/naver/datalab` | 1 | 954 ~ 1791 |
| `/rlte/areaBasedList1` (시군구 연관 관광지) | ~40+ | 950 ~ 3517 |

전체 API 활동 구간: 약 3.5초.

### 측정 2 — summer → autumn 전환 (상세 시트 미오픈, MutationObserver로 탭 잠금 시각 정밀 측정)

```
totalApiCalls: 81
spotCalls: 4      span 0 ~ 721ms      (areaBasedList2 + searchFestival2)
demandCalls: 15   span 1622 ~ 2155ms  (/demand/areaTarSjrnDsList)
rlteCalls: 61     span 1627 ~ 5578ms  (/rlte/areaBasedList1)  ← 최대 병목
overallSpan: 0 ~ 5578ms
```

탭 `aria-disabled` 상태 전이(관측 타임스탬프, 상대값):
```
t=6981ms  → 5개 탭 모두 aria-disabled="true"  (setLoading(true) 발생)
t=8610ms  → 5개 탭 모두 aria-disabled="true"  (재확인, 값 유지)
t=12590ms → 5개 탭 모두 aria-disabled="false" (setLoading(false), 잠금 해제)
```
→ **탭이 클릭 불가능한 상태로 남아있던 시간 ≈ 5.6초.** 이 구간이 rlte 호출 구간(끝 지점 5578ms 부근)과 거의 정확히 겹친다.

## 코드 원인 (`index.html`)

1. **`refreshSeasonTop5()`** (`index.html:3342`)
   - `_seasonTop5Cache[season]`가 없으면(해당 세션에서 그 계절 처음 방문) `lockTabs()`를 호출해 모든 계절 탭을 잠근다.
   - `_mapWithConcurrency(districtCodes, RLTE_CONCURRENCY=6, dc => _loadDistrictRlte(...))` — 계절당 시군구 26~41개를 동시성 6으로 순차 배치 처리(`index.html:3149,3353`). 시군구 하나당 요청 1건, 실측 200~440ms/건.
   - 이 함수는 탭 클릭 핸들러의 `exitHallyuMode()` 안에서 **await 없이 fire-and-forget으로 호출**된다(`index.html:4017`). 즉 스피너(`showSpinner`/`hideSpinner`, `loadSeasonData` 완료 시 사라짐)가 먼저 꺼진 뒤, 사용자 눈에는 로딩이 끝난 것처럼 보이는 시점에 **보이지 않는 두 번째 잠금**이 이어서 걸린다.
   - `lockTabs()`/`unlockTabs()`는 `_tabLockCount` 참조 카운트 방식(`index.html:1256`)이라 `showSpinner`의 잠금과 `refreshSeasonTop5`의 잠금이 겹쳐도 안전하게 누적되지만, 결과적으로 스피너가 사라진 후에도 탭 잠금이 수 초간 더 지속되는 것을 사용자가 알 방법이 없다(로딩 인디케이터 없음).

2. **`worker/index.js`**
   - `/demand`, `/rlte`, `/ko|en|zh|ja|bf/*` 라우트에 캐싱이 전혀 없다(`handleNaverDatalab`만 Cloudflare Cache API 사용, 나머지는 매번 upstream 재호출).
   - 계절 하나당 rlte 호출이 26~41건이므로, 캐시가 없으면 같은 시즌을 재방문(다른 세션/새로고침)해도 매번 동일한 지연이 반복된다.

## 단계 2 — 적용한 처방 (index.html, 커밋 1)

1. **탭 잠금 UX 버그 수정** — 실제로 적용한 핵심 처방.
   - `exitHallyuMode()`를 `async`로 바꾸고 `refreshSeasonTop5(currentSeason)`를 **await**하도록 변경(`index.html:4006` 부근).
   - 계절 탭 클릭 핸들러에서 `needsSeasonLoad`/`needsBFLoad`뿐 아니라 `needsTop5Rescore`(top5 캐시 미스 여부)도 스피너 표시 조건에 포함시키고, `exitHallyuMode()`를 같은 `try/finally` 블록 안에서 await하도록 변경(`index.html:4262` 부근). 초기 로드 경로(`index.html:4310` 부근)도 동일하게 `refreshSeasonTop5('spring')` 앞에 `return`을 붙여 스피너가 top5 완료까지 유지되게 함.
   - 효과: "로딩은 끝났는데 탭만 안 눌리는" 무응답 구간이 사라지고, 지연이 있는 동안 계속 스피너가 보인다. **네트워크 자체의 소요 시간(수 초)은 줄어들지 않지만, 사용자가 무응답을 버그로 오인하는 문제는 해소된다.**

2. **재발견된 2차 버그 — 무기한 hang 가능성**: 로컬 재현 중 시군구 rlte 요청 하나가 실제로 **90초 이상** 걸리는 사례를 실측(응답 없음 → 결국 504). 기존 코드에는 fetch 타임아웃이 전혀 없어, 위 1번 수정을 그대로 적용하면 "느린 하나의 요청이 전체 화면 스피너를 몇 분간 붙잡아 두는" 더 나쁜 회귀가 생길 수 있음을 확인.
   - 처방: `_fetchProvinceDemand`/`_fetchDistrictRelations`가 쓰는 fetch를 `AbortController` 기반 8초 타임아웃 헬퍼(`_fetchWithTimeout`, `index.html:3198` 부근)로 교체. 타임아웃 시 기존 catch 블록의 "부분 실패 허용" 경로(null 반환)로 자연스럽게 빠진다.
   - 이 발견 덕분에 원래 계획(1번만 적용)에서 범위가 확장됨 — **1번 단독 적용은 위험하므로 2번과 반드시 함께 적용**.

3. **가설 D 관련 저위험 정합성 버그 수정**: `openPlace()`/`openBFPlace()`가 여는 `loadNearbyStays`/`loadPlaceDetail`/`loadBFDetail`의 `.then()` 콜백이 `_lastOpened.kind`를 참조하는데, `resetSheet()`가 `_lastOpened = null`로 초기화하므로 계절 전환으로 시트가 닫힌 뒤 이 응답이 도착하면 `TypeError`(널 참조)가 발생하던 버그. `!_lastOpened ||` 가드 추가(4곳: `index.html:3636, 3663, 3918, 3927` 부근). 지연의 주 원인은 아니지만, 콘솔 예외를 없애고 연결 풀 경합을 줄이는 저위험 개선.

### 검증 상태 (모두 통과)

- `node --check`로 인라인 스크립트 문법 오류 없음 확인.
- 로컬 정적 서버(`python -m http.server`)에서 MutationObserver로 계측한 최종 재검증 결과(카카오맵 SDK가 이 세션 샌드박스에서 간헐적으로 `Failed to fetch`가 나서 재시도 끝에 성공):
  1. **미방문 계절 최초 전환**(winter): 탭 잠금(`aria-disabled`)과 스피너(`#apiSpinner` display)가 **정확히 동시에** on(t=4811ms)/off(t=9041ms) — 수정 전처럼 스피너가 먼저 사라지고 탭만 몰래 잠겨있는 "무응답 구간"이 사라짐. 잠금 지속시간 약 4.2초로 **8초 타임아웃 내에서 정상 종료**(과거 관측된 90초+ hang 재현 안 됨).
  2. **동일 계절 재방문**(spring, 이미 캐시됨): 잠금·스피너 이벤트 **0건** — 재방문이 빠르다는 기존 체감이 그대로 유지됨(회귀 없음).
  3. 수정 적용 전, 같은 방식으로 실측한 시군구 rlte 요청 중 하나가 실제로 90초 이상 소요된 사례를 확인했고(무한 대기 재현), `_fetchWithTimeout` 적용 후에는 동일한 시나리오에서 전체 흐름이 몇 초 내로 마무리됨을 확인.
- 배포 전 미커밋 상태. `git status`: `index.html` 변경만 존재(worker 변경 없음 → 이번 커밋은 index.html 단독).

## 단계 3 후보 (미착수)

- Worker에 `/rlte`, `/demand` 캐시 추가(`/naver/datalab`과 동일한 Cloudflare Cache API 패턴). 프록시 코드 변경이므로 index.html 변경과 별도 커밋.
- 클라이언트 측 rlte 결과를 localStorage 등으로 세션 간 영속화(데이터 최신성 트레이드오프 있어 검토 필요).
- 목표 응답시간(예: 500ms) 미달성 시에만 착수 — 현재 실측 기준 네트워크 자체 소요는 3.5~5.6초 수준이라 단계 3 없이는 "빠르다"고 보긴 어렵다. 사용자가 실제 체감상 이 정도 대기가 허용 가능한지 확인 필요.
