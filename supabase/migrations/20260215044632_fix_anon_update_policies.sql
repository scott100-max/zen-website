-- =============================================
-- Fix: Add missing anon UPDATE policies for geo backfill
-- The tracker uses the anon key to PATCH geo data onto page_views,
-- but the UPDATE policy was never applied to the live database.
-- =============================================

-- page_views: allow anon to UPDATE (for geo backfill + duration/scroll)
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'page_views' AND policyname = 'anon_update_page_views'
  ) THEN
    CREATE POLICY "anon_update_page_views"
      ON public.page_views FOR UPDATE TO anon USING (true) WITH CHECK (true);
  END IF;
END $$;

GRANT UPDATE ON public.page_views TO anon;

-- visitors: allow anon to UPDATE (for geo backfill on visitor record)
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies WHERE tablename = 'visitors' AND policyname = 'anon_update_visitors'
  ) THEN
    CREATE POLICY "anon_update_visitors"
      ON public.visitors FOR UPDATE TO anon USING (true) WITH CHECK (true);
  END IF;
END $$;

GRANT UPDATE ON public.visitors TO anon;
