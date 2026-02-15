-- Force-recreate anon UPDATE policies (drop + create)
-- Previous migration's IF NOT EXISTS may have found stale policies

DROP POLICY IF EXISTS "anon_update_page_views" ON public.page_views;
CREATE POLICY "anon_update_page_views"
  ON public.page_views FOR UPDATE TO anon USING (true) WITH CHECK (true);
GRANT UPDATE ON public.page_views TO anon;

DROP POLICY IF EXISTS "anon_update_visitors" ON public.visitors;
CREATE POLICY "anon_update_visitors"
  ON public.visitors FOR UPDATE TO anon USING (true) WITH CHECK (true);
GRANT UPDATE ON public.visitors TO anon;
