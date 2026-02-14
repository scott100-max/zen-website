// Supabase Edge Function: Tracking Pixel (/functions/v1/t)
// Server-side fallback for ad-blocked or JS-disabled visitors
// Returns 1x1 transparent GIF, inserts into page_views + visitor_logs

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

// 1x1 transparent GIF (43 bytes)
const PIXEL = new Uint8Array([
  0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
  0x80, 0x00, 0x00, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x21,
  0xf9, 0x04, 0x01, 0x00, 0x00, 0x00, 0x00, 0x2c, 0x00, 0x00,
  0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
  0x01, 0x00, 0x3b,
]);

const PIXEL_HEADERS = {
  "Content-Type": "image/gif",
  "Cache-Control": "no-store, no-cache, must-revalidate",
  "Access-Control-Allow-Origin": "https://salus-mind.com",
};

const supabaseUrl = Deno.env.get("SUPABASE_URL") as string;
const supabaseServiceKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") as string;

serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "https://salus-mind.com",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
      },
    });
  }

  const supabase = createClient(supabaseUrl, supabaseServiceKey);

  let pagePath = "/";
  let pageTitle: string | null = null;

  // Try to get page info from POST body (sendBeacon fallback)
  if (req.method === "POST") {
    try {
      const body = await req.json();
      if (body.path) pagePath = body.path;
      if (body.title) pageTitle = body.title;
    } catch {
      // Not JSON — fall through to Referer
    }
  }

  // Fall back to Referer header (noscript pixel)
  if (pagePath === "/" && req.headers.get("referer")) {
    try {
      const refUrl = new URL(req.headers.get("referer")!);
      pagePath = refUrl.pathname;
    } catch {
      // Invalid referer — keep "/"
    }
  }

  const userAgent = req.headers.get("user-agent") || "";

  // Skip bots
  if (/bot|crawl|spider|slurp|facebook|twitter|whatsapp|pingdom|lighthouse|gtmetrix|pagespeed/i.test(userAgent)) {
    return new Response(PIXEL, { headers: PIXEL_HEADERS });
  }

  // Insert page_view with visitor_id=NULL (no client identity available)
  const pageViewPromise = supabase.from("page_views").insert({
    visitor_id: null,
    session_id: null,
    page_path: pagePath,
    page_title: pageTitle,
    referrer: null,
  });

  // Insert visitor_log entry
  const visitorLogPromise = supabase.from("visitor_logs").insert({
    landing_page: pagePath,
    user_agent: userAgent.substring(0, 500),
  });

  // Fire both inserts concurrently, don't block the pixel response
  await Promise.allSettled([pageViewPromise, visitorLogPromise]);

  return new Response(PIXEL, { headers: PIXEL_HEADERS });
});
