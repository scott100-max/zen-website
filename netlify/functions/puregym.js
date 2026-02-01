// Netlify serverless function — proxies PureGym API requests
// Multi-user: accepts email + pin via POST body

const AUTH_URL = "https://auth.puregym.com/connect/token";
const API_BASE = "https://capi.puregym.com/api/v1";
const CLIENT_AUTH = "Basic cm8uY2xpZW50Og=="; // ro.client: (no secret)

const BROWSER_HEADERS = {
  "User-Agent": "PureGym/8.5.0 (iPhone; iOS 17.4; Scale/3.00)",
  "Accept": "application/json, text/plain, */*",
  "Accept-Language": "en-GB,en;q=0.9",
  "Accept-Encoding": "gzip, deflate, br",
  "X-Requested-With": "com.puregym.mobile"
};

async function getToken(email, pin) {
  const res = await fetch(AUTH_URL, {
    method: "POST",
    headers: {
      ...BROWSER_HEADERS,
      "Authorization": CLIENT_AUTH,
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body: `grant_type=password&username=${encodeURIComponent(email)}&password=${encodeURIComponent(pin)}&scope=pgcapi%20offline_access`
  });
  if (!res.ok) {
    const text = await res.text();
    if (res.status === 400) throw new Error("Invalid email or PIN. Please check your PureGym credentials.");
    throw new Error(`Auth failed (${res.status}): ${text.substring(0, 200)}`);
  }
  return res.json();
}

async function apiGet(path, token) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      ...BROWSER_HEADERS,
      "Authorization": `Bearer ${token}`
    }
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${text.substring(0, 200)}`);
  }
  return res.json();
}

export default async (req) => {
  const cors = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Content-Type": "application/json"
  };

  if (req.method === "OPTIONS") {
    return new Response("", { status: 204, headers: cors });
  }

  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "POST required with { email, pin }" }), {
      status: 405, headers: cors
    });
  }

  try {
    const body = await req.json();
    const email = body.email;
    const pin = body.pin;

    if (!email || !pin) {
      return new Response(JSON.stringify({ error: "Email and PIN are required." }), {
        status: 400, headers: cors
      });
    }

    // 1. Authenticate with user's credentials
    const auth = await getToken(email, pin);
    const token = auth.access_token;

    // 2. Fetch member info + activity in parallel
    const [member, activity] = await Promise.all([
      apiGet("/member", token),
      apiGet("/member/activity", token).catch(() => null)
    ]);

    // 3. Try to get home gym attendance
    let attendance = null;
    if (member.homeGymId) {
      attendance = await apiGet(`/gyms/${member.homeGymId}/attendance`, token).catch(() => null);
    }

    return new Response(JSON.stringify({
      member: {
        firstName: member.firstName,
        lastName: member.lastName,
        homeGymId: member.homeGymId,
        homeGymName: member.homeGymName || null
      },
      activity: activity,
      attendance: attendance
    }), { status: 200, headers: cors });

  } catch (err) {
    let msg = err.message || "Unknown error";
    if (msg.includes("<!DOCTYPE") || msg.includes("Cloudflare")) {
      msg = "PureGym servers are currently unavailable. Please try again later.";
    }
    return new Response(JSON.stringify({ error: msg }), {
      status: 500, headers: cors
    });
  }
};

export const config = {
  path: "/api/puregym"
};
