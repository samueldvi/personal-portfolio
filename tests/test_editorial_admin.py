import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from editorial.build_admin import build, ROOT


class EditorialAdminBuildTests(unittest.TestCase):
    def test_requires_configuration_and_writes_isolated_noindex_output(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'admin'
            with patch.dict(os.environ, {'SUPABASE_URL': '', 'SUPABASE_PUBLISHABLE_KEY': ''}):
                with self.assertRaises(ValueError):
                    build(output)
            with patch.dict(os.environ, {'SUPABASE_URL': 'https://example.supabase.co', 'SUPABASE_PUBLISHABLE_KEY': 'sb_secret_fixture'}):
                with self.assertRaises(ValueError):
                    build(output)
            self.assertFalse(output.exists())
            with patch.dict(os.environ, {'SUPABASE_URL': 'https://example.supabase.co', 'SUPABASE_PUBLISHABLE_KEY': 'sb_publishable_fixture'}):
                build(output)
            config = json.loads((output / 'config.json').read_text())
            self.assertEqual(config['supabase_url'], 'https://example.supabase.co')
            self.assertIn('noindex', (output / '_headers').read_text())
            self.assertIn('Allow: /', (output / 'robots.txt').read_text())
            self.assertFalse((ROOT / 'public' / 'admin').exists())

if __name__ == '__main__':
    unittest.main()
