-- Run only against an isolated Supabase test project after 001_initial.sql.
-- psql -X -v ON_ERROR_STOP=1 -v admin_uuid='<verified-enrolled-auth-user-uuid>' \
--      -f editorial/tests/rls_smoke.sql "$TEST_DATABASE_URL"
-- All synthetic rows are rolled back. This tests SQL/RLS role simulation, not
-- Supabase Auth token verification or Storage HTTP upload/download behavior.
\set ON_ERROR_STOP on
BEGIN;

SELECT set_config('qa.admin_uuid', :'admin_uuid', true);
SELECT set_config('qa.nonadmin_uuid', gen_random_uuid()::text, true);
SELECT set_config('qa.article_id', gen_random_uuid()::text, true);
SELECT set_config('qa.draft_article_id', gen_random_uuid()::text, true);
SELECT set_config('qa.published_translation_id', gen_random_uuid()::text, true);
SELECT set_config('qa.draft_translation_id', gen_random_uuid()::text, true);
SELECT set_config('qa.media_id', gen_random_uuid()::text, true);
SELECT set_config('qa.slug', 'qa-rls-' || replace(gen_random_uuid()::text, '-', ''), true);

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM editorial_private.admins
                 WHERE user_id = current_setting('qa.admin_uuid')::uuid) THEN
    RAISE EXCEPTION 'The supplied Auth user must be enrolled as an editorial administrator';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM storage.buckets
                 WHERE id = 'editorial-private' AND public = false) THEN
    RAISE EXCEPTION 'The editorial-private bucket must exist and remain private';
  END IF;
END $$;

SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claim.sub', current_setting('qa.admin_uuid'), true);
DO $$ BEGIN
  IF NOT public.editorial_can_manage() THEN
    RAISE EXCEPTION 'The enrolled administrator cannot manage editorial data';
  END IF;
END $$;

INSERT INTO public.editorial_categories(slug, label)
VALUES (current_setting('qa.slug') || '-category', 'Synthetic QA category');
INSERT INTO public.editorial_tags(slug, label)
VALUES (current_setting('qa.slug') || '-tag', 'Synthetic QA tag');
INSERT INTO public.editorial_articles(id, slug, category_id)
SELECT current_setting('qa.article_id')::uuid, current_setting('qa.slug'), c.id
FROM public.editorial_categories c WHERE c.slug = current_setting('qa.slug') || '-category';
INSERT INTO public.editorial_articles(id, slug)
VALUES (current_setting('qa.draft_article_id')::uuid, current_setting('qa.slug') || '-draft');
INSERT INTO public.editorial_article_tags(article_id, tag_id)
SELECT current_setting('qa.article_id')::uuid, t.id
FROM public.editorial_tags t WHERE t.slug = current_setting('qa.slug') || '-tag';
INSERT INTO public.editorial_translations
  (id, article_id, language, title, summary, body_markdown, status, published_at)
VALUES
  (current_setting('qa.published_translation_id')::uuid,
   current_setting('qa.article_id')::uuid, 'en', 'Synthetic public article',
   'Synthetic summary', 'Synthetic body', 'published', now()),
  (current_setting('qa.draft_translation_id')::uuid,
   current_setting('qa.article_id')::uuid, 'it', 'Synthetic draft article',
   'Draft summary', 'Draft body', 'draft', NULL);
INSERT INTO public.editorial_translations
  (article_id, language, title, summary, body_markdown, status)
VALUES (current_setting('qa.draft_article_id')::uuid, 'en',
        'Synthetic draft-only article', 'Draft summary', 'Draft body', 'draft');
INSERT INTO public.editorial_revisions
  (translation_id, revision_number, snapshot, editor_id)
VALUES (current_setting('qa.draft_translation_id')::uuid, 1,
        '{"synthetic":true}'::jsonb, current_setting('qa.admin_uuid')::uuid);
INSERT INTO public.editorial_social_drafts(translation_id, platform, copy)
VALUES (current_setting('qa.draft_translation_id')::uuid, 'linkedin', 'Synthetic post draft');
INSERT INTO public.editorial_media(id, storage_key, mime_type, width, height)
VALUES (current_setting('qa.media_id')::uuid,
        current_setting('qa.slug') || '.webp', 'image/webp', 800, 600);

DO $$ BEGIN
  IF (SELECT count(*) FROM public.editorial_revisions
      WHERE translation_id = current_setting('qa.draft_translation_id')::uuid) <> 1 THEN
    RAISE EXCEPTION 'The administrator cannot read revision history';
  END IF;
  IF (SELECT count(*) FROM public.editorial_publication_events
      WHERE translation_id = current_setting('qa.published_translation_id')::uuid
        AND action = 'publish') <> 1 THEN
    RAISE EXCEPTION 'Publication history did not record the initial publish';
  END IF;
END $$;

SET LOCAL ROLE anon;
SELECT set_config('request.jwt.claim.sub', '', true);
DO $$
DECLARE denied boolean;
BEGIN
  IF (SELECT count(*) FROM public.editorial_translations
      WHERE article_id IN (current_setting('qa.article_id')::uuid,
                           current_setting('qa.draft_article_id')::uuid)) <> 1 THEN
    RAISE EXCEPTION 'Anon must see only the published English translation';
  END IF;
  IF (SELECT count(*) FROM public.editorial_articles
      WHERE id IN (current_setting('qa.article_id')::uuid,
                   current_setting('qa.draft_article_id')::uuid)) <> 1 THEN
    RAISE EXCEPTION 'Anon can see a draft-only article or cannot see a published article';
  END IF;
  IF (SELECT count(*) FROM public.editorial_categories
      WHERE slug = current_setting('qa.slug') || '-category') <> 1 THEN
    RAISE EXCEPTION 'Anon cannot see the published article category';
  END IF;
  IF (SELECT count(*) FROM public.editorial_tags
      WHERE slug = current_setting('qa.slug') || '-tag') <> 1 THEN
    RAISE EXCEPTION 'Anon cannot see the published article tag';
  END IF;
  IF (SELECT count(*) FROM public.editorial_media
      WHERE id = current_setting('qa.media_id')::uuid) <> 0 THEN
    RAISE EXCEPTION 'Anon can read private media metadata';
  END IF;
  denied := false;
  BEGIN
    INSERT INTO public.editorial_articles(slug)
    VALUES (current_setting('qa.slug') || '-anon-write');
  EXCEPTION WHEN insufficient_privilege THEN denied := true;
  END;
  IF NOT denied THEN RAISE EXCEPTION 'Anon inserted an article'; END IF;
  denied := false;
  BEGIN
    PERFORM public.editorial_can_manage();
  EXCEPTION WHEN insufficient_privilege THEN denied := true;
  END;
  IF NOT denied THEN RAISE EXCEPTION 'Anon can execute the admin check RPC'; END IF;
  denied := false;
  BEGIN
    PERFORM 1 FROM editorial_private.admins;
  EXCEPTION WHEN insufficient_privilege THEN denied := true;
  END;
  IF NOT denied THEN RAISE EXCEPTION 'Anon can inspect administrator enrollment'; END IF;
  denied := false;
  BEGIN
    PERFORM 1 FROM public.editorial_revisions
    WHERE translation_id = current_setting('qa.draft_translation_id')::uuid;
  EXCEPTION WHEN insufficient_privilege THEN denied := true;
  END;
  IF NOT denied THEN RAISE EXCEPTION 'Anon can query private revisions'; END IF;
END $$;

SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claim.sub', current_setting('qa.nonadmin_uuid'), true);
DO $$
DECLARE changed integer; denied boolean := false;
BEGIN
  IF public.editorial_can_manage() THEN
    RAISE EXCEPTION 'An unenrolled user passed the admin check';
  END IF;
  IF (SELECT count(*) FROM public.editorial_translations
      WHERE id = current_setting('qa.draft_translation_id')::uuid) <> 0 THEN
    RAISE EXCEPTION 'Non-admin can read a private draft';
  END IF;
  IF (SELECT count(*) FROM public.editorial_revisions
      WHERE translation_id = current_setting('qa.draft_translation_id')::uuid) <> 0 THEN
    RAISE EXCEPTION 'Non-admin can read private revisions';
  END IF;
  IF (SELECT count(*) FROM public.editorial_social_drafts
      WHERE translation_id = current_setting('qa.draft_translation_id')::uuid) <> 0 THEN
    RAISE EXCEPTION 'Non-admin can read social drafts';
  END IF;
  IF (SELECT count(*) FROM public.editorial_media
      WHERE id = current_setting('qa.media_id')::uuid) <> 0 THEN
    RAISE EXCEPTION 'Non-admin can read private media metadata';
  END IF;
  BEGIN
    INSERT INTO public.editorial_articles(slug)
    VALUES (current_setting('qa.slug') || '-nonadmin-write');
  EXCEPTION WHEN insufficient_privilege THEN denied := true;
  END;
  IF NOT denied THEN RAISE EXCEPTION 'Non-admin inserted an article'; END IF;
  UPDATE public.editorial_translations SET title = 'Unauthorized edit'
  WHERE id = current_setting('qa.draft_translation_id')::uuid;
  GET DIAGNOSTICS changed = ROW_COUNT;
  IF changed <> 0 THEN RAISE EXCEPTION 'Non-admin edited a draft'; END IF;
  UPDATE public.editorial_translations SET status = 'withdrawn'
  WHERE id = current_setting('qa.published_translation_id')::uuid;
  GET DIAGNOSTICS changed = ROW_COUNT;
  IF changed <> 0 THEN RAISE EXCEPTION 'Non-admin withdrew a publication'; END IF;
END $$;

SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claim.sub', current_setting('qa.admin_uuid'), true);
DO $$
DECLARE denied boolean;
BEGIN
  denied := false;
  BEGIN
    UPDATE public.editorial_translations SET body_markdown = 'Changed while public'
    WHERE id = current_setting('qa.published_translation_id')::uuid;
  EXCEPTION WHEN raise_exception THEN denied := true;
  END;
  IF NOT denied THEN RAISE EXCEPTION 'Published text changed without withdrawal'; END IF;
  denied := false;
  BEGIN
    UPDATE public.editorial_translations SET published_at = now() - interval '1 day'
    WHERE id = current_setting('qa.published_translation_id')::uuid;
  EXCEPTION WHEN raise_exception THEN denied := true;
  END;
  IF NOT denied THEN RAISE EXCEPTION 'Published date changed without event'; END IF;
  denied := false;
  BEGIN
    UPDATE public.editorial_articles SET category_id = NULL
    WHERE id = current_setting('qa.article_id')::uuid;
  EXCEPTION WHEN raise_exception THEN denied := true;
  END;
  IF NOT denied THEN RAISE EXCEPTION 'Shared category changed while a language was public'; END IF;
  denied := false;
  BEGIN
    UPDATE public.editorial_media SET rights_status = 'approved'
    WHERE id = current_setting('qa.media_id')::uuid;
  EXCEPTION WHEN check_violation THEN denied := true;
  END;
  IF NOT denied THEN RAISE EXCEPTION 'Media rights approved without basis or credit'; END IF;
  UPDATE public.editorial_translations
  SET cover_media_id = current_setting('qa.media_id')::uuid
  WHERE id = current_setting('qa.draft_translation_id')::uuid;
  denied := false;
  BEGIN
    UPDATE public.editorial_translations SET status = 'published', published_at = now()
    WHERE id = current_setting('qa.draft_translation_id')::uuid;
  EXCEPTION WHEN raise_exception THEN denied := true;
  END;
  IF NOT denied THEN RAISE EXCEPTION 'Pending private cover allowed publication'; END IF;
END $$;

UPDATE public.editorial_media
SET rights_status = 'approved', rights_basis = 'Synthetic QA permission',
    credit = 'Synthetic QA', alt_text = '{"it":"Grafico sintetico"}'::jsonb
WHERE id = current_setting('qa.media_id')::uuid;
UPDATE public.editorial_translations SET status = 'published', published_at = now()
WHERE id = current_setting('qa.draft_translation_id')::uuid;
SET LOCAL ROLE anon;
SELECT set_config('request.jwt.claim.sub', '', true);
DO $$ BEGIN
  IF (SELECT count(*) FROM public.editorial_translations
      WHERE article_id = current_setting('qa.article_id')::uuid) <> 2 THEN
    RAISE EXCEPTION 'Independent Italian publication was not visible alongside English';
  END IF;
  IF (SELECT count(*) FROM public.editorial_media
      WHERE id = current_setting('qa.media_id')::uuid) <> 0 THEN
    RAISE EXCEPTION 'Approved cover metadata leaked while object remained private';
  END IF;
END $$;

SET LOCAL ROLE authenticated;
SELECT set_config('request.jwt.claim.sub', current_setting('qa.admin_uuid'), true);
UPDATE public.editorial_translations SET status = 'withdrawn'
WHERE id IN (current_setting('qa.published_translation_id')::uuid,
             current_setting('qa.draft_translation_id')::uuid);
DO $$ BEGIN
  IF (SELECT count(*) FROM public.editorial_publication_events
      WHERE translation_id IN (current_setting('qa.published_translation_id')::uuid,
                               current_setting('qa.draft_translation_id')::uuid)) <> 4 THEN
    RAISE EXCEPTION 'Publication history lacks publish/withdraw events';
  END IF;
END $$;
SET LOCAL ROLE anon;
SELECT set_config('request.jwt.claim.sub', '', true);
DO $$ BEGIN
  IF (SELECT count(*) FROM public.editorial_articles
      WHERE id = current_setting('qa.article_id')::uuid) <> 0 THEN
    RAISE EXCEPTION 'Withdrawn article is still visible to anon';
  END IF;
END $$;

ROLLBACK;
\echo 'PASS: synthetic SQL/RLS role smoke checks (transaction rolled back)'
