// Netlify serverless proxy — vidarebefordrar requests till Automile
// Stöder GET och POST med Authorization-header

export default async (req, context) => {
  const cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
  };

  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: cors });
  }

  const url = new URL(req.url);
  const target = url.searchParams.get('url');

  if (!target) {
    return new Response(JSON.stringify({ error: 'Missing url parameter' }), {
      status: 400, headers: { ...cors, 'Content-Type': 'application/json' }
    });
  }

  // Bygg vidarebefordrade headers
  const headers = {};
  const auth = req.headers.get('Authorization');
  const ct = req.headers.get('Content-Type');
  const xrw = req.headers.get('X-Requested-With');
  if (auth) headers['Authorization'] = auth;
  if (ct) headers['Content-Type'] = ct;
  if (xrw) headers['X-Requested-With'] = xrw;

  let body = undefined;
  if (['POST', 'PUT', 'PATCH'].includes(req.method)) {
    body = await req.text();
  }

  try {
    const upstream = await fetch(target, { method: req.method, headers, body });
    const text = await upstream.text();
    return new Response(text, {
      status: upstream.status,
      headers: {
        ...cors,
        'Content-Type': upstream.headers.get('Content-Type') || 'application/json',
      }
    });
  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500, headers: { ...cors, 'Content-Type': 'application/json' }
    });
  }
};

export const config = { path: '/.netlify/functions/proxy' };
