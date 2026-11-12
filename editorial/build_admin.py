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
LOCAL_KEYS = {'SUPABASE_URL', 'SUPABASE_PUBLISHABLE_KEY'}


def load_local_config(path):
    """Read two literal values without shell evaluation or printing their contents."""
    values = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        name, separator, value = line.partition('=')
        name = name.strip()
        if not separator or name not in LOCAL_KEYS or name in values:
            raise ValueError('Invalid or duplicate entry in the local editorial configuration')
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        values[name] = value
    if set(values) != LOCAL_KEYS:
        raise ValueError('Both Supabase settings are required in the local editorial configuration')
    return values


def build(output, *, config=None):
    output = output.resolve()
    if output == ROOT or ROOT in output.parents or output.exists():
        raise ValueError('Choose a new output directory outside the repository')
    config = os.environ if config is None else config
    url = config.get('SUPABASE_URL', '').rstrip('/')
    key = config.get('SUPABASE_PUBLISHABLE_KEY', '')
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment or not key.startswith('sb_publishable_'):
        raise ValueError('Set an HTTPS SUPABASE_URL origin and a sb_publishable_ key')
    output.mkdir(parents=True)
    for name in ('index.html', 'admin.css', 'admin.js'):
        shutil.copy2(SOURCE / name, output / name)
    (output / 'config.json').write_text(json.dumps({'supabase_url': url, 'supabase_publishable_key': key}) + '\n')
    (output / '_headers').write_text('/*\n  X-Robots-Tag: noindex, nofollow\n  Cache-Control: no-store\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n')
    (output / 'robots.txt').write_text('User-agent: *\nAllow: /\n')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(build(args.output))
