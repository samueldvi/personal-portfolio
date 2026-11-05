#!/usr/bin/env python3
"""Stage RLS-visible, approved articles for the existing static generator.

This never writes into content/ or public/. Review staged output before copying
it into the repository and building a release.
"""
import argparse
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import re
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
LANGS = {'it', 'en', 'fr'}


def render_markdown(source):
    """Small, safe Markdown subset: text is always escaped; raw HTML is inert."""
    result, paragraph, listing, code = [], [], False, False
    def flush():
        if paragraph:
            result.append('<p>' + ' '.join(escape(x, quote=True) for x in paragraph) + '</p>')
            paragraph.clear()
    for raw in source.splitlines():
        line = raw.strip()
        if line.startswith('```'):
            flush()
            if listing:
                result.append('</ul>'); listing = False
            code = not code
            result.append('<pre><code>' if code else '</code></pre>')
        elif code:
            result.append(escape(raw, quote=True) + '\n')
        elif not line:
            flush()
            if listing:
                result.append('</ul>'); listing = False
        elif re.match(r'^#{1,3}\s+', line):
            flush()
            if listing:
                result.append('</ul>'); listing = False
            depth = len(line) - len(line.lstrip('#'))
            tag = min(depth + 1, 4)
            result.append(f'<h{tag}>{escape(line[depth:].strip(), quote=True)}</h{tag}>')
        elif re.match(r'^[-*]\s+', line):
            flush()
            if not listing:
                result.append('<ul>'); listing = True
            result.append('<li>' + escape(line[2:].strip(), quote=True) + '</li>')
        else:
            if listing:
                result.append('</ul>'); listing = False
            paragraph.append(line)
    flush()
    if listing: result.append('</ul>')
    if code: result.append('</code></pre>')
    return '\n'.join(result)


def normalize(rows, now=None):
    now = now or datetime.now(timezone.utc)
    grouped = {}
    for row in rows:
        if row.get('status') != 'published' or row.get('language') not in LANGS:
            continue
        published_at = row.get('published_at')
        if not published_at:
            continue
        published = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
        if published.tzinfo is None or published > now:
            continue
        article = row.get('editorial_articles') or {}
        slug = article.get('slug')
        if not isinstance(slug, str) or not SLUG.fullmatch(slug):
            raise ValueError('Published article has an invalid shared slug')
        language = row['language']
        title = row.get('title')
        summary = row.get('summary')
        body = row.get('body_markdown')
        if not all(isinstance(value, str) and value.strip() for value in (title, summary, body)):
            raise ValueError(f'Published {slug}/{language} lacks title, summary or body')
        category = ((article.get('editorial_categories') or {}).get('label') or 'Writing').strip()
        tags = [part['editorial_tags']['label'] for part in article.get('editorial_article_tags', []) if part.get('editorial_tags', {}).get('label')]
        item = grouped.setdefault(slug, {'status': 'published', 'visibility': 'public', 'slug': slug, 'date': published.date().isoformat(), 'languages': [], 'categories': [category], 'tags': sorted(set(tags)), 'author': 'Samuel Okotako', 'image': None, 'translations': {}, '_bodies': {}})
        if language in item['languages']:
            raise ValueError(f'Duplicate published translation: {slug}/{language}')
        item['languages'].append(language)
        item['translations'][language] = {'title': title.strip(), 'description': summary.strip(), 'date': published.date().isoformat()}
        item['_bodies'][language] = render_markdown(body)
        item['date'] = min(item['date'], published.date().isoformat())
    return [grouped[key] for key in sorted(grouped)]


def fetch_public():
    base = os.environ.get('SUPABASE_URL', '').rstrip('/')
    key = os.environ.get('SUPABASE_PUBLISHABLE_KEY', '')
    parsed = urlsplit(base)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment or not key:
        raise ValueError('Set SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY for public RLS reads')
    select = 'id,language,title,summary,body_markdown,status,published_at,editorial_articles!inner(slug,editorial_categories(label),editorial_article_tags(editorial_tags(label)))'
    query = urlencode({'select': select, 'status': 'eq.published', 'order': 'published_at.desc', 'limit': '1000'})
    request = Request(base + '/rest/v1/editorial_translations?' + query, headers={'apikey': key, 'accept': 'application/json'})
    with urlopen(request, timeout=20) as response:
        rows = json.load(response)
    if not isinstance(rows, list) or len(rows) >= 1000:
        raise ValueError('Unexpected or truncated editorial API response')
    return rows


def stage(rows, output):
    output = output.resolve()
    if output == ROOT or ROOT in output.parents or output.exists():
        raise ValueError('Choose a new staging directory outside the repository')
    items = normalize(rows)
    output.mkdir(parents=True)
    registry = []
    for item in items:
        bodies = item.pop('_bodies')
        registry.append(item)
        for language, markup in bodies.items():
            dest = output / 'articles' / item['slug'] / f'{language}.html'
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(markup + '\n', encoding='utf-8')
    (output / 'articles.json').write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return len(registry)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixture', type=Path, help='Offline fixture; omit for an RLS-filtered Supabase read')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.fixture.read_text(encoding='utf-8')) if args.fixture else fetch_public()
    print(f'Staged {stage(rows, args.output)} articles in {args.output}')
