"""Fail-closed SEO configuration for local, preview and approved public builds.

Cloudflare supplies CF_PAGES and CF_PAGES_BRANCH during a Pages build. The
explicit opt-in and branch name must be configured for the production build;
setting SITE_URL alone never makes pages indexable.
"""
import os

CANONICAL_ORIGIN = 'https://samuelokotako.com'
SITE_URL = os.environ.get('SITE_URL', CANONICAL_ORIGIN).strip().rstrip('/')
PRODUCTION_BRANCH = os.environ.get('PORTFOLIO_PRODUCTION_BRANCH', '').strip()
INDEXING_REQUESTED = os.environ.get('PORTFOLIO_INDEXING', '').strip().lower() == 'enabled'
INDEXING_ENABLED = all((
    INDEXING_REQUESTED,
    SITE_URL == CANONICAL_ORIGIN,
    os.environ.get('CF_PAGES') == '1',
    PRODUCTION_BRANCH,
    os.environ.get('CF_PAGES_BRANCH') == PRODUCTION_BRANCH,
))
