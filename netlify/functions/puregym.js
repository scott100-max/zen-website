// Netlify serverless function — proxies PureGym API requests
// Authenticates with PureGym, fetches member + activity data, returns JSON

const AUTH_URL = "https://auth.puregym.com/connect/token";
const API_BASE = "https://capi.puregym.com/api/v1";
const CLIENT_AUTH = "Basic cm8uY2xpZW50Og=="; // ro.client: (no secret)

// Credentials — move to Netlify environment variables for production
const PG_EMAIL = process.env.PUREGYM_EMAIL || "Ella.ripley@icloud.com";
const PG_PIN = process.env.PUREGYM_PIN || "97966079";

async function getToken() {
  const res = await fetch(AUTH_URL, {
    method: "POST",
    headers: {
      "Authorization": CLIENT_AUTH,
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body: `grant_type=password&username=${encodeURIComponent(PG_EMAIL)}&password=${encodeURIComponent(PG_PIN)}&scope=pgcapi%20offline_access`
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Auth failed (${res.status}): ${text}`);
  }
  return res.json();
}

async function apiGet(path, token) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Authorization": `Bearer ${token}` }
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${path} failed (${res.status}): ${text}`);
  }
  return res.json();
}

export default async (req) => {
  const cors = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Content-Type": "application/json"
  };

  if (req.method === "OPTIONS") {
    return new Response("", { status: 204, headers: cors });
  }

  try {
    // 1. Authenticate
    const auth = await getToken();
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
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: cors
    });
  }
};

export const config = {
  path: "/api/puregym"
};
