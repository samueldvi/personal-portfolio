# Portfolio V2 integration status

This branch is a working integration, not a release candidate. The existing Python static generator remains the source of public HTML. The starter's standalone `web/` tree and exporter are not copied over the production site: doing so would discard the current translations, case studies, CV approval checks, Formspree behavior, SEO gates and generated-route checks.

## Implemented in this branch

- Writing archives exist in IT/EN/FR, with an honest empty state until real articles are approved. Search is a small, progressive JavaScript enhancement.
- A published article may have one, two or three approved language versions. Detail pages, canonical and hreflang, sitemap entries and RSS items are emitted only for available translations. Language switching falls back to the archive when a translation is missing.
- Article pages show estimated reading time, tags, related articles in the same language, and manual share links in indexable production builds. No automatic social posting exists.
- `fashion-book/` is an independent Cloudflare Pages output candidate. It is absent from the tech site's `public/` tree, navigation and sitemap. It has no real photographs or unverified measurements; its `noindex` header and robots file do not provide access control.
- `editorial/migrations/001_initial.sql` models articles, independent translations, categories, tags, media rights, revisions, social drafts and publication events. Its RLS denies anonymous writes and restricts admin operations to a separately enrolled Supabase Auth user. No account or database has been connected.

## Incomplete, and required before merge or production deployment

- Supabase project setup, migration execution and database-backed tests are unavailable without a project. The SQL has not been executed against Supabase yet. A rollback-only three-role SQL smoke test is prepared in `editorial/tests/rls_smoke.sql`; it is unrun. See `editorial/README.md` for exact setup and access checks.
- An isolated admin client, private media upload path and staging exporter are implemented in `editorial/`. They are not deployed and have not been exercised against a real Supabase project. Live authentication, RLS, storage, revision and publication checks remain mandatory before exposing an admin route.
- The migration configures a private Supabase Storage bucket and RLS for uploads. A rights-approval UI and safe promotion to public media are not implemented; the exporter omits cover images until they exist.
- The Fashion Book needs verified profile details and approved photographs before a public subdomain is configured. Restricted galleries require actual authentication and authorization, not `noindex`.
- Full keyboard and screen-reader review, measured contrast and performance, Supabase connectivity and a real database-backed end-to-end editorial check remain to be completed. The previously recorded local visual and preview HTTP checks are narrower than these gates.

## External configuration when the implementation is ready

1. Create a Supabase project and apply the versioned migration in a private SQL session. Enroll only Samuel's verified Auth user in `editorial_private.admins` after disabling public signup and setting the desired MFA policy. Never put the UUID or credentials in source code.
2. Configure protected environment variables in Cloudflare/CI. The public/publishable key can authorize only RLS-filtered reads; a service-role key must never enter browser JavaScript or a public build artifact.
3. Create a separate Cloudflare Pages project for `fashion-book/` and map `model.samuelokotako.com` only after asset rights and content review. Preserve `_headers` and `robots.txt` in that project. Leave the Data & AI project's build output at `public/`.
4. Review current service pricing and limits before choosing a paid plan. No paid plan is required by the files in this branch; the actual recurring cost depends on Supabase, Cloudflare and media usage after account configuration.

No DNS, Cloudflare, Supabase or production configuration has been changed by this branch. The branch was pushed and a draft pull request opened; Cloudflare automatically created a branch preview from its existing integration.

## Local verification completed

- Production-simulated static build generated 32 pages; `check_site.py` passed for routes, internal links, 404 metadata, canonical/hreflang, sitemap and current content.
- Existing build-mode checks passed for local, preview and main variants, including noindex outside production.
- Public-source safety checks passed after allowing only blank-valued `.env.example` templates.
- Eleven Python tests passed, including a synthetic export → static build → withdrawal cycle that checks RSS, sitemap, SEO metadata, search markup, related links and exclusion of private social drafts. CI now runs the Python suite.
- Chrome headless local QA checked 60 page/viewport combinations at 320, 375, 390, 768, 1024 and 1440 px, plus 30 combinations at 200% root text size (320, 390 and 768 px): no document-level horizontal overflow. Home screenshots at 390 px and 1440 px in light/dark were visually inspected. A 320 px / 200% screenshot exposed an unreadable mobile wordmark; the shared CSS was corrected and inspected again.
- Twenty-six Node tests passed: 19 contact-form tests, five mocked admin-controller scenarios and two writing-search checks. The mocked admin tests exposed a duplicate-tag conflict and late cover validation; both were corrected. These fixtures do not establish live Supabase behavior.
- The branch preview at `https://feature-portfolio-v2.samuel-okotako.pages.dev` passed HTTP checks: Writing returned 200 with `X-Robots-Tag: noindex` and a noindex meta tag; canonical/hreflang were absent; `robots.txt` allowed crawling; sitemap, an unknown route and `/fashion-book/` returned 404. This verifies the served response for those URLs, not all browser interactions.
- Supabase migration, RLS, Auth, Storage and live article operations were **not** run: no project credentials are configured, and the local Docker daemon is unavailable. Full keyboard/screen-reader checks and measured performance were also not completed. These are release gates, not inferred successes.
- Gitleaks history and working-tree scans found no leaks. `check_public_safety.py`, its fixture tests, the build-mode gates and `git diff --check` passed. The current local default build has 32 HTML files, three languages and zero real articles.

## Cost boundary

No paid service was provisioned. The existing Cloudflare Pages integration automatically created a branch preview; the production site remains on `main`. A small editorial project may fit Supabase Free limits, but inactive free projects can pause and production needs should be assessed against current limits. Supabase's documented Pro database baseline is $25/month before extra usage; media/storage, Cloudflare usage, the existing domain and any Formspree tier may add cost depending on real use. Confirm current account plan and limits before enabling the service. References: https://supabase.com/docs/guides/platform/billing-on-supabase and https://supabase.com/kb/faqs/platform/database-only-cost and https://developers.cloudflare.com/pages/platform/limits/.
