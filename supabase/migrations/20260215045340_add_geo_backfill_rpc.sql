-- RPC function for geo backfill on page_views
-- PostgREST requires SELECT access to find rows for UPDATE,
-- but anon has no SELECT policy on page_views. Using SECURITY DEFINER
-- bypasses RLS so the tracker can backfill geo data.

CREATE OR REPLACE FUNCTION public.backfill_page_view_geo(
  pv_id UUID,
  geo_country TEXT DEFAULT NULL,
  geo_city TEXT DEFAULT NULL,
  geo_region TEXT DEFAULT NULL,
  geo_latitude FLOAT8 DEFAULT NULL,
  geo_longitude FLOAT8 DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
  UPDATE public.page_views
  SET country = geo_country,
      city = geo_city,
      region = geo_region,
      latitude = geo_latitude,
      longitude = geo_longitude
  WHERE id = pv_id
    AND country IS NULL;  -- only backfill if not already set
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION public.backfill_page_view_geo(UUID, TEXT, TEXT, TEXT, FLOAT8, FLOAT8) TO anon;

-- RPC function for updating duration + scroll depth
CREATE OR REPLACE FUNCTION public.update_page_view_engagement(
  pv_id UUID,
  dur INTEGER DEFAULT NULL,
  scroll INTEGER DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
  UPDATE public.page_views
  SET duration_seconds = COALESCE(dur, duration_seconds),
      scroll_depth_pct = COALESCE(scroll, scroll_depth_pct)
  WHERE id = pv_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION public.update_page_view_engagement(UUID, INTEGER, INTEGER) TO anon;
