#!/usr/bin/env python3
"""Build the isolated admin preview with public Supabase configuration only."""
import argparse
import json
import os
from pathlib import Path
import shutil
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).resolve().parent / 'admin'


def build(output):
    output = output.resolve()
    if output == ROOT or ROOT in output.parents or output.exists():
        raise ValueError('Choose a new output directory outside the repository')
    url = os.environ.get('SUPABASE_URL', '').rstrip('/')
    key = os.environ.get('SUPABASE_PUBLISHABLE_KEY', '')
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment or not key:
        raise ValueError('Set an HTTPS SUPABASE_URL origin and SUPABASE_PUBLISHABLE_KEY')
    output.mkdir(parents=True)
    for name in ('index.html', 'admin.css', 'admin.js'):
        shutil.copy2(SOURCE / name, output / name)
    (output / 'config.json').write_text(json.dumps({'supabase_url': url, 'supabase_publishable_key': key}) + '\n')
    (output / '_headers').write_text('/*\n  X-Robots-Tag: noindex, nofollow\n  Cache-Control: no-store\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n')
    (output / 'robots.txt').write_text('User-agent: *\nDisallow: /\n')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(build(args.output))
