from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class FashionBookIsolationTests(unittest.TestCase):
    def test_isolated_preview_has_no_unauthorized_media_or_public_link(self):
        preview = ROOT / 'fashion-book'
        markup = (preview / 'index.html').read_text()
        headers = (preview / '_headers').read_text()
        self.assertIn('noindex', markup)
        self.assertIn('X-Robots-Tag: noindex', headers)
        self.assertIn('Allow: /', (preview / 'robots.txt').read_text())
        self.assertNotIn('184 cm', markup)
        self.assertFalse(list(preview.rglob('*.jpg')) + list(preview.rglob('*.webp')))
        self.assertFalse((ROOT / 'public' / 'fashion-book').exists())
        self.assertNotIn('/fashion-book/', (ROOT / 'public' / 'en' / 'index.html').read_text())

if __name__ == '__main__':
    unittest.main()
