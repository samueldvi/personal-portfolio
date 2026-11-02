#!/usr/bin/env python3
"""Check generated routes, anchors, assets, metadata and redirect safety."""
from html.parser import HTMLParser
from html import escape
from pathlib import Path
from urllib.parse import urlsplit, unquote
import sys
import xml.etree.ElementTree as ET
from site_config import SITE_URL
from site_content import LANGS
from build_pages import routes, ARTICLES, GALLERIES, MOMENTS, PROJECT_DETAILS, PROJECTS, INITIATIVES, ITS_MODULES, read_redirects

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / 'public'
ROUTES = ('', 'about/', 'projects/', 'experience/', 'contact/')


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.assets = []
        self.robots = []
        self.canonicals = []
        self.alternates = []
        self.lang = None
        self.headings = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html':
            self.lang = a.get('lang')
        if tag == 'h1':
            self.headings += 1
        if a.get('id'):
            if a['id'] in self.ids:
                raise AssertionError(f'Duplicate ID: {a["id"]}')
            self.ids.add(a['id'])
        if tag == 'a' and a.get('href'):
            self.links.append(a['href'])
        if tag in ('script', 'img', 'source', 'video') and a.get('src'):
            self.assets.append(a['src'])
        if tag == 'img' and a.get('srcset'):
            self.assets += [candidate.strip().split()[0] for candidate in a['srcset'].split(',') if candidate.strip()]
        if tag == 'video' and a.get('poster'):
            self.assets.append(a['poster'])
        if tag == 'link':
            if a.get('rel') == 'stylesheet':
                self.assets.append(a['href'])
            if a.get('rel') == 'canonical':
                self.canonicals.append(a['href'])
            if a.get('rel') == 'alternate' and a.get('hreflang'):
                self.alternates.append((a['hreflang'], a['href']))
        if tag == 'meta' and a.get('name') == 'robots':
            self.robots.append(a.get('content'))


def resolve(source, link):
    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc:
        return None, None
    if parsed.path.startswith('/'):
        local = PUBLIC / unquote(parsed.path).lstrip('/')
    else:
        local = source.parent / unquote(parsed.path)
    if not parsed.path:
        local = source
    if local.is_dir() or parsed.path.endswith('/'):
        local = local / 'index.html'
    return local.resolve(), parsed.fragment


def check():
    assert PUBLIC.is_dir(), 'Run python3 build_pages.py first'
    expected = [PUBLIC / 'index.html', PUBLIC / '404.html']
    expected += [PUBLIC / lang / '404.html' for lang in LANGS]
    expected += [PUBLIC / lang / route / 'index.html' for lang in LANGS for route in ROUTES]
    expected += [PUBLIC / lang / route / 'index.html' for lang in LANGS for route in routes() if route not in ('home',) + tuple(x.strip('/') for x in ROUTES if x)]
    expected += [PUBLIC / lang / 'writing' / item['slug'] / 'index.html' for lang in LANGS for item in ARTICLES]
    expected += [PUBLIC / lang / 'projects' / item['id'] / 'index.html' for lang in LANGS for item in PROJECT_DETAILS]
    for file in expected:
        assert file.is_file(), f'Missing route: {file.relative_to(PUBLIC)}'
    for lang in LANGS:
        education = (PUBLIC / lang / 'experience' / 'index.html').read_text(encoding='utf-8')
        assert education.count('class="module-grade"') == 28, f'Incomplete ITS module table: {lang}'
        assert all(escape(item['name']) in education and f'class="module-grade">{escape(item["grade"])}</td>' in education for item in ITS_MODULES), f'Incorrect ITS module transcription: {lang}'
        assert 'Ore</th>' not in education and 'CFU</th>' not in education, f'Hours or credits leaked: {lang}'
        for project in PROJECT_DETAILS:
            detail = (PUBLIC / lang / 'projects' / project['id'] / 'index.html').read_text(encoding='utf-8')
            assert detail.count('class="case-section') >= 9 and 'case-evidence' in detail, f'Incomplete case study: {lang}/{project["id"]}'
        for draft in (item['id'] for item in PROJECTS if item.get('detail') != 'published'):
            assert not (PUBLIC / lang / 'projects' / draft).exists(), f'Draft case study published: {lang}/{draft}'
    redirects = read_redirects()
    assert (PUBLIC / '_redirects').exists() == bool(redirects), 'Generated redirect file mismatch'
    pages = {}
    for file in PUBLIC.rglob('*.html'):
        page = Page()
        page.feed(file.read_text(encoding='utf-8'))
        assert page.headings == 1, f'Expected one h1: {file}'
        assert page.lang in LANGS, f'Missing language: {file}'
        pages[file.resolve()] = page
    assert len(pages) == len({p.resolve() for p in expected}), f'Unexpected HTML output: {len(pages)} pages'
    for file, page in pages.items():
        for link in page.links + page.assets:
            target, fragment = resolve(file, link)
            if target is None:
                continue
            assert PUBLIC.resolve() in target.parents or target == PUBLIC.resolve(), f'Path leaves public/: {link}'
            assert target.is_file(), f'Broken internal path: {file.relative_to(PUBLIC)} -> {link}'
            if fragment:
                assert fragment in pages[target].ids, f'Broken anchor: {file.relative_to(PUBLIC)} -> {link}'
        if file.name == '404.html':
            assert any('noindex' in x for x in page.robots), f'404 must be noindex: {file}'
            markup = file.read_text(encoding='utf-8')
            assert 'id="themeSelect"' in markup and 'portfolio-theme' in markup, f'404 theme control is missing: {file}'
            assert '/en/projects/' in markup if file.parent == PUBLIC else f'/{page.lang}/projects/' in markup, f'404 projects link is missing: {file}'
            assert '/en/' in markup if file.parent == PUBLIC else f'/{page.lang}/' in markup, f'404 home link is missing: {file}'
            assert all(urlsplit(link).scheme == '' and not urlsplit(link).netloc for link in page.assets), f'404 has a remote dependency: {file}'
    origin = SITE_URL.rstrip('/')
    if not origin:
        assert (PUBLIC / 'robots.txt').read_text() == 'User-agent: *\nDisallow: /\n'
        assert not (PUBLIC / 'sitemap.xml').exists()
        for file, page in pages.items():
            assert any('noindex' in x for x in page.robots), f'Unpublished page is indexable: {file}'
            assert not page.canonicals and not page.alternates, f'Fake SEO URL: {file}'
    else:
        for file, page in pages.items():
            if file.name == '404.html':
                continue
            assert len(page.canonicals) == 1 and page.canonicals[0].startswith(origin), f'Canonical: {file}'
            assert {lang for lang, _ in page.alternates}.issuperset(LANGS), f'Hreflang: {file}'
        tree = ET.parse(PUBLIC / 'sitemap.xml')
        locs = [x.text for x in tree.findall('.//{*}loc')]
        assert locs and all(x.startswith(origin) for x in locs)
    if not ARTICLES:
        assert not any((PUBLIC / lang / 'writing').exists() for lang in LANGS), 'Empty writing page was published'
    if not GALLERIES:
        assert not any((PUBLIC / lang / 'gallery').exists() for lang in LANGS), 'Empty gallery page was published'
    if not MOMENTS:
        assert not any((PUBLIC / lang / 'moments').exists() for lang in LANGS), 'Unapproved moments page was published'
    if not INITIATIVES:
        assert not any((PUBLIC / lang / 'initiatives').exists() for lang in LANGS), 'Empty initiatives page was published'
    print(f'OK: {len(pages)} pages, 3 languages, internal links/assets/anchors, 404 metadata, SEO state.')
    print('Cloudflare HTTP 404 status requires verification after deployment.')


if __name__ == '__main__':
    try:
        check()
    except (AssertionError, OSError, ValueError, ET.ParseError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        raise SystemExit(1)
