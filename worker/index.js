// Season Road — TourAPI 프록시 워커
// 클라이언트(index.html)에서 KTO_API_KEY를 완전히 제거하기 위해
// 요청을 대신 받아 서버 사이드 시크릿(env.KTO_API_KEY)을 주입해 공공데이터포털로 전달한다.
//
// 라우트: /kto/:base/:endpoint?...
//   base     — ko | en | zh | ja | bf  (bf = 무장애 여행정보, KorWithService2)
//   endpoint — areaBasedList2 | searchFestival2 | detailCommon2 | searchKeyword2 | detailWithTour2 등

const UPSTREAM_BASES = {
  ko: 'https://apis.data.go.kr/B551011/KorService2',
  en: 'https://apis.data.go.kr/B551011/EngService2',
  zh: 'https://apis.data.go.kr/B551011/ChsService2',
  ja: 'https://apis.data.go.kr/B551011/JpnService2',
  bf: 'https://apis.data.go.kr/B551011/KorWithService2',
};

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders() });
    }

    const url = new URL(request.url);
    const [, base, endpoint] = url.pathname.split('/'); // '' / kto 없이 /base/endpoint

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
