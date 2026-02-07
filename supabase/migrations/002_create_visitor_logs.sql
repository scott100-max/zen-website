-- =============================================
-- Salus — Visitor Location Tracking
-- Migration: 002_create_visitor_logs
-- =============================================

-- Create visitor_logs table
CREATE TABLE IF NOT EXISTS public.visitor_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  country TEXT,
  city TEXT,
  latitude FLOAT8,
  longitude FLOAT8,
  landing_page TEXT,
  user_agent TEXT,
  session_id UUID
);

-- Index for date-range queries (dashboard filters)
CREATE INDEX idx_visitor_logs_created_at ON public.visitor_logs (created_at DESC);

-- Enable RLS
ALTER TABLE public.visitor_logs ENABLE ROW LEVEL SECURITY;

-- Policy: anonymous visitors can INSERT only (tracking from website)
CREATE POLICY "anon_insert_visitor_logs"
  ON public.visitor_logs
  FOR INSERT
  TO anon
  WITH CHECK (true);

-- Policy: authenticated users can SELECT only (dashboard reads)
CREATE POLICY "authenticated_select_visitor_logs"
  ON public.visitor_logs
  FOR SELECT
  TO authenticated
  USING (true);

-- Grant permissions (schema usage + table access)
GRANT USAGE ON SCHEMA public TO anon;
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT INSERT ON public.visitor_logs TO anon;
GRANT SELECT ON public.visitor_logs TO authenticated;
