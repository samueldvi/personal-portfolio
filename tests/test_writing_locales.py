"""Exercise an English-only article without modifying editorial source data."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch
import build_pages

SOURCE = Path(__file__).resolve().parents[1]

class WritingLocaleTests(unittest.TestCase):
    def test_article_cover_uses_its_localized_share_alt(self):
        article = {
            'slug': 'example', 'date': '2026-11-01', 'languages': ['en'],
            'image': {'alt': {'en': 'A documented cover image'}},
            'translations': {'en': {'title': 'Example', 'description': 'Summary'}}
        }
        with patch.object(build_pages, 'ORIGIN', 'https://samuelokotako.com'):
            head = build_pages.seo_head('en', 'writing', 'Example', 'Summary', 'example', image='/assets/example.webp', article=article)
        self.assertIn('property="og:image:alt" content="A documented cover image"', head)

    def test_article_html_rejects_encoded_script_links(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            body = root / 'content/articles/example/en.html'
            body.parent.mkdir(parents=True)
            body.write_text('<p><a href="&#x6a;avascript:alert(1)">bad</a></p>')
            with patch.object(build_pages, 'ROOT', root):
                with self.assertRaises(ValueError):
                    build_pages.article_body({'slug': 'example'}, 'en')

    def test_english_only_article_is_static_and_localized(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / 'site'
            shutil.copytree(SOURCE, root, ignore=shutil.ignore_patterns('.git', 'public', '__pycache__'))
            article = {
                'slug': 'sample-english-article', 'status': 'published', 'visibility': 'public',
                'date': '2026-11-05', 'languages': ['en'], 'categories': ['Data Engineering'],
                'tags': ['Python'], 'image': None,
                'translations': {'en': {'title': 'A </script><script>alert(1)</script> article', 'description': 'Fixture description.', 'seo_title': 'SEO article title', 'seo_description': 'SEO article description.'}}
            }
            draft = {**article, 'slug': 'never-publish-draft', 'status': 'draft'}
            private = {**article, 'slug': 'never-publish-private', 'visibility': 'private'}
            (root / 'content' / 'articles.json').write_text(json.dumps([article, draft, private]))
            body = root / 'content' / 'articles' / article['slug']
            body.mkdir(parents=True)
            (body / 'en.html').write_text('<p>Fixture body with a safe paragraph.</p>')
            env = {**os.environ, 'SITE_URL': 'https://samuelokotako.com', 'CF_PAGES': '1', 'CF_PAGES_BRANCH': 'main', 'PYTHONDONTWRITEBYTECODE': '1'}
            for script in ('build_pages.py', 'check_site.py'):
                subprocess.run(['python3', '-B', script], cwd=root, env=env, check=True, capture_output=True, text=True)
            public = root / 'public'
            page = (public / 'en/writing/sample-english-article/index.html').read_text()
            self.assertNotIn('</script><script>alert(1)</script>', page)
            self.assertIn('A \\u003c/script\\u003e\\u003cscript\\u003ealert(1)', page)
            self.assertIn('<title>SEO article title</title>', page)
            self.assertIn('content="SEO article description."', page)
            self.assertIn('<link rel="canonical" href="https://samuelokotako.com/en/writing/sample-english-article/">', page)
            self.assertIn('hreflang="en"', page)
            self.assertNotIn('hreflang="it" href="https://samuelokotako.com/it/writing/sample-english-article/"', page)
            self.assertFalse((public / 'it/writing/sample-english-article').exists())
            self.assertFalse((public / 'fr/writing/sample-english-article').exists())
            self.assertFalse((public / 'en/writing/never-publish-draft').exists())
            self.assertFalse((public / 'en/writing/never-publish-private').exists())
            self.assertTrue((public / 'it/writing/index.html').exists())
            feed = ET.parse(public / 'en/writing/feed.xml')
            self.assertEqual(len(feed.findall('.//item')), 1)
            self.assertEqual(len(ET.parse(public / 'it/writing/feed.xml').findall('.//item')), 0)
            article['image'] = {'src': '/assets/unapproved.jpg', 'width': 800, 'height': 600, 'alt': {'en': 'Unapproved image'}}
            (root / 'content' / 'articles.json').write_text(json.dumps([article]))
            rejected = subprocess.run(['python3', '-B', 'build_pages.py'], cwd=root, env=env, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn('documented image publication rights', rejected.stderr)
            article['image'] = None
            article['translations']['en']['date'] = '2026-99-99'
            (root / 'content' / 'articles.json').write_text(json.dumps([article]))
            rejected = subprocess.run(['python3', '-B', 'build_pages.py'], cwd=root, env=env, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn('invalid en publication date', rejected.stderr)

    def test_feed_uses_localized_dates_for_order(self):
        rows = [
            {'slug': 'older-shared', 'date': '2026-01-01', 'languages': ['en'], 'translations': {'en': {'title': 'Published later', 'description': 'A', 'date': '2026-10-01'}}},
            {'slug': 'newer-shared', 'date': '2026-02-01', 'languages': ['en'], 'translations': {'en': {'title': 'Published earlier', 'description': 'B', 'date': '2026-03-01'}}},
        ]
        with patch.object(build_pages, 'ARTICLES', rows), patch.object(build_pages, 'ORIGIN', 'https://samuelokotako.com'):
            feed = build_pages.writing_feed('en')
        self.assertLess(feed.index('Published later'), feed.index('Published earlier'))

if __name__ == '__main__':
    unittest.main()
