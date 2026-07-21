// Season Road — TourAPI + 네이버 데이터랩 프록시 워커
// 클라이언트(index.html)에서 KTO_API_KEY / NAVER_CLIENT_ID·SECRET을 완전히 제거하기 위해
// 요청을 대신 받아 서버 사이드 시크릿을 주입해 각 upstream으로 전달한다.
//
// 라우트:
//   /:base/:endpoint?...  — base = ko|en|zh|ja|bf (KTO Tour API, bf = 무장애 여행정보 KorWithService2)
//                            endpoint — areaBasedList2 | searchFestival2 | detailCommon2 | searchKeyword2 | detailWithTour2 등
//   /naver/datalab        — 네이버 데이터랩 검색어트렌드 프록시 (POST)

const UPSTREAM_BASES = {
  ko: 'https://apis.data.go.kr/B551011/KorService2',
  en: 'https://apis.data.go.kr/B551011/EngService2',
  zh: 'https://apis.data.go.kr/B551011/ChsService2',
  ja: 'https://apis.data.go.kr/B551011/JpnService2',
  bf: 'https://apis.data.go.kr/B551011/KorWithService2',
};

const NAVER_DATALAB_URL = 'https://openapi.naver.com/v1/datalab/search';
const VALID_SEASONS = ['spring', 'summer', 'autumn', 'winter']; // index.html의 SEASONS와 동일해야 함

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

// ── 네이버 데이터랩 검색어트렌드 프록시 ──
// 일일 호출 한도가 공식 문서에 명시돼 있지 않아 보수적으로, 계절(season)당 하루 1회만 실제
// 네이버 API를 호출하고 같은 날 동일 계절 요청은 Cloudflare Cache API로 응답을 재사용한다.
async function handleNaverDatalab(request, env) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'POST only' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json', ...corsHeaders() },
    });
  }

  let payload;
  try {
    payload = await request.json();
  } catch {
    return new Response(JSON.stringify({ error: 'invalid JSON body' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', ...corsHeaders() },
    });
  }

  const { season, keywordGroups } = payload || {};
  if (!VALID_SEASONS.includes(season)) {
    return new Response(JSON.stringify({ error: `season must be one of ${VALID_SEASONS.join('/')}` }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', ...corsHeaders() },
    });
  }
  if (!Array.isArray(keywordGroups) || keywordGroups.length === 0 || keywordGroups.length > 5) {
    return new Response(JSON.stringify({ error: 'keywordGroups(1~5) required' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json', ...corsHeaders() },
    });
  }

  const today = new Date().toISOString().slice(0, 10); // UTC 기준 일 단위 캐시 키
  const cache = caches.default;
  const cacheKey = new Request(`https://season-road-datalab-cache.internal/${season}/${today}`);

  const cached = await cache.match(cacheKey);
  if (cached) {
    const res = new Response(cached.body, cached);
    Object.entries(corsHeaders()).forEach(([k, v]) => res.headers.set(k, v));
    return res;
  }

  const end = new Date();
  const start = new Date(end);
  start.setDate(start.getDate() - 30);
  const fmt = d => d.toISOString().slice(0, 10);

  let upstreamRes;
  try {
    upstreamRes = await fetch(NAVER_DATALAB_URL, {
      method: 'POST',
      headers: {
        'X-Naver-Client-Id': env.NAVER_CLIENT_ID,
        'X-Naver-Client-Secret': env.NAVER_CLIENT_SECRET,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        startDate: fmt(start),
        endDate: fmt(end),
        timeUnit: 'date',
        keywordGroups,
      }),
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: 'upstream fetch failed', detail: String(e) }), {
      status: 502,
      headers: { 'Content-Type': 'application/json', ...corsHeaders() },
    });
  }

  const body = await upstreamRes.text();
  const res = new Response(body, {
    status: upstreamRes.status,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=86400',
      ...corsHeaders(),
    },
  });

  if (upstreamRes.status === 200) {
    await cache.put(cacheKey, res.clone());
  }

  return res;
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders() });
    }

    const url = new URL(request.url);
    const [, base, endpoint] = url.pathname.split('/'); // '' / kto 없이 /base/endpoint

    if (base === 'naver' && endpoint === 'datalab') {
      return handleNaverDatalab(request, env);
    }

    const upstreamBase = UPSTREAM_BASES[base];
    if (!upstreamBase || !endpoint) {
      return new Response(JSON.stringify({ error: 'invalid route. use /:base/:endpoint' }), {
        status: 400,
        headers: { 'Content-Type': 'application/json', ...corsHeaders() },
      });
    }

    const qs = new URLSearchParams(url.search);
    qs.set('serviceKey', env.KTO_API_KEY);

    const upstreamUrl = `${upstreamBase}/${endpoint}?${qs.toString()}`;

    try {
      const upstreamRes = await fetch(upstreamUrl);
      const body = await upstreamRes.text();
      return new Response(body, {
        status: upstreamRes.status,
        headers: { 'Content-Type': 'application/json', ...corsHeaders() },
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: 'upstream fetch failed', detail: String(e) }), {
        status: 502,
        headers: { 'Content-Type': 'application/json', ...corsHeaders() },
      });
    }
  },
};
