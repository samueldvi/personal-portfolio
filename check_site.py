#!/usr/bin/env python3
"""Check generated routes, anchors, assets, metadata and redirect safety."""
from html.parser import HTMLParser
from html import escape
import hashlib
from pathlib import Path
from urllib.parse import urlsplit, unquote
import sys
import xml.etree.ElementTree as ET
from site_config import SITE_URL, INDEXING_ENABLED
from site_content import LANGS, CONTENT
from build_pages import routes, ARTICLES, GALLERIES, MOMENTS, PROJECT_DETAILS, PROJECTS, PROJECT_VISUALS, ALL_PROJECTS, INITIATIVES, ITS_MODULES, read_redirects, sitemap_paths, SOCIAL_IMAGE, DOCUMENTS

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
        self.title = ''
        self.in_title = False
        self.description = ''
        self.metadata = {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'html':
            self.lang = a.get('lang')
        if tag == 'h1':
            self.headings += 1
        if tag == 'title':
            self.in_title = True
        if a.get('id'):
            if a['id'] in self.ids:
                raise AssertionError(f'Duplicate ID: {a["id"]}')
            self.ids.add(a['id'])
        if tag == 'a' and a.get('href'):
            self.links.append(a['href'])
        if tag in ('script', 'img', 'source', 'video') and a.get('src'):
            self.assets.append(a['src'])
        if tag in ('img', 'source') and a.get('srcset'):
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
        if tag == 'meta':
            self.metadata[a.get('name') or a.get('property')] = a.get('content', '')
            if a.get('name') == 'description':
                self.description = a.get('content', '')

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


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
        home = (PUBLIC / lang / 'index.html').read_text(encoding='utf-8')
        assert all(f'class="{section}' in home for section in ('home-hero', 'home-featured', 'home-scope', 'home-path', 'home-contact')), f'Incomplete homepage: {lang}'
        assert home.count('class="home-project"') == min(3, len(PROJECTS)), f'Featured projects mismatch: {lang}'
        assert f'id="hero-title"><span>{escape(CONTENT[lang]["hero_title"])}</span>' in home and escape(CONTENT[lang]['hero_title_follow']) in home, f'Home value proposition missing: {lang}'
        assert 'aria-current="page"' in home, f'Active homepage navigation missing: {lang}'
        assert home.count('class="home-skill__evidence"') == 2 and home.count('class="home-skill__pending"') == 1, f'Homepage case-study evidence mismatch: {lang}'
        assert all(f'href="/{lang}/projects/{item["id"]}/"' in home for item in PROJECT_DETAILS if item['category'] in ('engineering', 'governance')), f'Available case-study link missing: {lang}'
        assert 'bank-loan-approval-prediction' not in home, f'Unverified ML draft linked from homepage: {lang}'
        cv = {item['language']: item for item in DOCUMENTS if item.get('kind') == 'cv'}
        if cv:
            expected_cv = cv[lang]['file']
            expected_label = {'it': 'Scarica il CV', 'en': 'Download resume', 'fr': 'Télécharger mon CV'}[lang]
            assert home.count('class="home-contact__cv"') == 1, f'CV link count: {lang}'
            assert f'href="{expected_cv}" type="application/pdf" download>{expected_label}' in home, f'CV language, label or PDF path: {lang}'
        about = (PUBLIC / lang / 'about' / 'index.html').read_text(encoding='utf-8')
        assert 'id="about-beyond-title"' in about, f'About secondary section missing: {lang}'
        assert f'href="/{lang}/contact/"' in about and 'class="about-note section"' in about, f'About personal note contact link missing: {lang}'
        assert CONTENT[lang]['about_fashion_title'] in about and CONTENT[lang]['about_mediation_title'] in about, f'About personal areas missing: {lang}'
        contact = (PUBLIC / lang / 'contact' / 'index.html').read_text(encoding='utf-8')
        assert 'action="https://formspree.io/f/xgaappab"' in contact and 'method="POST"' in contact, f'Formspree action or POST method missing: {lang}'
        assert all(f'name="{name}"' in contact for name in ('name', 'email', 'reason', 'message', '_gotcha')), f'Incomplete contact form: {lang}'
        assert 'contact-form.js' in contact and 'data-form-status' in contact and 'aria-live="polite"' in contact, f'Accessible AJAX form missing: {lang}'
        assert 'https://formspree.io/legal/privacy-policy/' in contact, f'Privacy notice missing: {lang}'
        email = 'samuel.okotako.work@gmail.com'
        assert contact.count('href="mailto:') == 1 and f'<a class="contact-email" href="mailto:{email}">{email}</a>' in contact, f'Professional mailto missing or duplicated: {lang}'
        education = (PUBLIC / lang / 'experience' / 'index.html').read_text(encoding='utf-8')
        assert education.count('class="module-grade"') == 28, f'Incomplete ITS module table: {lang}'
        assert all(escape(item['name']) in education and f'class="module-grade">{escape(item["grade"])}</td>' in education for item in ITS_MODULES), f'Incorrect ITS module transcription: {lang}'
        assert 'Ore</th>' not in education and 'CFU</th>' not in education, f'Hours or credits leaked: {lang}'
        for project in PROJECT_DETAILS:
            detail = (PUBLIC / lang / 'projects' / project['id'] / 'index.html').read_text(encoding='utf-8')
            assert detail.count('class="case-section') >= 9 and 'case-evidence' in detail, f'Incomplete case study: {lang}/{project["id"]}'
            assert 'id="architecture"' in detail and '<ol>' in detail and 'case-jump' in detail and 'case-next' in detail, f'Case navigation or process missing: {lang}/{project["id"]}'
            assert 'case-section--architecture' in detail, f'Missing architecture: {lang}/{project["id"]}'
            if project['id'] == 'dbt':
                assert 'case-visual-break' in detail and 'ecommerce-dashboard-720.webp' in detail, f'Missing authentic screenshot: {lang}/{project["id"]}'
        for draft in (item['id'] for item in ALL_PROJECTS if item.get('detail') != 'published'):
            assert not (PUBLIC / lang / 'projects' / draft).exists(), f'Draft case study published: {lang}/{draft}'
        project_index = (PUBLIC / lang / 'projects' / 'index.html').read_text(encoding='utf-8')
        assert project_index.count('<article class="project-card') == len(PROJECTS), f'Incorrect public project count: {lang}'
        assert 'id="projectGrid"' in project_index and 'aria-controls="projectGrid"' in project_index and 'aria-live="polite"' in project_index, f'Accessible project filters missing: {lang}'
        assert 'data-filter="machine-learning"' not in project_index, f'Empty Machine Learning filter published: {lang}'
        assert 'project-card__visual--concept' in project_index and 'project-visual-concept' not in project_index, f'Radar concept visual missing: {lang}'
        for item in PROJECTS:
            assert f'id="project-{item["id"]}"' in project_index, f'Published card missing: {lang}/{item["id"]}'
            assert f'data-category="{item["category"]}"' in project_index, f'Project category missing: {lang}/{item["id"]}'
        for source in ('ecommerce-dashboard.png', 'ecommerce-dashboard-720.webp', 'ecommerce-dashboard-1440.webp', 'ecommerce-LICENSE.txt'):
            assert (PUBLIC / 'assets' / 'projects' / source).is_file(), f'Missing licensed dashboard asset: {source}'
        for item in ALL_PROJECTS:
            if item.get('status') == 'draft':
                assert f'id="project-{item["id"]}"' not in project_index, f'Draft card published: {lang}/{item["id"]}'
                assert not (PUBLIC / lang / 'projects' / item['id']).exists(), f'Draft route published: {lang}/{item["id"]}'
    expected_pdfs = {item['file'].lstrip('/') for item in DOCUMENTS if item['file'].lower().endswith('.pdf')}
    public_pdfs = {str(file.relative_to(PUBLIC)) for file in PUBLIC.rglob('*.pdf')}
    assert public_pdfs == expected_pdfs, f'Unexpected or missing public PDF: {public_pdfs ^ expected_pdfs}'
    assert len(public_pdfs) == 3 and all(path.startswith('cv/') for path in public_pdfs), 'Only the three localized Data Engineer CVs may be public'
    for item in DOCUMENTS:
        if item.get('kind') == 'cv':
            public_file = PUBLIC / item['file'].lstrip('/')
            assert hashlib.sha256(public_file.read_bytes()).hexdigest() == item['sha256'], f'Published CV differs from approved PDF: {item["language"]}'
    redirects = read_redirects()
    assert (PUBLIC / '_redirects').exists() == bool(redirects), 'Generated redirect file mismatch'
    pages = {}
    for file in PUBLIC.rglob('*.html'):
        page = Page()
        page.feed(file.read_text(encoding='utf-8'))
        assert page.headings == 1, f'Expected one h1: {file}'
        assert page.lang in LANGS, f'Missing language: {file}'
        assert page.title.strip() and page.description.strip(), f'Missing title or description: {file}'
        pages[file.resolve()] = page
    for lang in LANGS:
        localized = [(file, page) for file, page in pages.items() if page.lang == lang and file.name != '404.html']
        titles = [page.title for _, page in localized]
        assert len(titles) == len(set(titles)), f'Duplicate {lang} title'
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
    origin = SITE_URL if INDEXING_ENABLED else ''
    if not INDEXING_ENABLED:
        assert (PUBLIC / 'robots.txt').read_text() == 'User-agent: *\nDisallow: /\n'
        assert not (PUBLIC / 'sitemap.xml').exists()
        for file, page in pages.items():
            assert any('noindex' in x for x in page.robots), f'Unpublished page is indexable: {file}'
            assert not page.canonicals and not page.alternates, f'Fake SEO URL: {file}'
    else:
        for file, page in pages.items():
            if file.name == '404.html':
                continue
            local = '/' + str(file.relative_to(PUBLIC).parent).replace('\\', '/') + '/'
            if file.parent == PUBLIC:
                local = '/'
            assert page.canonicals == [origin + local], f'Canonical: {file}'
            alternates = dict(page.alternates)
            assert {code for code in LANGS}.issubset(alternates), f'Hreflang: {file}'
            for code in LANGS:
                expected = origin + ('/' + code + local[3:] if file.parent != PUBLIC else f'/{code}/')
                assert alternates[code] == expected, f'Non-reciprocal hreflang: {file} {code}'
            assert page.metadata.get('og:url') == page.canonicals[0], f'Open Graph URL: {file}'
            assert page.metadata.get('og:image') and page.metadata.get('twitter:image') == page.metadata['og:image'], f'Sharing image: {file}'
            assert page.metadata.get('twitter:card') == 'summary_large_image', f'Twitter card: {file}'
            assert not any('noindex' in value for value in page.robots), f'Public page is noindex: {file}'
        tree = ET.parse(PUBLIC / 'sitemap.xml')
        locs = [x.text for x in tree.findall('.//{*}loc')]
        assert locs == [origin + path for path in sitemap_paths()], 'Sitemap routes do not match published pages'
        assert (PUBLIC / 'robots.txt').read_text().startswith('User-agent: *\nAllow: /\nSitemap: ' + origin), 'Public robots.txt mismatch'
        assert (PUBLIC / SOCIAL_IMAGE.lstrip('/')).is_file(), 'Social image missing'
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
