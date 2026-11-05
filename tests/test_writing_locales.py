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
                'translations': {'en': {'title': 'A sample article', 'description': 'Fixture description.'}}
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

if __name__ == '__main__':
    unittest.main()
