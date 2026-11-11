-- Supabase/PostgreSQL 15+ editorial model. Apply in a dedicated project before use.
-- No administrator is created by this migration; access fails closed until enrolled manually.
BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS editorial_private;
CREATE TABLE editorial_private.admins (
  user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now()
);
REVOKE ALL ON SCHEMA editorial_private FROM PUBLIC, anon, authenticated;
REVOKE ALL ON ALL TABLES IN SCHEMA editorial_private FROM PUBLIC, anon, authenticated;
CREATE FUNCTION editorial_private.is_admin() RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = ''
AS $$ SELECT EXISTS (SELECT 1 FROM editorial_private.admins WHERE user_id = auth.uid()) $$;
REVOKE ALL ON FUNCTION editorial_private.is_admin() FROM PUBLIC;
GRANT USAGE ON SCHEMA editorial_private TO authenticated;
GRANT EXECUTE ON FUNCTION editorial_private.is_admin() TO authenticated;
CREATE FUNCTION public.editorial_can_manage() RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = ''
AS $$ SELECT editorial_private.is_admin() $$;
REVOKE ALL ON FUNCTION public.editorial_can_manage() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.editorial_can_manage() TO authenticated;

CREATE TABLE public.editorial_categories (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  label text NOT NULL CHECK (char_length(label) BETWEEN 1 AND 100),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE public.editorial_tags (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  label text NOT NULL CHECK (char_length(label) BETWEEN 1 AND 100)
);
CREATE TABLE public.editorial_articles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  category_id uuid REFERENCES public.editorial_categories(id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE public.editorial_translations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  article_id uuid NOT NULL REFERENCES public.editorial_articles(id) ON DELETE RESTRICT,
  language text NOT NULL CHECK (language IN ('it','en','fr')),
  title text NOT NULL CHECK (char_length(title) BETWEEN 1 AND 200),
  summary text NOT NULL DEFAULT '',
  body_markdown text NOT NULL DEFAULT '',
  seo_title text,
  seo_description text,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','review','scheduled','published','withdrawn')),
  published_at timestamptz,
  scheduled_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (article_id, language),
  CHECK (status <> 'published' OR published_at IS NOT NULL),
  CHECK (status <> 'scheduled' OR scheduled_at IS NOT NULL)
);
CREATE INDEX editorial_public_translations_idx ON public.editorial_translations(language, published_at DESC)
  WHERE status = 'published';
CREATE TABLE public.editorial_article_tags (
  article_id uuid NOT NULL REFERENCES public.editorial_articles(id) ON DELETE RESTRICT,
  tag_id uuid NOT NULL REFERENCES public.editorial_tags(id) ON DELETE RESTRICT,
  PRIMARY KEY (article_id, tag_id)
);
CREATE TABLE public.editorial_media (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  storage_key text NOT NULL UNIQUE CHECK (storage_key !~ '(^/|(^|/)\.\.(/|$))'),
  mime_type text NOT NULL CHECK (mime_type IN ('image/jpeg','image/png','image/webp','image/avif')),
  width integer NOT NULL CHECK (width > 0),
  height integer NOT NULL CHECK (height > 0),
  alt_text jsonb NOT NULL DEFAULT '{}'::jsonb,
  credit text NOT NULL DEFAULT '',
  rights_basis text NOT NULL DEFAULT '',
  rights_status text NOT NULL DEFAULT 'pending' CHECK (rights_status IN ('pending','approved','rejected')),
  visibility text NOT NULL DEFAULT 'private' CHECK (visibility IN ('private','public')),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK (visibility <> 'public' OR (rights_status = 'approved' AND credit <> '' AND rights_basis <> ''))
);
ALTER TABLE public.editorial_translations
  ADD COLUMN cover_media_id uuid REFERENCES public.editorial_media(id) ON DELETE RESTRICT;
CREATE TABLE public.editorial_revisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  translation_id uuid NOT NULL REFERENCES public.editorial_translations(id) ON DELETE RESTRICT,
  revision_number integer NOT NULL CHECK (revision_number > 0),
  snapshot jsonb NOT NULL,
  editor_id uuid NOT NULL REFERENCES auth.users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (translation_id, revision_number)
);
CREATE TABLE public.editorial_social_drafts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  translation_id uuid NOT NULL REFERENCES public.editorial_translations(id) ON DELETE RESTRICT,
  platform text NOT NULL CHECK (platform IN ('linkedin','instagram','other')),
  copy text NOT NULL DEFAULT '',
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','approved','used')),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (translation_id, platform)
);
CREATE TABLE public.editorial_publication_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  translation_id uuid NOT NULL REFERENCES public.editorial_translations(id) ON DELETE RESTRICT,
  action text NOT NULL CHECK (action IN ('publish','withdraw')),
  actor_id uuid NOT NULL REFERENCES auth.users(id),
  occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE FUNCTION editorial_private.guard_translation() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  IF TG_OP = 'UPDATE' AND OLD.status = 'published' THEN
    IF NEW.status NOT IN ('published', 'withdrawn')
       OR (to_jsonb(NEW) - 'updated_at' - 'status')
         <> (to_jsonb(OLD) - 'updated_at' - 'status') THEN
      RAISE EXCEPTION 'Withdraw a published translation before editing its content or publication date';
    END IF;
  END IF;
  IF NEW.status = 'published' THEN
    IF NEW.published_at > now() THEN
      RAISE EXCEPTION 'Use scheduled status for a future publication date';
    END IF;
    IF btrim(NEW.summary) = '' OR btrim(NEW.body_markdown) = '' THEN
      RAISE EXCEPTION 'Published translations need a summary and body';
    END IF;
    IF NEW.cover_media_id IS NOT NULL AND NOT EXISTS (
      SELECT 1 FROM public.editorial_media m
      WHERE m.id = NEW.cover_media_id AND m.rights_status = 'approved'
    ) THEN
      RAISE EXCEPTION 'Cover media rights must be approved before publication';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER editorial_translation_guard BEFORE INSERT OR UPDATE ON public.editorial_translations
  FOR EACH ROW EXECUTE FUNCTION editorial_private.guard_translation();
CREATE FUNCTION editorial_private.record_publication() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE event_action text;
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.status = 'published' THEN event_action := 'publish'; END IF;
  ELSE
    IF NEW.status = 'published' AND OLD.status <> 'published' THEN
      event_action := 'publish';
    ELSIF OLD.status = 'published' AND NEW.status <> 'published' THEN
      event_action := 'withdraw';
    END IF;
  END IF;
  IF event_action IS NOT NULL THEN
    INSERT INTO public.editorial_publication_events(translation_id, action, actor_id)
    VALUES (NEW.id, event_action, auth.uid());
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER editorial_publication_history AFTER INSERT OR UPDATE OF status ON public.editorial_translations
  FOR EACH ROW EXECUTE FUNCTION editorial_private.record_publication();

-- Category, slug and tags are shared by every language. Keep them stable while
-- at least one translation is published, including during edits to another draft.
CREATE FUNCTION editorial_private.guard_shared_article() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
BEGIN
  IF (NEW.slug IS DISTINCT FROM OLD.slug OR NEW.category_id IS DISTINCT FROM OLD.category_id)
     AND EXISTS (SELECT 1 FROM public.editorial_translations t
                 WHERE t.article_id = OLD.id AND t.status = 'published') THEN
    RAISE EXCEPTION 'Withdraw all published translations before changing shared article metadata';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER editorial_shared_article_guard BEFORE UPDATE ON public.editorial_articles
  FOR EACH ROW EXECUTE FUNCTION editorial_private.guard_shared_article();
CREATE FUNCTION editorial_private.guard_article_tags() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = '' AS $$
DECLARE target_article uuid;
BEGIN
  IF TG_OP = 'DELETE' THEN
    target_article := OLD.article_id;
  ELSE
    target_article := NEW.article_id;
  END IF;
  IF TG_OP = 'UPDATE' THEN
    IF OLD.article_id IS DISTINCT FROM NEW.article_id THEN
      IF EXISTS (SELECT 1 FROM public.editorial_translations t
                 WHERE t.article_id = OLD.article_id AND t.status = 'published') THEN
        RAISE EXCEPTION 'Withdraw all published translations before changing shared tags';
      END IF;
    END IF;
  END IF;
  IF EXISTS (SELECT 1 FROM public.editorial_translations t
             WHERE t.article_id = target_article AND t.status = 'published') THEN
    RAISE EXCEPTION 'Withdraw all published translations before changing shared tags';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER editorial_article_tags_guard BEFORE INSERT OR UPDATE OR DELETE ON public.editorial_article_tags
  FOR EACH ROW EXECUTE FUNCTION editorial_private.guard_article_tags();

CREATE FUNCTION editorial_private.touch_updated_at() RETURNS trigger
LANGUAGE plpgsql SET search_path = '' AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END $$;
CREATE TRIGGER editorial_articles_updated BEFORE UPDATE ON public.editorial_articles
  FOR EACH ROW EXECUTE FUNCTION editorial_private.touch_updated_at();
CREATE TRIGGER editorial_translations_updated BEFORE UPDATE ON public.editorial_translations
  FOR EACH ROW EXECUTE FUNCTION editorial_private.touch_updated_at();
CREATE TRIGGER editorial_social_updated BEFORE UPDATE ON public.editorial_social_drafts
  FOR EACH ROW EXECUTE FUNCTION editorial_private.touch_updated_at();

ALTER TABLE public.editorial_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.editorial_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.editorial_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.editorial_translations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.editorial_article_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.editorial_media ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.editorial_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.editorial_social_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.editorial_publication_events ENABLE ROW LEVEL SECURITY;

-- Anonymous reads are restricted to rows connected to a currently published translation.
CREATE POLICY editorial_public_translations ON public.editorial_translations FOR SELECT TO anon
  USING (status = 'published' AND published_at <= now());
CREATE POLICY editorial_public_articles ON public.editorial_articles FOR SELECT TO anon
  USING (EXISTS (SELECT 1 FROM public.editorial_translations t WHERE t.article_id = editorial_articles.id AND t.status = 'published' AND t.published_at <= now()));
CREATE POLICY editorial_public_categories ON public.editorial_categories FOR SELECT TO anon
  USING (EXISTS (SELECT 1 FROM public.editorial_articles a WHERE a.category_id = editorial_categories.id));
CREATE POLICY editorial_public_tags ON public.editorial_tags FOR SELECT TO anon
  USING (EXISTS (SELECT 1 FROM public.editorial_article_tags at WHERE at.tag_id = editorial_tags.id));
CREATE POLICY editorial_public_article_tags ON public.editorial_article_tags FOR SELECT TO anon
  USING (EXISTS (SELECT 1 FROM public.editorial_articles a WHERE a.id = editorial_article_tags.article_id));
CREATE POLICY editorial_public_media ON public.editorial_media FOR SELECT TO anon
  USING (visibility = 'public' AND rights_status = 'approved');

-- One enrolled Supabase Auth user may manage content; the public cannot write.
CREATE POLICY editorial_admin_categories ON public.editorial_categories FOR ALL TO authenticated USING (editorial_private.is_admin()) WITH CHECK (editorial_private.is_admin());
CREATE POLICY editorial_admin_tags ON public.editorial_tags FOR ALL TO authenticated USING (editorial_private.is_admin()) WITH CHECK (editorial_private.is_admin());
CREATE POLICY editorial_admin_articles ON public.editorial_articles FOR ALL TO authenticated USING (editorial_private.is_admin()) WITH CHECK (editorial_private.is_admin());
CREATE POLICY editorial_admin_translations ON public.editorial_translations FOR ALL TO authenticated USING (editorial_private.is_admin()) WITH CHECK (editorial_private.is_admin());
CREATE POLICY editorial_admin_article_tags ON public.editorial_article_tags FOR ALL TO authenticated USING (editorial_private.is_admin()) WITH CHECK (editorial_private.is_admin());
CREATE POLICY editorial_admin_media ON public.editorial_media FOR ALL TO authenticated USING (editorial_private.is_admin()) WITH CHECK (editorial_private.is_admin());
CREATE POLICY editorial_admin_revisions_read ON public.editorial_revisions FOR SELECT TO authenticated USING (editorial_private.is_admin());
CREATE POLICY editorial_admin_revisions_insert ON public.editorial_revisions FOR INSERT TO authenticated WITH CHECK (editorial_private.is_admin());
CREATE POLICY editorial_admin_social ON public.editorial_social_drafts FOR ALL TO authenticated USING (editorial_private.is_admin()) WITH CHECK (editorial_private.is_admin());
CREATE POLICY editorial_admin_events_read ON public.editorial_publication_events FOR SELECT TO authenticated USING (editorial_private.is_admin());

REVOKE ALL ON public.editorial_categories, public.editorial_tags, public.editorial_articles,
  public.editorial_translations, public.editorial_article_tags, public.editorial_media,
  public.editorial_revisions, public.editorial_social_drafts,
  public.editorial_publication_events FROM PUBLIC, anon, authenticated;
GRANT SELECT ON public.editorial_categories, public.editorial_tags, public.editorial_articles,
  public.editorial_translations, public.editorial_article_tags, public.editorial_media TO anon;
GRANT SELECT, INSERT ON public.editorial_categories, public.editorial_tags TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.editorial_articles, public.editorial_translations,
  public.editorial_media, public.editorial_social_drafts TO authenticated;
GRANT SELECT, INSERT, DELETE ON public.editorial_article_tags TO authenticated;
GRANT SELECT, INSERT ON public.editorial_revisions TO authenticated;
GRANT SELECT ON public.editorial_publication_events TO authenticated;

-- Uploads start in a private bucket. Publishing an approved image needs a separate,
-- reviewed promotion step; a public metadata row does not expose the private object.
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('editorial-private', 'editorial-private', false, 5242880,
        ARRAY['image/jpeg','image/png','image/webp','image/avif'])
ON CONFLICT (id) DO NOTHING;
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM storage.buckets WHERE id = 'editorial-private' AND public) THEN
    RAISE EXCEPTION 'editorial-private bucket must not be public';
  END IF;
END $$;
CREATE POLICY editorial_private_media_read ON storage.objects FOR SELECT TO authenticated
  USING (bucket_id = 'editorial-private' AND editorial_private.is_admin());
CREATE POLICY editorial_private_media_insert ON storage.objects FOR INSERT TO authenticated
  WITH CHECK (bucket_id = 'editorial-private' AND editorial_private.is_admin());
CREATE POLICY editorial_private_media_update ON storage.objects FOR UPDATE TO authenticated
  USING (bucket_id = 'editorial-private' AND editorial_private.is_admin())
  WITH CHECK (bucket_id = 'editorial-private' AND editorial_private.is_admin());
COMMIT;
