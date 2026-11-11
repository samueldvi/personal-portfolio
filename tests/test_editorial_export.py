import tempfile
import os
from pathlib import Path
import unittest
from datetime import datetime, timezone
from unittest.mock import patch
from editorial.export_public import fetch_public, normalize, stage


class EditorialExportTests(unittest.TestCase):
    def test_published_locales_only_and_html_is_inert(self):
        parent = {'slug': 'reliable-data', 'editorial_categories': {'label': 'Data Engineering'}, 'editorial_article_tags': [{'editorial_tags': {'label': 'Python'}}]}
        base = {'language': 'en', 'title': 'Reliable data', 'summary': 'A verified example', 'seo_title': 'Reliable data | Samuel Okotako', 'seo_description': 'Technical notes on reliable data.', 'body_markdown': '# Approach\n<script>alert(1)</script>', 'published_at': '2026-11-01T12:00:00Z', 'status': 'published', 'editorial_articles': parent}
        rows = [base, {**base, 'language': 'it', 'status': 'draft'}, {**base, 'language': 'fr', 'published_at': '2099-01-01T00:00:00Z'}]
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'staged'
            self.assertEqual(stage(rows, target), 1)
            self.assertTrue((target / 'articles/reliable-data/en.html').exists())
            self.assertFalse((target / 'articles/reliable-data/it.html').exists())
            self.assertFalse((target / 'articles/reliable-data/fr.html').exists())
            body = (target / 'articles/reliable-data/en.html').read_text()
            self.assertIn('&lt;script&gt;', body)
            self.assertNotIn('<script>', body)
            self.assertEqual(normalize(rows, datetime(2026, 11, 5, tzinfo=timezone.utc))[0]['languages'], ['en'])
            translation = normalize(rows, datetime(2026, 11, 5, tzinfo=timezone.utc))[0]['translations']['en']
            self.assertEqual(translation['seo_title'], 'Reliable data | Samuel Okotako')
            self.assertEqual(translation['seo_description'], 'Technical notes on reliable data.')

    def test_cannot_stage_inside_repository_or_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'existing'
            target.mkdir()
            with self.assertRaises(ValueError):
                stage([], target)

    def test_exporter_rejects_secret_key_before_request(self):
        with patch.dict(os.environ, {'SUPABASE_URL': 'https://example.supabase.co', 'SUPABASE_PUBLISHABLE_KEY': 'sb_secret_fixture'}):
            with self.assertRaises(ValueError):
                fetch_public()

if __name__ == '__main__':
    unittest.main()
