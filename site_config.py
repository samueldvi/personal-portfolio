"""SEO settings for the approved public release.

Only a Cloudflare Pages build of main may produce indexable HTML. Local builds
and builds from every other branch remain noindex, even with SITE_URL set.
"""
import os

CANONICAL_ORIGIN = 'https://samuelokotako.com'
SITE_URL = (os.environ.get('SITE_URL') or CANONICAL_ORIGIN).strip().rstrip('/')
PUBLISHED_BRANCH = 'main'
INDEXING_ENABLED = all((
    SITE_URL == CANONICAL_ORIGIN,
    os.environ.get('CF_PAGES') == '1',
    os.environ.get('CF_PAGES_BRANCH') == PUBLISHED_BRANCH,
))
