"""Synthetic editorial export → static build tests; these do not exercise Supabase."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

from editorial.export_public import stage


SOURCE = Path(__file__).resolve().parents[1]
BUILD_ENV = {
    **os.environ,
    'SITE_URL': 'https://samuelokotako.com',
    'CF_PAGES': '1',
    'CF_PAGES_BRANCH': 'main',
    'PYTHONDONTWRITEBYTECODE': '1',
}


def row(slug, language, status='published', published_at='2026-01-01T12:00:00Z'):
    return {
        'language': language,
        'title': f'{slug} in {language}',
        'summary': f'A documented {slug} example.',
        'body_markdown': '# Approach\nWe inspect input data and record quality checks.',
        'seo_title': f'{slug} case note',
        'seo_description': f'Publication notes for {slug}.',
        'status': status,
        'published_at': published_at,
        'editorial_articles': {
            'slug': slug,
            'editorial_categories': {'label': 'Data Engineering'},
            'editorial_article_tags': [{'editorial_tags': {'label': 'Quality'}}],
        },
    }


class EditorialPublicationTests(unittest.TestCase):
    def test_publish_english_only_then_withdraw_from_static_output(self):
        with tempfile.TemporaryDirectory(prefix='editorial-publication-') as folder:
            root = Path(folder)
            site = root / 'site'
            shutil.copytree(SOURCE, site, ignore=shutil.ignore_patterns('.git', 'public', '__pycache__', '*.pyc'))
            rows = [
                row('reliable-pipelines', 'en'),
                row('quality-checks', 'en'),
                row('reliable-pipelines', 'it', status='draft'),
                row('reliable-pipelines', 'fr', published_at='2099-01-01T12:00:00Z'),
            ]
            rows[0]['editorial_social_drafts'] = [{'platform': 'linkedin', 'copy': 'UNPUBLISHED_LINKEDIN_DRAFT'}]
            rows[0]['cover_media_id'] = 'private-cover-fixture'

            def publish_fixture(data, stage_name):
                staged = root / stage_name
                stage(data, staged)
                shutil.copy2(staged / 'articles.json', site / 'content/articles.json')
                shutil.copytree(staged / 'articles', site / 'content/articles', dirs_exist_ok=True)
                for script in ('build_pages.py', 'check_site.py'):
                    subprocess.run(['python3', '-B', script], cwd=site, env=BUILD_ENV,
                                   check=True, capture_output=True, text=True)
                return site / 'public'

            public = publish_fixture(rows, 'first-export')
            page = (public / 'en/writing/reliable-pipelines/index.html').read_text()
            archive = (public / 'en/writing/index.html').read_text()
            sitemap = (public / 'sitemap.xml').read_text()
            feed = ET.parse(public / 'en/writing/feed.xml')
            self.assertIn('<link rel="canonical" href="https://samuelokotako.com/en/writing/reliable-pipelines/">', page)
            self.assertIn('hreflang="en"', page)
            self.assertNotIn('<link rel="alternate" hreflang="it"', page)
            self.assertIn('application/ld+json', page)
            self.assertIn('"datePublished": "2026-01-01"', page)
            self.assertIn('og:type" content="article"', page)
            self.assertIn('property="og:title" content="reliable-pipelines case note"', page)
            self.assertIn('name="twitter:card" content="summary_large_image"', page)
            self.assertIn('reliable-pipelines case note', page)
            self.assertIn('article-related', page)
            self.assertIn('href="/en/writing/quality-checks/"', page)
            self.assertIn('datetime="2026-01-01"', page)
            self.assertIn('Data Engineering · Quality', page)
            self.assertIn('linkedin.com/sharing/share-offsite/', page)
            self.assertIn('writing-search.js', archive)
            self.assertIn('data-article-card', archive)
            self.assertIn('min read', page)
            self.assertNotIn('UNPUBLISHED_LINKEDIN_DRAFT', page)
            registry = (site / 'content/articles.json').read_text()
            self.assertNotIn('UNPUBLISHED_LINKEDIN_DRAFT', registry)
            self.assertNotIn('private-cover-fixture', registry)
            self.assertEqual(len(feed.findall('.//item')), 2)
            self.assertIn('/en/writing/reliable-pipelines/', sitemap)
            self.assertFalse((public / 'it/writing/reliable-pipelines').exists())
            self.assertFalse((public / 'fr/writing/reliable-pipelines').exists())

            withdrawn = [{**rows[0], 'status': 'withdrawn'}, *rows[1:]]
            public = publish_fixture(withdrawn, 'second-export')
            sitemap = (public / 'sitemap.xml').read_text()
            feed = ET.parse(public / 'en/writing/feed.xml')
            self.assertFalse((public / 'en/writing/reliable-pipelines').exists())
            self.assertNotIn('/en/writing/reliable-pipelines/', sitemap)
            self.assertEqual(len(feed.findall('.//item')), 1)
            self.assertTrue((public / 'en/writing/quality-checks/index.html').exists())

    def test_duplicate_published_locale_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix='editorial-duplicate-') as folder:
            with self.assertRaisesRegex(ValueError, 'Duplicate published translation'):
                stage([row('same-slug', 'en'), row('same-slug', 'en')], Path(folder) / 'stage')


if __name__ == '__main__':
    unittest.main()
