-- =============================================
-- Salus — Analytics Tables
-- Migration: 003_create_analytics_tables
-- Tables: visitors, page_views, events
-- =============================================

-- ===== 1. Visitors — one row per unique device/browser =====
CREATE TABLE IF NOT EXISTS public.visitors (
  id UUID PRIMARY KEY,                          -- client-generated, stored in localStorage as salus_vid
  first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  total_sessions INTEGER NOT NULL DEFAULT 1,
  country TEXT,
  city TEXT,
  region TEXT,
  timezone TEXT,
  user_agent TEXT
);

ALTER TABLE public.visitors ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_insert_visitors"
  ON public.visitors FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon_update_visitors"
  ON public.visitors FOR UPDATE TO anon USING (true) WITH CHECK (true);

CREATE POLICY "authenticated_select_visitors"
  ON public.visitors FOR SELECT TO authenticated USING (true);

GRANT INSERT, UPDATE ON public.visitors TO anon;
GRANT SELECT ON public.visitors TO authenticated;

-- ===== 2. Page Views — every page visited =====
CREATE TABLE IF NOT EXISTS public.page_views (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  visitor_id UUID REFERENCES public.visitors(id),
  session_id UUID,
  page_path TEXT,
  page_title TEXT,
  referrer TEXT,
  utm_source TEXT,
  utm_medium TEXT,
  utm_campaign TEXT,
  utm_content TEXT,
  utm_term TEXT,
  country TEXT,
  city TEXT,
  region TEXT,
  latitude FLOAT8,
  longitude FLOAT8,
  duration_seconds INTEGER,
  scroll_depth_pct INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_page_views_created_at ON public.page_views (created_at DESC);
CREATE INDEX idx_page_views_visitor_id ON public.page_views (visitor_id);
CREATE INDEX idx_page_views_session_id ON public.page_views (session_id);
CREATE INDEX idx_page_views_page_path ON public.page_views (page_path);

ALTER TABLE public.page_views ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_insert_page_views"
  ON public.page_views FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "anon_update_page_views"
  ON public.page_views FOR UPDATE TO anon USING (true) WITH CHECK (true);

CREATE POLICY "authenticated_select_page_views"
  ON public.page_views FOR SELECT TO authenticated USING (true);

GRANT INSERT, UPDATE ON public.page_views TO anon;
GRANT SELECT ON public.page_views TO authenticated;

-- ===== 3. Events — discrete interactions =====
CREATE TABLE IF NOT EXISTS public.events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  visitor_id UUID REFERENCES public.visitors(id),
  session_id UUID,
  page_path TEXT,
  event_type TEXT,
  event_target TEXT,
  event_value TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_events_created_at ON public.events (created_at DESC);
CREATE INDEX idx_events_visitor_id ON public.events (visitor_id);
CREATE INDEX idx_events_event_type ON public.events (event_type);
CREATE INDEX idx_events_session_id ON public.events (session_id);

ALTER TABLE public.events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_insert_events"
  ON public.events FOR INSERT TO anon WITH CHECK (true);

CREATE POLICY "authenticated_select_events"
  ON public.events FOR SELECT TO authenticated USING (true);

GRANT INSERT ON public.events TO anon;
GRANT SELECT ON public.events TO authenticated;

-- ===== 4. RPC: increment visitor session count =====
CREATE OR REPLACE FUNCTION public.increment_visitor_session(vid UUID)
RETURNS VOID AS $$
BEGIN
  UPDATE public.visitors
  SET last_seen = NOW(),
      total_sessions = total_sessions + 1
  WHERE id = vid;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION public.increment_visitor_session(UUID) TO anon;
