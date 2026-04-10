# DESIGN.md — Season Road

> 계절과 트렌드로 이어지는 여행 코스 추천 웹서비스  
> 2026 한국관광공사 관광데이터 활용 공모전 출품작

---

## 1. 디자인 철학

- **자연스러움**: 계절과 여행의 감성을 억지스럽지 않게 담는다
- **차분함**: 과한 애니메이션, 강한 색 대비보다 은은하고 세련된 인상
- **명확함**: 지도 중심 서비스 특성상 UI는 최대한 군더더기 없이
- **모바일 우선**: 375px 기준 설계, 데스크톱은 확장

---

## 2. 컬러 시스템

### 브랜드 컬러 (Primary)

| 이름 | HEX | 용도 |
|------|-----|------|
| Primary 500 | `#22c55e` | 메인 버튼, 활성 탭, 강조 |
| Primary 400 | `#4ade80` | 호버 상태 |
| Primary 300 | `#86efac` | 배경 강조, 보조 |
| Primary 100 | `#dcfce7` | 카드 배경, 태그 배경 |
| Primary 900 | `#14532d` | 텍스트 강조 |

### 중립 컬러 (Neutral)

| 이름 | HEX | 용도 |
|------|-----|------|
| Gray 900 | `#111827` | 메인 텍스트 |
| Gray 600 | `#4b5563` | 서브 텍스트 |
| Gray 400 | `#9ca3af` | 힌트, 비활성 텍스트 |
| Gray 200 | `#e5e7eb` | 구분선, 테두리 |
| Gray 100 | `#f3f4f6` | 페이지 배경 |
| White     | `#ffffff` | 카드, 모달 배경 |

### 계절 컬러

| 계절 | HEX | 설명 |
|------|-----|------|
| 봄 | `#fde047` | 파스텔 노랑 |
| 여름 | `#4ade80` | 파스텔 초록 |
| 가을 | `#fb923c` | 파스텔 주황 |
| 겨울 | `#38bdf8` | 파스텔 바다색 |

### 핀 컬러 (지도)

| 핀 종류 | HEX | 설명 |
|---------|-----|------|
| 당일 코스 | `#22c55e` | 초록 |
| 1박 코스 | `#ef4444` | 빨강 |
| 2박 코스 | `#3b82f6` | 파랑 |
| 한류 촬영지 | `#a855f7` | 보라 |
| 무장애 코스 | `#f59e0b` | 황금색 |

---

## 3. 타이포그래피

### 폰트

```css
--font-primary: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif;
--font-english: 'DM Sans', sans-serif;
```

- **한글**: Pretendard (CDN 사용, 가볍고 가독성 우수)
- **영문/숫자**: DM Sans (모던하고 여행 감성에 어울림)

### 스케일

| 이름 | 크기 | 굵기 | 용도 |
|------|------|------|------|
| Display | 24px | 700 | 페이지 타이틀 |
| Heading 1 | 20px | 600 | 섹션 제목 |
| Heading 2 | 17px | 600 | 카드 제목 |
| Body | 15px | 400 | 본문 |
| Caption | 13px | 400 | 부가 정보, 태그 |
| Micro | 11px | 400 | 뱃지, 라벨 |

---

## 4. 컴포넌트 스타일

### 버튼

```css
/* Primary */
background: #22c55e;
color: #ffffff;
border-radius: 10px;
padding: 12px 20px;
font-size: 15px;
font-weight: 600;

/* Secondary */
background: #ffffff;
border: 1.5px solid #22c55e;
color: #22c55e;

/* 비활성 */
background: #e5e7eb;
color: #9ca3af;
```

### 카드

```css
background: #ffffff;
border-radius: 16px;
box-shadow: 0 1px 4px rgba(0,0,0,0.08);
padding: 16px;
```

### 탭 (계절 필터)

```css
/* 활성 탭 */
background: 계절별 컬러 (100);
color: 계절별 컬러 (900);
border-bottom: 2.5px solid 계절별 컬러 (500);
border-radius: 0;
font-weight: 600;

/* 비활성 탭 */
color: #9ca3af;
border-bottom: 2.5px solid transparent;
```

### 핀 (카카오맵 커스텀 오버레이)

```
크기: 32×40px
형태: 상단 원형 + 하단 삼각형 꼬리
테두리: 흰색 2px stroke
그림자: 0 2px 6px rgba(0,0,0,0.2)
```

### 바텀시트 (코스 상세)

```css
position: fixed;
bottom: 0;
border-radius: 20px 20px 0 0;
background: #ffffff;
max-height: 80vh;
overflow-y: auto;
padding: 20px 16px;
```

---

## 5. 레이아웃

### 모바일 (375px 기준)

```
┌─────────────────┐
│  헤더 (56px)    │  로고 + 검색 + 메뉴
├─────────────────┤
│  계절 탭 (48px) │  봄/여름/가을/겨울
├─────────────────┤
│                 │
│   카카오맵      │  flex: 1 (나머지 전체)
│                 │
│   [핀들]        │
│                 │
├─────────────────┤
│ 바텀시트 (접힘) │  56px (핸들바만 노출)
└─────────────────┘
```

### 데스크톱 (1024px+)

```
┌──────────┬──────────────────┐
│          │  헤더             │
│  사이드  ├──────────────────┤
│  패널    │                  │
│  (360px) │   카카오맵        │
│          │   (나머지 전체)   │
│  코스    │                  │
│  목록    │                  │
└──────────┴──────────────────┘
```

---

## 6. 간격 시스템

```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
```

---

## 7. 아이콘

- **라이브러리**: Lucide Icons (경량, 일관성 우수)
- **크기**: 20px (기본), 24px (헤더), 16px (인라인)
- **색상**: Gray 600 기본, Primary 500 활성

---

## 8. 반응형 브레이크포인트

| 이름 | 기준 | 설명 |
|------|------|------|
| mobile | 375px~ | 기본 설계 기준 |
| tablet | 768px~ | 사이드패널 등장 |
| desktop | 1024px~ | 풀 레이아웃 |

---

## 9. 다국어 대응 (한·영·중·일)

- 폰트: 한글(Pretendard), 영문(DM Sans), 중·일(시스템 폰트 fallback)
- 텍스트 길이 차이 고려 → 버튼/태그 너비 고정하지 않고 `min-width` 사용
- RTL 미지원 (중·일 모두 LTR)

---

## 10. 접근성 (무장애 코스 기능 관련)

- 색상만으로 정보 전달 금지 → 핀에 아이콘/텍스트 병행
- 터치 타깃 최소 44×44px
- 폰트 크기 최소 13px
- 이미지 alt 텍스트 필수

---

*최종 수정: 2026-04-10*
