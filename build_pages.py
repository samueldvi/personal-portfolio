#!/usr/bin/env python3
"""Build dependency-free, localized static pages from structured content.

Canonical metadata and indexing require an explicit approved Pages build.
Local and preview builds remain noindex even when SITE_URL is populated.
"""
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
import json
import re
import shutil
from site_config import SITE_URL, INDEXING_ENABLED
from site_content import CONTENT, EXTRA, CASE_STUDIES, LANGS

ROOT = Path(__file__).resolve().parent
CONTACT_EMAIL = 'samuel.okotako.work@gmail.com'
OUTPUT = ROOT / 'public'
BASE_ROUTES = ('home', 'about', 'projects', 'experience', 'contact')
ORIGIN = SITE_URL if INDEXING_ENABLED else ''
if SITE_URL:
    parsed = urlsplit(SITE_URL)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.path or parsed.query or parsed.fragment:
        raise ValueError('SITE_URL must be an HTTPS origin without a path, query or fragment')


def h(value):
    return escape(str(value), quote=True)


def media_sources_from_srcset(value):
    return [candidate.strip().split()[0] for candidate in value.split(',') if candidate.strip()]


def load_registry(name):
    value = json.loads((ROOT / 'content' / f'{name}.json').read_text(encoding='utf-8'))
    if not isinstance(value, list):
        raise ValueError(f'content/{name}.json must contain a list')
    return value


ALL_PROJECTS = load_registry('projects')
PROJECTS = [item for item in ALL_PROJECTS if item.get('status', 'published') == 'published']
PROJECT_VISUALS = json.loads((ROOT / 'content' / 'project_visuals.json').read_text(encoding='utf-8'))
HOME_MEDIA = json.loads((ROOT / 'content' / 'home_media.json').read_text(encoding='utf-8'))
ITS_MODULES = load_registry('its_modules')
PROJECT_DETAILS = [item for item in PROJECTS if item.get('detail') == 'published']
ARTICLES = [item for item in load_registry('articles') if item.get('status') == 'published']
GALLERIES = [item for item in load_registry('galleries') if item.get('status') == 'published']
MOMENTS = [item for item in load_registry('moments') if item.get('status') == 'published']
DOCUMENTS = [item for item in load_registry('documents') if item.get('status') == 'published']
INITIATIVES = [item for item in load_registry('initiatives') if item.get('status') == 'published']
FONT_ASSETS = (
    '/assets/fonts/newsreader-latin-400.woff2',
    '/assets/fonts/manrope-latin-variable.woff2',
    '/assets/fonts/OFL-Newsreader.txt',
    '/assets/fonts/OFL-Manrope.txt',
)
SOCIAL_IMAGE = '/assets/social/samuel-okotako-og.png'
SITE_ASSETS = (*FONT_ASSETS, '/assets/favicon.svg', SOCIAL_IMAGE)


def slug(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
        raise ValueError(f'Invalid URL slug: {value!r}')
    return value


def validate():
    if not isinstance(HOME_MEDIA, dict) or set(HOME_MEDIA) != {'portrait', 'projects', 'creative'} or not isinstance(HOME_MEDIA['projects'], dict):
        raise ValueError('content/home_media.json needs portrait, projects and creative slots')
    for slot, media in [('portrait', HOME_MEDIA['portrait']), ('creative', HOME_MEDIA['creative']), *HOME_MEDIA['projects'].items()]:
        if media is None:
            continue
        if slot not in ('portrait', 'creative') and slot not in {item['id'] for item in PROJECTS}:
            raise ValueError(f'Unknown home media project: {slot}')
        rights = media.get('rights') or {}
        if media.get('status') != 'approved' or rights.get('status') != 'approved' or not rights.get('basis') or not rights.get('credit'):
            raise ValueError(f'Home media {slot} needs documented publication approval')
        if not isinstance(media.get('width'), int) or not isinstance(media.get('height'), int) or min(media['width'], media['height']) < 1:
            raise ValueError(f'Home media {slot} needs positive dimensions')
        if not media.get('src') or not all((media.get('alt') or {}).get(lang) for lang in LANGS):
            raise ValueError(f'Home media {slot} needs fallback source and localized alt text')
        if slot == 'creative' and not all((media.get('caption') or {}).get(lang) for lang in LANGS):
            raise ValueError('Creative home media needs localized captions')
        for key in ('avif_srcset', 'webp_srcset', 'srcset'):
            for candidate in media_sources_from_srcset(media.get(key, '')):
                media_file(candidate)
        media_file(media['src'])
    if len(ITS_MODULES) != 28 or [item.get('number') for item in ITS_MODULES] != list(range(1, 29)):
        raise ValueError('The verified ITS register must contain 28 ordered modules')
    for item in ITS_MODULES:
        if not item.get('name') or not re.fullmatch(r'(?:[0-9]|10)/10|IDONEO', item.get('grade','')):
            raise ValueError('Invalid official ITS module name or grade')
    project_ids = [slug(item['id']) for item in ALL_PROJECTS]
    if len(project_ids) != len(set(project_ids)):
        raise ValueError('Duplicate project ID')
    if set(PROJECT_VISUALS) != {item['id'] for item in PROJECTS}:
        raise ValueError('Project visuals must match published projects')
    for item in ALL_PROJECTS:
        if item.get('status', 'published') not in ('draft', 'published') or item.get('detail') not in ('draft', 'published'):
            raise ValueError(f'Invalid project publication state: {item["id"]}')
        if item.get('status') == 'draft' and item.get('detail') != 'draft':
            raise ValueError(f'Unpublished project cannot have a published detail: {item["id"]}')
        if item in PROJECTS:
            visual = PROJECT_VISUALS[item['id']]
            if visual.get('kind') not in ('flow', 'screenshot', 'concept') or not visual.get('evidence'):
                raise ValueError(f'Invalid visual for {item["id"]}')
            if item.get('detail') == 'published' and (not isinstance(visual.get('steps'), list) or len(visual['steps']) < 2):
                raise ValueError(f'Missing documented process for {item["id"]}')
            if visual['kind'] == 'screenshot':
                media = visual.get('media') or {}
                rights = media.get('rights') or {}
                if rights.get('status') != 'licensed' or not all(rights.get(key) for key in ('license', 'basis', 'credit')):
                    raise ValueError(f'Screenshot rights need a documented license: {item["id"]}')
                if not all(media.get(key) for key in ('src', 'webp_srcset', 'license_file', 'width', 'height')) or not all((media.get('alt') or {}).get(lang) for lang in LANGS):
                    raise ValueError(f'Incomplete screenshot metadata: {item["id"]}')
                if min(media['width'], media['height']) < 1:
                    raise ValueError(f'Invalid screenshot dimensions: {item["id"]}')
                for source in (media['src'], media['license_file'], *media_sources_from_srcset(media['webp_srcset'])):
                    media_file(source)
        if item.get('github'):
            link = urlsplit(item['github'])
            if link.scheme != 'https' or link.netloc != 'github.com' or len(link.path.strip('/').split('/')) < 2:
                raise ValueError(f'Project {item["id"]} needs a valid public GitHub repository URL')
        for lang in LANGS:
            if item.get('detail') == 'published':
                case = CASE_STUDIES[lang].get(item['id'])
                if not case or any(not case.get(key) for key in ('context','problem','goal','responsibility','technologies','architecture','decisions','results','limits','evidence','repo_note')):
                    raise ValueError(f'Incomplete {lang} case study for {item["id"]}')
                if not isinstance(case['decisions'], list) or not all(part.get('heading') and part.get('text') for part in case['decisions']):
                    raise ValueError(f'Invalid technical decisions for {item["id"]}')
                if not isinstance(case['results'], list) or not all(part.get('label') and part.get('detail') for part in case['results']):
                    raise ValueError(f'Invalid verified results for {item["id"]}')
                if not all(case.get(key) for key in ('diagram_title', 'diagram_note', 'diagram_steps', 'checks')) or len(case['diagram_steps']) != len(PROJECT_VISUALS[item['id']]['steps']):
                    raise ValueError(f'Incomplete localized architecture diagram for {item["id"]}')
            content = item['translations'][lang]
            for key in ('name','type','teaser','context','problem','approach','outcome','tech'):
                if not content.get(key):
                    raise ValueError(f'Missing {lang} {key} for project {item["id"]}')
    if len({item['slug'] for item in ARTICLES}) != len(ARTICLES):
        raise ValueError('Duplicate article slug')
    if len({item['slug'] for item in GALLERIES}) != len(GALLERIES):
        raise ValueError('Duplicate gallery slug')
    for item in ARTICLES:
        slug(item['slug'])
        for key in ('date','languages','categories','image','translations'):
            if key not in item:
                raise ValueError(f'Article {item["slug"]} lacks {key}')
        if set(item['languages']) != set(LANGS):
            raise ValueError(f'Article {item["slug"]} must list it, en and fr languages')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', item['date']):
            raise ValueError(f'Article {item["slug"]} needs ISO date YYYY-MM-DD')
        if not isinstance(item['categories'], list) or not item['categories']:
            raise ValueError(f'Article {item["slug"]} needs categories')
        if item['image']:
            media = item['image']
            if not all(media.get(key) for key in ('src','width','height','alt')):
                raise ValueError(f'Article {item["slug"]} has incomplete image metadata')
            if not all(media['alt'].get(lang) for lang in LANGS):
                raise ValueError(f'Article {item["slug"]} needs localized image alt text')
        for lang in LANGS:
            for key in ('title','description'):
                if not item['translations'][lang].get(key):
                    raise ValueError(f'Article {item["slug"]} lacks {lang} {key}')
            article_body(item, lang)
    for item in GALLERIES:
        slug(item['slug'])
        rights = item.get('rights') or {}
        if rights.get('status') != 'approved' or not rights.get('basis') or not rights.get('credit'):
            raise ValueError(f'Published gallery item {item["slug"]} lacks approved, documented rights')
        for key in ('author','category','kind','media','translations'):
            if not item.get(key):
                raise ValueError(f'Gallery item {item["slug"]} lacks {key}')
        for lang in LANGS:
            for key in ('title','description','alt'):
                if not item['translations'][lang].get(key):
                    raise ValueError(f'Gallery item {item["slug"]} lacks {lang} {key}')
        media = item['media']
        if item['kind'] not in ('image','video','embed') or not all(media.get(x) for x in ('width','height')):
            raise ValueError(f'Gallery item {item["slug"]} has incomplete media dimensions')
        if item['kind'] in ('image','video') and not media.get('src'):
            raise ValueError(f'Gallery item {item["slug"]} needs a local media source')
        if item['kind'] in ('video','embed') and not media.get('poster'):
            raise ValueError(f'Video/embed {item["slug"]} needs a poster')
        if item['kind'] == 'embed':
            parsed = urlsplit(media.get('url',''))
            if parsed.scheme != 'https' or not parsed.netloc:
                raise ValueError(f'Embed {item["slug"]} needs an HTTPS URL')
    if len({item['slug'] for item in MOMENTS}) != len(MOMENTS):
        raise ValueError('Duplicate moment slug')
    for item in MOMENTS:
        slug(item['slug'])
        if item.get('category') not in EXTRA['it']['moment_categories']:
            raise ValueError(f'Moment {item["slug"]} needs a supported editorial category')
        if item.get('context') not in ('personal', 'group', 'company'):
            raise ValueError(f'Moment {item["slug"]} needs a context')
        approval = item.get('approval') or {}
        if approval.get('owner') is not True:
            raise ValueError(f'Moment {item["slug"]} needs explicit owner publication approval')
        if item['context'] in ('group', 'company') and approval.get('people') is not True:
            raise ValueError(f'Moment {item["slug"]} needs confirmation for identifiable people')
        if item['context'] == 'company' and approval.get('organization') is not True:
            raise ValueError(f'Moment {item["slug"]} needs organization publication permission')
        rights = item.get('rights') or {}
        if rights.get('status') != 'approved' or not rights.get('basis') or not rights.get('credit'):
            raise ValueError(f'Moment {item["slug"]} lacks approved, documented rights')
        media = item.get('media') or {}
        if not all(media.get(key) for key in ('small', 'small_width', 'medium', 'medium_width', 'large', 'width', 'height')):
            raise ValueError(f'Moment {item["slug"]} needs responsive media and dimensions')
        if not all(isinstance(media[key], int) and media[key] > 0 for key in ('small_width', 'medium_width', 'width', 'height')):
            raise ValueError(f'Moment {item["slug"]} needs positive image dimensions')
        if not (media['small_width'] <= media['medium_width'] <= media['width']):
            raise ValueError(f'Moment {item["slug"]} has inconsistent image widths')
        if not all(str(media[key]).endswith('.webp') for key in ('small', 'medium', 'large')):
            raise ValueError(f'Moment {item["slug"]} must use optimized WebP variants')
        for lang in LANGS:
            content = item['translations'][lang]
            if not all(content.get(key) for key in ('title', 'caption', 'alt')):
                raise ValueError(f'Moment {item["slug"]} needs {lang} title, caption and alt')
    if len({item['slug'] for item in INITIATIVES}) != len(INITIATIVES):
        raise ValueError('Duplicate initiative slug')
    for item in INITIATIVES:
        slug(item['slug'])
        if not item.get('category'):
            raise ValueError(f'Initiative {item["slug"]} needs a category')
        for lang in LANGS:
            if not all(item['translations'][lang].get(key) for key in ('title','summary')):
                raise ValueError(f'Initiative {item["slug"]} needs {lang} title and summary')
    for item in DOCUMENTS:
        slug(item['slug'])
        if not item.get('file') or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', item.get('updated', '')):
            raise ValueError(f'Document {item["slug"]} needs file and updated date')
        approval = item.get('approval') or {}
        if approval.get('owner') is not True or approval.get('privacy_reviewed') is not True:
            raise ValueError(f'Document {item["slug"]} needs explicit owner and privacy approval')
        if item.get('kind') == 'cv' and (item.get('language') not in ('it', 'en') or not item['file'].lower().endswith('.pdf')):
            raise ValueError(f'CV {item["slug"]} needs an IT/EN language and a PDF file')
        if item['file'].lower().endswith('.pdf'):
            with media_file(item['file'])[0].open('rb') as document_file:
                if document_file.read(4) != b'%PDF':
                    raise ValueError(f'Document {item["slug"]} is not a PDF')
        for lang in LANGS:
            if not all(item['translations'][lang].get(key) for key in ('title','description')):
                raise ValueError(f'Document {item["slug"]} needs {lang} title and description')
    cv_languages = [item['language'] for item in DOCUMENTS if item.get('kind') == 'cv']
    if cv_languages and sorted(cv_languages) != ['en', 'it']:
        raise ValueError('Public CV requires one approved IT PDF and one approved EN PDF')
    for source in published_media_sources():
        media_file(source)


def routes():
    result = list(BASE_ROUTES)
    if ARTICLES:
        result.insert(3, 'writing')
    if GALLERIES:
        result.insert(4 if ARTICLES else 3, 'gallery')
    if MOMENTS:
        result.insert(-1, 'moments')
    if INITIATIVES:
        result.insert(-1, 'initiatives')
    return result


def path(lang, route='home', slug_value=None):
    base = f'/{lang}/'
    if route == 'home':
        return base
    base += f'{route}/'
    return base + f'{slug(slug_value)}/' if slug_value else base


def absolute(local_path):
    return ORIGIN + local_path


def early_theme():
    return '''<script>try{const choice=localStorage.getItem('portfolio-theme');if(choice==='light'||choice==='dark')document.documentElement.dataset.theme=choice}catch(_){}</script>'''


def seo_head(lang, route, title, description, slug_value=None, noindex=False, image=None, article=None):
    tags = [f'<meta name="description" content="{h(description)}">', '<meta name="color-scheme" content="light dark">']
    if noindex or not ORIGIN:
        tags.append('<meta name="robots" content="noindex, nofollow">')
    else:
        target = absolute(path(lang, route, slug_value)) if lang else absolute('/')
        tags.append(f'<link rel="canonical" href="{h(target)}">')
        if lang:
            for code in LANGS:
                tags.append(f'<link rel="alternate" hreflang="{code}" href="{h(absolute(path(code, route, slug_value)))}">')
            if route == 'home':
                tags.append(f'<link rel="alternate" hreflang="x-default" href="{h(absolute("/"))}">')
        else:
            for code in LANGS:
                tags.append(f'<link rel="alternate" hreflang="{code}" href="{h(absolute(path(code)))}">')
            tags.append(f'<link rel="alternate" hreflang="x-default" href="{h(absolute("/"))}">')
    tags += [f'<meta property="og:title" content="{h(title)}">', f'<meta property="og:description" content="{h(description)}">', f'<meta property="og:type" content="{"article" if article else "website"}">', '<meta property="og:site_name" content="Samuel Okotako">']
    if lang:
        locale = {'it':'it_IT', 'en':'en_US', 'fr':'fr_FR'}[lang]
        tags.append(f'<meta property="og:locale" content="{locale}">')
    if ORIGIN and not noindex:
        target = absolute(path(lang, route, slug_value)) if lang else absolute('/')
        tags.append(f'<meta property="og:url" content="{h(target)}">')
    if ORIGIN and not noindex:
        share_image = image if article and image else SOCIAL_IMAGE
        image_url = absolute(share_image)
        tags.extend((
            f'<meta property="og:image" content="{h(image_url)}">',
            f'<meta property="og:image:alt" content="{h("Samuel Okotako — Data Engineering, Machine Learning, Data Governance")}">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{h(title)}">',
            f'<meta name="twitter:description" content="{h(description)}">',
            f'<meta name="twitter:image" content="{h(image_url)}">',
        ))
        if share_image == SOCIAL_IMAGE:
            tags.extend(('<meta property="og:image:width" content="1200">', '<meta property="og:image:height" content="630">'))
    if ORIGIN and route == 'home' and lang and not noindex:
        data = {'@context':'https://schema.org','@type':'Person','name':'Samuel Okotako','url':absolute(path(lang))}
        tags.append(f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>')
    if ORIGIN and article and not noindex:
        data = {'@context':'https://schema.org','@type':'Article','headline':article['translations'][lang]['title'],'datePublished':article['date'],'description':article['translations'][lang]['description'],'inLanguage':lang,'mainEntityOfPage':absolute(path(lang, 'writing', article['slug'])),'author':{'@type':'Person','name':article.get('author','Samuel Okotako')}}
        tags.append(f'<script type="application/ld+json">{json.dumps(data, ensure_ascii=False)}</script>')
    return '\n  '.join(tags)


def navigation(lang, current_route=None):
    c = {**CONTENT[lang], **EXTRA[lang]}
    names = dict(zip(BASE_ROUTES, c['nav']))
    names.update(writing=c['writing_nav'], gallery=c['gallery_nav'], moments=c['moments_nav'], initiatives=c['initiatives_nav'])
    links = []
    for route in routes():
        current = ' aria-current="page"' if route == current_route else ''
        links.append(f'<a href="{path(lang, route)}"{current}>{h(names[route])}</a>')
    return ''.join(links)


def language_switch(lang, route, current=True, slug_value=None):
    c = CONTENT[lang]
    links = ''.join(f'<a href="{path(code, route, slug_value)}" hreflang="{code}" lang="{code}" data-language="{code}"{ " aria-current=\"page\"" if code == lang and current else ""}>{code.upper()}</a>' for code in LANGS)
    return f'<div class="language-switch" role="group" aria-label="{h(c["language_label"])}">{links}</div>'


def theme_control(c):
    options = ''.join(f'<option value="{value}">{h(label)}</option>' for value,label in zip(('auto','light','dark'), c['theme_options']))
    return f'<label class="theme-control"><span class="visually-hidden">{h(c["theme_label"])}</span><select id="themeSelect" aria-label="{h(c["theme_label"])}">{options}</select></label>'


def shell(lang, route, body, title, description, *, not_found=False, slug_value=None, image=None, article=None, root=False):
    c = CONTENT[lang]
    depth = 0 if root else 1 if route == 'home' or not_found else 2 if not slug_value else 3
    asset_prefix = '../' * depth
    home_href = '/' if root else path(lang)
    nav = navigation(lang, route if route in routes() and not not_found else None)
    contact_script = f'<script src="{asset_prefix}contact-form.js" defer></script>' if route == 'contact' else ''
    return f'''<!doctype html>
<html lang="{lang}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{h(title)}</title>
  {seo_head(lang, route, title, description, slug_value, noindex=not_found, image=image, article=article)}
  {early_theme()}
  <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
  <link rel="preload" href="/assets/fonts/newsreader-latin-400.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="{asset_prefix}style.css"><script src="{asset_prefix}script.js" defer></script>{contact_script}
</head>
<body data-page="{h(route)}">
<a class="skip-link" href="#main">{h(c['skip'])}</a>
<header class="site-header"><div class="container header-inner"><a class="wordmark" href="{home_href}" aria-label="SO Samuel Okotako — {h(c['nav'][0])}"><span class="wordmark-mark" aria-hidden="true">S<span>O</span></span><span>Samuel <strong>Okotako</strong></span></a><nav class="nav" id="navMenu" aria-label="{h(c['nav_label'])}">{nav}</nav><div class="header-tools">{language_switch(lang, route if route in routes() else 'home', current=not not_found, slug_value=slug_value)}{theme_control(c)}</div><button class="menu-toggle" id="menuToggle" type="button" aria-controls="navMenu" aria-expanded="false" aria-label="{h(c['menu_open'])}" data-open-label="{h(c['menu_open'])}" data-close-label="{h(c['menu_close'])}"><span></span><span></span></button></div></header>
<main id="main">{body}</main>
<footer class="site-footer"><div class="container footer-inner"><span>© 2026 Samuel Okotako</span><a href="{path(lang)}">{h(c['footer_top'])} ↑</a></div></footer>
</body></html>'''


def home_visual(media, lang, kind, sizes, priority=False):
    """Render approved media, or a clearly illustrative CSS composition."""
    if media is None:
        return f'<div class="home-art home-art--{h(kind)}" aria-hidden="true"><span class="home-art__grid"></span><span class="home-art__ring"></span><span class="home-art__trace"></span><span class="home-art__monogram">SO</span></div>'
    sources = ''.join(
        f'<source type="image/{format_name}" srcset="{h(media[key])}" sizes="{h(sizes)}">'
        for format_name, key in (('avif', 'avif_srcset'), ('webp', 'webp_srcset')) if media.get(key)
    )
    srcset = f' srcset="{h(media["srcset"])}" sizes="{h(sizes)}"' if media.get('srcset') else ''
    priority_attr = ' fetchpriority="high"' if priority else ''
    loading = 'eager' if priority else 'lazy'
    return f'<picture class="home-picture">{sources}<img src="{h(media["src"])}"{srcset} width="{media["width"]}" height="{media["height"]}" alt="{h(media["alt"][lang])}" loading="{loading}" decoding="async"{priority_attr}></picture>'


def portrait_figure(lang, location):
    media = HOME_MEDIA['portrait']
    if media is None:
        return f'<div class="{location}__media">{home_visual(None, lang, "portrait", "100vw")}</div>'
    sizes = '(max-width: 639px) 100vw, (max-width: 1179px) 44vw, 32vw'
    priority = location in ('home-hero', 'about-hero')
    visual = home_visual(media, lang, 'portrait', sizes, priority=priority)
    return f'<figure class="{location}__media portrait-figure">{visual}<figcaption><small>{h(CONTENT[lang]["photo_credit"])}</small></figcaption></figure>'


def home(lang):
    c = CONTENT[lang]
    cv_documents = {item.get('language'): item for item in DOCUMENTS if item.get('kind') == 'cv'}
    cv_link = ''
    if {'it', 'en'} <= cv_documents.keys():
        cv = cv_documents['it' if lang == 'it' else 'en']
        cv_link = f'<a class="home-contact__cv" href="{h(cv["file"])}" type="application/pdf" download>{h(c["cv_download"])} <span aria-hidden="true">↓</span></a>'
    featured = []
    for item in PROJECTS[:3]:
        p = item['translations'][lang]
        project_id = item['id']
        href = path(lang, 'projects', project_id) if item.get('detail') == 'published' else path(lang, 'projects') + '#project-' + project_id
        visual = home_visual(HOME_MEDIA['projects'].get(project_id), lang, project_id, '(max-width: 700px) 100vw, (max-width: 1100px) 50vw, 33vw')
        featured.append(f'''<a class="home-project" href="{href}"><div class="home-project__visual">{visual}</div><div class="home-project__body"><div class="home-project__meta"><span>{h(item['number'])} / {len(PROJECTS):02d}</span><span>{h(p['type'])}</span></div><h3>{h(p['name'])}</h3><p>{h(p['teaser'])}</p><div class="home-project__foot"><span>{h(p['tech'])}</span><span class="home-project__arrow" aria-hidden="true">↗</span></div></div></a>''')
    skills = []
    for number, title, text, category in c['focus']:
        cases = [item for item in PROJECT_DETAILS if item['category'] == category]
        if cases:
            links = ''.join(f'<li><a href="{path(lang, "projects", item["id"])}">{h(item["translations"][lang]["name"])} <span aria-hidden="true">↗</span></a></li>' for item in cases)
            evidence = f'<div class="home-skill__evidence"><span>{h(c["home_case_label"])}</span><ul class="home-skill__links">{links}</ul></div>'
        else:
            evidence = f'<p class="home-skill__pending">{h(c["home_case_pending"])}</p>'
        skills.append(f'<li><span class="home-skill__number">{h(number)}</span><div><h3>{h(title)}</h3><p>{h(text)}</p>{evidence}</div></li>')
    portrait = portrait_figure(lang, 'home-hero')
    creative = ''
    if HOME_MEDIA['creative']:
        media = HOME_MEDIA['creative']
        image = home_visual(media, lang, 'creative', '(max-width: 700px) 100vw, 45vw')
        creative = f'''<section class="home-creative home-section section" aria-labelledby="home-creative-title"><div class="container home-creative__layout"><div class="home-creative__copy"><p class="eyebrow"><span class="eyebrow-rule"></span>{h(c['home_creative_label'])}</p><h2 id="home-creative-title">{h(c['home_creative_title'])}</h2><p>{h(c['home_creative_intro'])}</p></div><figure class="home-creative__figure">{image}<figcaption><span>{h(media['caption'][lang])}</span><small>{h(c['photo_credit'])}</small></figcaption></figure></div></section>'''
    body = f'''<section class="home-hero home-section" aria-labelledby="hero-title"><div class="container home-hero__layout"><div class="home-hero__copy"><p class="home-hero__name">Samuel Okotako</p><p class="eyebrow"><span class="eyebrow-rule"></span>{h(c['hero_kicker'])}</p><h1 id="hero-title"><span>{h(c['hero_title'])}</span> <span class="home-hero__promise">{h(c['hero_title_follow'])}</span></h1><p class="home-hero__value">{h(c['hero_value'])}</p><p class="home-hero__intro">{h(c['hero_intro'])}</p><div class="hero-actions"><a class="button button--solid" href="{path(lang,'projects')}">{h(c['hero_cta'])}<span aria-hidden="true">↗</span></a><a class="button button--outline" href="{path(lang,'contact')}">{h(c['hero_contact'])}</a></div></div>{portrait}</div></section>
<section class="home-featured home-section section" aria-labelledby="home-featured-title"><div class="container"><div class="home-section-head"><div><p class="eyebrow"><span class="eyebrow-rule"></span>{h(c['selected_label'])}</p><h2 id="home-featured-title">{h(c['selected_title'])}</h2></div><div class="home-section-head__aside"><p>{h(c['selected_intro'])}</p><a class="text-link" href="{path(lang,'projects')}">{h(c['home_all_projects'])}<span aria-hidden="true">↗</span></a></div></div><div class="home-projects">{''.join(featured)}</div></div></section>
<section class="home-scope home-section section" aria-labelledby="home-scope-title"><div class="container home-scope__layout"><div><p class="eyebrow"><span class="eyebrow-rule"></span>{h(c['focus_label'])}</p><h2 id="home-scope-title">{h(c['home_skills_title'])}</h2></div><ol class="home-skills">{''.join(skills)}</ol></div></section>
<section class="home-path home-section section" aria-labelledby="home-path-title"><div class="container"><div class="home-section-head"><div><p class="eyebrow"><span class="eyebrow-rule"></span>{h(c['home_path_label'])}</p><h2 id="home-path-title">{h(c['home_path_title'])}</h2></div></div><div class="home-path__grid"><article class="home-path__card home-path__card--lead"><span class="home-path__index">01 / {h(c['experience_label'])}</span><h3>Spindox</h3><p>{h(c['home_experience_intro'])}</p><a class="text-link" href="{path(lang,'experience')}">{h(c['home_experience_link'])}<span aria-hidden="true">↗</span></a></article><article class="home-path__card"><span class="home-path__index">02 / {h(c['education_label'])}</span><h3>ITS Steve Jobs Academy</h3><p>{h(c['home_education_intro'])}</p><a class="text-link" href="{path(lang,'experience')}#education">{h(c['home_education_link'])}<span aria-hidden="true">↗</span></a></article><article class="home-path__card"><span class="home-path__index">03 / {h(c['education_label'])}</span><h3>{h(c['unict_name'])}</h3><p>{h(c['home_unict_intro'])}</p><a class="text-link" href="{path(lang,'experience')}#education">{h(c['home_education_link'])}<span aria-hidden="true">↗</span></a></article><article class="home-path__card"><span class="home-path__index">04 / {h(c['education_label'])}</span><h3>I.T. Archimede</h3><p>{h(c['home_archimede_intro'])}</p><a class="text-link" href="{path(lang,'projects')}#project-radar">{h(c['archimede_link'])}<span aria-hidden="true">↗</span></a></article></div></div></section>
{creative}
<section class="home-contact home-section section" aria-labelledby="home-contact-title"><div class="container home-contact__layout"><div><p class="eyebrow"><span class="eyebrow-rule"></span>{h(c['contact_label'])}</p><h2 id="home-contact-title">{h(c['home_contact_title'])}</h2><p>{h(c['home_contact_intro'])}</p></div><div class="home-contact__actions"><a class="button button--light" href="{path(lang,'contact')}#contactForm">{h(c['hero_contact'])}<span aria-hidden="true">↗</span></a>{cv_link}<a class="home-contact__email" href="mailto:{h(CONTACT_EMAIL)}">{h(CONTACT_EMAIL)}</a></div></div></section>'''
    return shell(lang, 'home', body, c['title'], c['description'], image=HOME_MEDIA['portrait']['src'] if HOME_MEDIA['portrait'] else None)


def about(lang):
    c = CONTENT[lang]
    extra = EXTRA[lang]
    steps = ''.join(f'<li><span>0{i}</span><h3>{h(title)}</h3><p>{h(text)}</p></li>' for i, (title, text) in enumerate(c['about_steps'], 1))
    documents = ''
    other_documents = [item for item in DOCUMENTS if item.get('kind') != 'cv']
    if other_documents:
        entries = ''.join(f'<li><a href="{h(item["file"])}">{h(item["translations"][lang]["title"])} ↗</a><p>{h(item["translations"][lang]["description"])}</p></li>' for item in other_documents)
        documents = f'<section class="section public-documents"><div class="container"><h2>{h(extra["documents_title"])}</h2><ul>{entries}</ul></div></section>'
    portrait = portrait_figure(lang, 'about-hero')
    body = f'''<section class="about-hero section inner-page" id="about" aria-labelledby="about-title"><div class="container about-hero__layout"><div class="about-hero__copy"><p class="eyebrow"><span class="eyebrow-rule"></span>{h(c['about_label'])}</p><h1 id="about-title">{h(c['about_title'])}</h1><p>{h(c['about_intro'])}</p></div>{portrait}</div></section>
<section class="about-method section" aria-labelledby="about-method-title"><div class="container"><div class="about-method__head"><p class="eyebrow"><span class="eyebrow-rule"></span>{h(c['about_method_label'])}</p><h2 id="about-method-title">{h(c['about_method_title'])}</h2></div><ol class="method-list">{steps}</ol></div></section>{documents}'''
    return shell(lang, 'about', body, f'{c["about_label"]} | Samuel Okotako', c['about_intro'], image=HOME_MEDIA['portrait']['src'] if HOME_MEDIA['portrait'] else None)


def process_diagram(item, lang, compact=False):
    case = CASE_STUDIES[lang][item['id']]
    steps = ''.join(f'<li><span class="process-diagram__number">{index:02d}</span><span>{h(label)}</span></li>' for index, label in enumerate(case['diagram_steps'], 1))
    title = '' if compact else f'<h3>{h(case["diagram_title"])}</h3>'
    note = '' if compact else f'<figcaption>{h(case["diagram_note"])}</figcaption>'
    return f'<figure class="process-diagram{" process-diagram--compact" if compact else ""}">{title}<ol>{steps}</ol>{note}</figure>'


def project_image(item, lang, compact=False):
    media = PROJECT_VISUALS[item['id']]['media']
    image = f'<picture><source type="image/webp" srcset="{h(media["webp_srcset"])}" sizes="{h("(max-width: 760px) 100vw, 720px" if compact else "(max-width: 900px) 100vw, 880px")}"><img src="{h(media["src"])}" width="{media["width"]}" height="{media["height"]}" alt="{h(media["alt"][lang])}" loading="lazy" decoding="async"></picture>'
    if compact:
        return f'<div class="project-card__visual project-card__visual--image">{image}</div>'
    labels = EXTRA[lang]
    return f'<figure class="case-screenshot">{image}<figcaption>{h(CASE_STUDIES[lang][item["id"]]["visual_caption"])} {h(media["rights"]["credit"])} · <a href="{h(media["license_file"])}">{h(labels["case_license"])}</a></figcaption></figure>'


def project_card(item, lang, lead=False):
    c = CONTENT[lang]; p = item['translations'][lang]; project_id = slug(item['id'])
    visual = PROJECT_VISUALS[project_id]
    url = path(lang, 'projects', project_id) if item.get('detail') == 'published' else f'{path(lang,"experience")}#education'
    cta = EXTRA[lang]['case_cta'] if item.get('detail') == 'published' else c['education_link']
    if visual['kind'] == 'screenshot':
        visual_markup = project_image(item, lang, True)
    elif visual['kind'] == 'flow':
        visual_markup = f'<div class="project-card__visual project-card__visual--flow">{process_diagram(item, lang, True)}</div>'
    else:
        visual_markup = f'<div class="project-card__visual project-card__visual--concept"><span aria-hidden="true" class="concept-radar"><i></i><i></i><i></i></span><span class="concept-caption">{h(c["project_visual_concept"])}</span></div>'
    details = ''
    if item.get('detail') != 'published':
        labels = [('field_context','context'),('field_problem','problem'),('field_approach','approach'),('field_outcome','outcome'),('field_tech','tech')]
        rows = ''.join(f'<div><dt>{h(c[label])}</dt><dd>{h(p[key])}</dd></div>' for label,key in labels)
        details = f'<details class="project-details"><summary>{h(c["details"])}<span aria-hidden="true">＋</span></summary><dl>{rows}</dl></details>'
    return f'''<article class="project-card{" project-card--lead" if lead else ""}" id="project-{project_id}" data-category="{h(item['category'])}"><div class="project-card__copy"><div class="project-card__top"><span class="project-index">{h(item['number'])} / {len(PROJECTS):02d}</span><span class="project-category">{h(p['type'])}</span></div><h2><a href="{url}">{h(p['name'])}</a></h2><p class="project-teaser">{h(p['teaser'])}</p><dl class="project-card__summary"><div><dt>{h(c['field_problem'])}</dt><dd>{h(p['problem'])}</dd></div><div><dt>{h(c['field_approach'])}</dt><dd>{h(p['approach'])}</dd></div></dl><p class="tech-line">{h(p['tech'])}</p><a class="project-link" href="{url}">{h(cta)} <span aria-hidden="true">↗</span></a></div>{visual_markup}{details}</article>'''


def projects(lang):
    c=CONTENT[lang]
    categories={item['category'] for item in PROJECTS}
    labels=dict(c['filters'])
    if not categories.issubset(labels):
        raise ValueError(f'Missing filter labels for {categories-set(labels)}')
    filters=''.join(f'<button type="button" data-filter="{h(value)}" aria-controls="projectGrid" aria-pressed="{str(value=="all").lower()}">{h(labels[value])}</button>' for value in ('all',)+tuple(x for x in labels if x!='all' and x in categories))
    cards='\n'.join(project_card(item,lang,i==0) for i,item in enumerate(PROJECTS))
    body=f'''<section class="section projects inner-page" id="projects" aria-labelledby="projects-title"><div class="container"><div class="section-intro section-intro--wide"><p class="eyebrow"><span class="eyebrow-rule"></span>{h(c['projects_label'])}</p><h1 id="projects-title">{h(c['projects_title'])}</h1><p>{h(c['projects_intro'])}</p></div><div class="filter-bar" role="group" aria-label="{h(c['filters_label'])}">{filters}<span class="filter-count" id="filterCount" aria-live="polite" data-one="{h(c['filter_count_one'])}" data-many="{h(c['filter_count'])}">{len(PROJECTS)} {h(c['filter_count'])}</span></div><div class="project-grid" id="projectGrid">{cards}</div></div></section>'''
    return shell(lang,'projects',body,f'{c["projects_title"]} | Samuel Okotako',c['projects_intro'])


def experience(lang):
    c=CONTENT[lang]
    rows=''.join(f'<tr><th scope="row">{h(item["number"]):s}</th><td>{h(item["name"])}</td><td class="module-grade">{h(item["grade"])}</td></tr>' for item in ITS_MODULES)
    modules=f'<details class="modules" id="its-modules"><summary>{h(c["modules_summary"])}<span aria-hidden="true">＋</span></summary><div class="module-table-wrap"><table><thead><tr><th scope="col">#</th><th scope="col">{h(c["module_name"])}</th><th scope="col">{h(c["module_grade"])}</th></tr></thead><tbody>{rows}</tbody></table></div><p>{h(c["modules_source_note"])}</p></details>'
    body=f'''<section class="section experience inner-page" id="experience" aria-labelledby="experience-title"><div class="container experience-layout"><div class="section-intro"><p class="eyebrow">{h(c['experience_label'])}</p><h1 id="experience-title">{h(c['experience_title'])}</h1><p>{h(c['experience_intro'])}</p></div><div class="experience-story"><div class="experience-story__head"><span class="experience-period">{h(c['experience_period'])}</span><h2>Spindox</h2><p>{h(c['experience_role'])}</p></div><div class="experience-story__row"><span>01</span><div><h3>{h(c['experience_actual_title'])}</h3><p>{h(c['experience_actual'])}</p></div></div><div class="experience-story__row"><span>02</span><div><h3>{h(c['experience_separate_title'])}</h3><p>{h(c['experience_separate'])}</p></div></div></div></div></section>
<section class="section education" id="education" aria-labelledby="education-title"><div class="container"><div class="section-intro section-intro--wide"><p class="eyebrow">{h(c['education_label'])}</p><h2 id="education-title">{h(c['education_title'])}</h2><p>{h(c['education_intro'])}</p></div><div class="education-grid"><article class="education-card education-card--its"><div class="education-card__top"><span class="institution">ITS Steve Jobs Academy</span><span class="level">EQF 5</span></div><h3>{h(c['its_degree'])}</h3><p>{h(c['its_date'])}</p><div class="grade-grid"><div><strong>110/110</strong><span>{h(c['final_grade'])}</span></div><div><strong>9,2/10</strong><span>{h(c['module_average'])}</span></div></div>{modules}</article><div class="education-side"><article class="education-card"><span class="institution">{h(c['unict_name'])}</span><h3>{h(c['unict_degree'])}</h3><span class="status-pill">{h(c['ongoing'])}</span></article><article class="education-card"><span class="institution">I.T. Archimede</span><h3>{h(c['archimede_degree'])}</h3><a href="{path(lang,'projects')}#project-radar">{h(c['archimede_link'])} <span aria-hidden="true">↗</span></a></article></div></div></div></section>'''
    return shell(lang,'experience',body,f'{c["experience_label"]} & {c["education_label"]} | Samuel Okotako',c['experience_intro'])


def contact(lang):
    c = CONTENT[lang]
    reasons = ''.join(f'<option value="{value}">{h(c[key])}</option>' for value, key in (
        ('project', 'form_reason_project'),
        ('collaboration', 'form_reason_collaboration'),
        ('question', 'form_reason_question'),
        ('other', 'form_reason_other'),
    ))
    body = f'''<section class="section contact inner-page" id="contact" aria-labelledby="contact-title"><div class="container contact-layout"><div class="contact-copy"><p class="eyebrow">{h(c['contact_label'])}</p><h1 id="contact-title">{h(c['contact_title'])}</h1><p>{h(c['contact_intro'])}</p><div class="contact-actions"><a class="button button--solid" href="#contactForm">{h(c['contact_form_action'])}<span aria-hidden="true">↗</span></a><a class="contact-email" href="mailto:{h(CONTACT_EMAIL)}">{h(CONTACT_EMAIL)}</a></div><div class="contact-social"><a href="https://github.com/samueldvi" target="_blank" rel="noopener noreferrer">GitHub ↗</a><a href="https://www.linkedin.com/in/okotako-samuel-44492620b" target="_blank" rel="noopener noreferrer">LinkedIn ↗</a></div></div><div class="form-panel"><div class="form-panel__head"><h2>{h(c['form_title'])}</h2></div><p id="formNote">{h(c['form_note'])}</p>
<form id="contactForm" action="https://formspree.io/f/xgaappab" method="POST" aria-describedby="formNote formPrivacy" data-sending="{h(c['form_sending'])}" data-success="{h(c['form_success'])}" data-error-required="{h(c['form_error_required'])}" data-error-email="{h(c['form_error_email'])}" data-error-invalid="{h(c['form_error_invalid'])}" data-error-server-field="{h(c['form_error_server_field'])}" data-error-validation="{h(c['form_error_validation'])}" data-error-server-validation="{h(c['form_error_server_validation'])}" data-error-rate="{h(c['form_error_rate'])}" data-error-blocked="{h(c['form_error_blocked'])}" data-error-honeypot="{h(c['form_error_honeypot'])}" data-error-http="{h(c['form_error_http'])}" data-error-network="{h(c['form_error_network'])}">
<fieldset><legend class="visually-hidden">{h(c['form_title'])}</legend>
<div class="form-field"><label for="contactName">{h(c['form_name'])}</label><input id="contactName" name="name" type="text" autocomplete="name" required maxlength="120" aria-describedby="contactNameError"><span class="form-field-error" id="contactNameError" data-error-for="name"></span></div>
<div class="form-field"><label for="contactEmail">{h(c['form_email'])}</label><input id="contactEmail" name="email" type="email" autocomplete="email" inputmode="email" required maxlength="254" aria-describedby="contactEmailError"><span class="form-field-error" id="contactEmailError" data-error-for="email"></span></div>
<div class="form-field"><label for="contactReason">{h(c['form_reason'])}</label><select id="contactReason" name="reason" required aria-describedby="contactReasonError"><option value="">{h(c['form_reason_placeholder'])}</option>{reasons}</select><span class="form-field-error" id="contactReasonError" data-error-for="reason"></span></div>
<div class="form-field"><label for="contactMessage">{h(c['form_message'])}</label><textarea id="contactMessage" name="message" rows="5" required maxlength="10000" aria-describedby="contactMessageError"></textarea><span class="form-field-error" id="contactMessageError" data-error-for="message"></span></div>
</fieldset>
<div class="form-honeypot" aria-hidden="true"><label for="contactWebsite">Website</label><input id="contactWebsite" name="_gotcha" type="text" tabindex="-1" autocomplete="off"></div>
<p class="form-privacy" id="formPrivacy">{h(c['form_privacy'])} <a href="https://formspree.io/legal/privacy-policy/" target="_blank" rel="noopener noreferrer">{h(c['form_privacy_link'])}</a> {h(c['form_privacy_tail'])}</p>
<button type="submit">{h(c['form_button'])}</button><p class="form-status" data-form-status role="status" aria-live="polite" aria-atomic="true"></p>
</form></div></div></section>'''
    return shell(lang, 'contact', body, f'{c["contact_label"]} | Samuel Okotako', c['contact_intro'])



def project_detail(lang, item):
    labels=EXTRA[lang]; p=item['translations'][lang]; case=CASE_STUDIES[lang][item['id']]
    simple_fields=[('case_context','context'),('case_problem','problem'),('case_goal','goal'),('case_responsibility','responsibility')]
    sections=''.join(f'<section class="case-section"><h2>{h(labels[label])}</h2><p>{h(case[key])}</p></section>' for label,key in simple_fields)
    sections+=f'<section class="case-section case-section--architecture" id="architecture"><h2>{h(labels["case_architecture"])}</h2><div>{process_diagram(item, lang)}</div></section>'
    sections+=f'<section class="case-section"><h2>{h(labels["case_implementation"])}</h2><p>{h(case["architecture"])}</p></section>'
    if PROJECT_VISUALS[item['id']]['kind'] == 'screenshot':
        sections+=f'<div class="case-visual-break">{project_image(item, lang)}</div>'
    decisions=''.join(f'<li><h3>{h(part["heading"])}</h3><p>{h(part["text"])}</p></li>' for part in case['decisions'])
    sections+=f'<section class="case-section"><h2>{h(labels["case_decisions"])}</h2><ul class="case-list">{decisions}</ul></section>'
    sections+=f'<section class="case-section"><h2>{h(labels["case_checks"])}</h2><p>{h(case["checks"])}</p></section>'
    results=''.join(f'<li><strong>{h(part["label"])}</strong><p>{h(part["detail"])}</p></li>' for part in case['results'])
    sections+=f'<section class="case-section"><h2>{h(labels["case_results"])}</h2><ul class="case-list">{results}</ul></section>'
    sections+=f'<section class="case-section"><h2>{h(labels["case_limits"])}</h2><p>{h(case["limits"])}</p></section>'
    stack=''.join(f'<li>{h(technology)}</li>' for technology in case['technologies'])
    sections+=f'<section class="case-section"><h2>{h(labels["case_technologies"])}</h2><ul class="case-stack">{stack}</ul></section>'
    repository=f'<a href="{h(item["github"])}" target="_blank" rel="noopener noreferrer">{h(labels["case_repository"])} ↗</a>' if item.get('github') else f'<p>{h(case["repo_note"])}</p>'
    index = PROJECT_DETAILS.index(item)
    next_item = PROJECT_DETAILS[(index + 1) % len(PROJECT_DETAILS)]
    next_link = f'<a class="case-next" href="{path(lang,"projects",next_item["id"])}"><span>{h(labels["case_next"])}</span><strong>{h(next_item["translations"][lang]["name"])}</strong><span aria-hidden="true">↗</span></a>' if len(PROJECT_DETAILS) > 1 else ''
    body = f'<article class="inner-page case-page"><div class="case-hero section"><div class="container"><a class="case-hero__back" href="{path(lang,"projects")}#project-{h(item["id"])}">← {h(labels["case_back"])}</a><p class="eyebrow"><span class="eyebrow-rule"></span>{h(p["type"])}</p><h1>{h(p["name"])}</h1><p class="page-lead">{h(p["teaser"])}</p><a class="case-jump" href="#architecture">{h(labels["case_jump"])} <span aria-hidden="true">↓</span></a></div></div><div class="container case-body"><div class="case-content">{sections}<section class="case-section case-evidence"><h2>{h(labels["case_evidence"])}</h2><p>{h(case["evidence"])}</p>{repository}</section></div><nav class="case-footer" aria-label="{h(labels["case_back"])}"><a class="case-back" href="{path(lang,"projects")}#project-{h(item["id"])}">← {h(labels["case_back"])}</a>{next_link}</nav></div></article>'
    return shell(lang,'projects',body,f'{p["name"]} | Samuel Okotako',p['teaser'],slug_value=item['id'])


def article_body(item, lang):
    location = ROOT / 'content' / 'articles' / slug(item['slug']) / f'{lang}.html'
    if not location.is_file():
        raise ValueError(f'Missing article body: {location.relative_to(ROOT)}')
    markup = location.read_text(encoding='utf-8')
    if re.search(r'<\s*(script|iframe|style|object|embed|form)\b|\bon[a-z]+\s*=|javascript\s*:', markup, re.I):
        raise ValueError(f'Unsafe embedded content in {location.relative_to(ROOT)}')
    return markup


def writing(lang):
    c=EXTRA[lang]
    links=''.join(f'<article class="listing-card"><time datetime="{h(item["date"])}">{h(item["date"])}</time><h2><a href="{path(lang,"writing",item["slug"])}">{h(item["translations"][lang]["title"])}</a></h2><p>{h(item["translations"][lang]["description"])}</p><span>{h(", ".join(item["categories"]))}</span></article>' for item in ARTICLES)
    body=f'<section class="section inner-page listing-page"><div class="container"><p class="eyebrow">{h(c["writing_nav"])}</p><h1>{h(c["writing_title"])}</h1><p class="page-lead">{h(c["writing_intro"])}</p><div class="listing-grid">{links}</div></div></section>'
    return shell(lang,'writing',body,f'{c["writing_title"]} | Samuel Okotako',c['writing_intro'])


def article_page(lang, item):
    c=EXTRA[lang]; p=item['translations'][lang]
    body=f'<article class="section inner-page article-page"><div class="container"><p class="eyebrow">{h(", ".join(item["categories"]))}</p><h1>{h(p["title"])}</h1><p class="page-lead">{h(p["description"])}</p><p class="article-date"><time datetime="{h(item["date"])}">{h(c["published"])} {h(item["date"])}</time></p><div class="article-body">{article_body(item,lang)}</div></div></article>'
    image=item['image']['src'] if item['image'] else None
    if item['image']:
        media=item['image']
        srcset=f' srcset="{h(media["srcset"])}" sizes="(max-width: 820px) 100vw, 820px"' if media.get('srcset') else ''
        visual=f'<figure class="article-image"><img src="{h(media["src"])}"{srcset} width="{int(media["width"])}" height="{int(media["height"])}" alt="{h(media["alt"][lang])}" decoding="async"></figure>'
        body=body.replace('<div class="article-body">',visual+'<div class="article-body">')
    return shell(lang,'writing',body,f'{p["title"]} | Samuel Okotako',p['description'],slug_value=item['slug'],image=image,article=item)


def gallery(lang):
    c=EXTRA[lang]
    cards=[]
    for item in GALLERIES:
        p=item['translations'][lang]; media=item['media']
        if item['kind']=='image':
            srcset=''
            if media.get('srcset'):
                srcset=f' srcset="{h(media["srcset"])}" sizes="(max-width: 700px) 100vw, 50vw"'
            visual=f'<img src="{h(media["src"])}"{srcset} width="{int(media["width"])}" height="{int(media["height"])}" alt="{h(p["alt"])}" loading="lazy" decoding="async">'
        elif item['kind']=='video':
            visual=f'<video controls preload="none" poster="{h(media["poster"])}" width="{int(media["width"])}" height="{int(media["height"])}" aria-label="{h(p["alt"])}"><source src="{h(media["src"])}"></video>'
        else:
            visual=f'<div class="embed-shell" style="aspect-ratio:{int(media["width"])} / {int(media["height"])}"><img src="{h(media["poster"])}" width="{int(media["width"])}" height="{int(media["height"])}" alt="" loading="lazy"><button type="button" data-embed-url="{h(media["url"])}" data-embed-title="{h(p["alt"])}">▶ {h(p["title"])}</button><noscript><a href="{h(media["url"])}">{h(p["title"])}</a></noscript></div>'
        cards.append(f'<figure class="gallery-card">{visual}<figcaption><h2>{h(p["title"])}</h2><p>{h(p["description"])}</p><small>© {h(item["author"])}</small></figcaption></figure>')
    body=f'<section class="section inner-page gallery-page"><div class="container"><p class="eyebrow">{h(c["gallery_nav"])}</p><h1>{h(c["gallery_title"])}</h1><p class="page-lead">{h(c["gallery_intro"])}</p><div class="gallery-grid">{"".join(cards)}</div></div></section>'
    return shell(lang,'gallery',body,f'{c["gallery_title"]} | Samuel Okotako',c['gallery_intro'])



def moments(lang):
    c=EXTRA[lang]
    cards=[]
    for item in MOMENTS:
        p=item['translations'][lang]; media=item['media']
        small=h(media['small']); medium=h(media['medium']); large=h(media['large'])
        srcset = f' srcset="{small} {int(media["small_width"])}w, {medium} {int(media["medium_width"])}w" sizes="(max-width: 700px) 100vw, 50vw"' if media['small_width'] < media['medium_width'] else ''
        cards.append(f'<figure class="moment-card" id="moment-{h(item["slug"])}"><a class="moment-open" href="{large}" data-moment-open data-title="{h(p["title"])}" data-caption="{h(p["caption"])}" data-alt="{h(p["alt"])}" aria-label="{h(c["moments_open"])}: {h(p["title"])}"><img src="{medium}"{srcset} width="{int(media["width"])}" height="{int(media["height"])}" alt="{h(p["alt"])}" loading="lazy" decoding="async"></a><figcaption><span class="eyebrow">{h(c["moment_categories"][item["category"]])}</span><h2>{h(p["title"])}</h2><p>{h(p["caption"])}</p><small>© {h(item["rights"]["credit"])}</small></figcaption></figure>')
    lightbox=f'<dialog class="moment-lightbox" id="momentLightbox" aria-labelledby="momentLightboxTitle"><div class="moment-lightbox__top"><h2 id="momentLightboxTitle"></h2><button id="momentLightboxClose" type="button" aria-label="{h(c["moments_close"])}">×</button></div><figure><img id="momentLightboxImage" alt=""><figcaption id="momentLightboxCaption"></figcaption></figure></dialog>'
    body=f'<section class="section inner-page moments-page"><div class="container"><p class="eyebrow">{h(c["moments_nav"])}</p><h1>{h(c["moments_title"])}</h1><p class="page-lead">{h(c["moments_intro"])}</p><div class="moments-grid">{"".join(cards)}</div></div></section>{lightbox}'
    return shell(lang,'moments',body,f'{c["moments_title"]} | Samuel Okotako',c['moments_intro'])


def initiatives(lang):
    c=EXTRA[lang]
    cards=''.join(f'<article class="listing-card"><span class="project-category">{h(item["category"])}</span><h2>{h(item["translations"][lang]["title"])}</h2><p>{h(item["translations"][lang]["summary"])}</p></article>' for item in INITIATIVES)
    body=f'<section class="section inner-page listing-page"><div class="container"><p class="eyebrow">{h(c["initiatives_nav"])}</p><h1>{h(c["initiatives_title"])}</h1><p class="page-lead">{h(c["initiatives_intro"])}</p><div class="listing-grid">{cards}</div></div></section>'
    return shell(lang,'initiatives',body,f'{c["initiatives_title"]} | Samuel Okotako',c['initiatives_intro'])

def not_found(lang, *, root=False):
    c={**CONTENT[lang],**EXTRA[lang]}
    home_href=path(lang)
    projects_href=path(lang,'projects')
    language_links=''
    if root:
        links=''.join(f'<a href="{path(code)}" hreflang="{code}" lang="{code}">{label} ↗</a>' for code,label in [('it','Italiano'),('en','English'),('fr','Français')])
        language_links=f'<nav class="not-found-languages" aria-label="{h(c["language_label"])}">{links}</nav>'
    body=f'<section class="section not-found"><span class="not-found__numeral" aria-hidden="true">404</span><div class="container"><p class="eyebrow">404 / {h(c["not_found_title"])}</p><h1>{h(c["not_found_title"])}</h1><p>{h(c["not_found_text"])}</p><div class="hero-actions"><a class="button button--solid" href="{home_href}">{h(c["not_found_home"])} <span aria-hidden="true">↗</span></a><a class="button button--outline" href="{projects_href}">{h(c["not_found_projects"])}</a></div>{language_links}</div></section>'
    return shell(lang,'404',body,f'404 | Samuel Okotako',c['not_found_text'],not_found=True,root=root)


def root_landing():
    c=EXTRA['en']; ui=CONTENT['en']
    seo=seo_head(None,'home',c['gateway_title'],c['gateway_description'])
    cards=''.join(f'<a class="language-card" href="{code}/" data-language="{code}" hreflang="{code}" lang="{code}"><span>{code.upper()}</span><strong>{h(name)}</strong><small>{h(c[f"gateway_card_{code}"])}</small><span aria-hidden="true">↗</span></a>' for code,name in [('it','Italiano'),('en','English'),('fr','Français')])
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{h(c["gateway_title"])}</title>{seo}{early_theme()}<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="style.css"><script src="script.js" defer></script></head><body data-page="gateway"><a class="skip-link" href="#main">{h(ui["skip"])}</a><header class="site-header"><div class="container header-inner"><a class="wordmark" href="/" aria-label="SO Samuel Okotako — {h(ui["nav"][0])}"><span class="wordmark-mark" aria-hidden="true">S<span>O</span></span><span>Samuel <strong>Okotako</strong></span></a><div class="header-tools">{theme_control(ui)}</div></div></header><main id="main" class="gateway-main"><div class="container"><p class="eyebrow"><span class="eyebrow-rule"></span>{h(c["gateway_eyebrow"])}</p><h1>{h(c["gateway_heading"])}</h1><p>{h(c["gateway_intro"])}</p><p class="gateway-hint" id="languageHint" aria-live="polite" data-legacy-hint="{h(c["gateway_legacy"])}" data-suggested-template="{h(c["gateway_suggested"])}">{h(c["gateway_initial"])}</p><div class="language-grid">{cards}</div></div></main><footer class="site-footer"><div class="container footer-inner"><span>© 2026 Samuel Okotako</span><a href="en/">{h(c["gateway_enter"])} ↗</a></div></footer></body></html>'''


def root_404():
    return not_found('en', root=True)


def published_media_sources():
    sources = list(SITE_ASSETS)
    for item in PROJECTS:
        visual = PROJECT_VISUALS[item['id']]
        if visual['kind'] == 'screenshot':
            media = visual['media']
            sources.extend((media['src'], media['license_file']))
            sources.extend(media_sources_from_srcset(media['webp_srcset']))
    for media in [HOME_MEDIA['portrait'], HOME_MEDIA['creative'], *HOME_MEDIA['projects'].values()]:
        if media is None:
            continue
        sources.append(media['src'])
        for key in ('avif_srcset', 'webp_srcset', 'srcset'):
            sources.extend(media_sources_from_srcset(media.get(key, '')))
    for item in ARTICLES:
        if item['image']:
            sources.append(item['image']['src'])
            for candidate in item['image'].get('srcset', '').split(','):
                if candidate.strip():
                    sources.append(candidate.strip().split()[0])
    for item in MOMENTS:
        sources.extend(item['media'][key] for key in ('small', 'medium', 'large'))
    for item in DOCUMENTS:
        sources.append(item['file'])
    for item in GALLERIES:
        media = item['media']
        if media.get('src'):
            sources.append(media['src'])
        if media.get('poster'):
            sources.append(media['poster'])
        for candidate in media.get('srcset', '').split(','):
            if candidate.strip():
                sources.append(candidate.strip().split()[0])
    return sorted(set(sources))


def media_file(source):
    if not source.startswith('/assets/'):
        raise ValueError(f'Published media must use /assets/: {source}')
    relative = Path(source.lstrip('/'))
    original = (ROOT / relative).resolve()
    asset_root = (ROOT / 'assets').resolve()
    if asset_root not in original.parents or not original.is_file():
        raise ValueError(f'Missing or invalid published asset: {source}')
    return original, relative


def copy_published_media():
    """Copy only media referenced by published entries into the deploy output."""
    for source in published_media_sources():
        original, relative = media_file(source)
        destination = OUTPUT / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, destination)

def save(local_path, markup):
    target=OUTPUT/local_path
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(markup,encoding='utf-8')


def sitemap_paths():
    paths=['/']
    for lang in LANGS:
        paths += [path(lang,route) for route in routes()]
        paths += [path(lang,'writing',item['slug']) for item in ARTICLES]
        paths += [path(lang,'projects',item['id']) for item in PROJECT_DETAILS]
    paths += [item['file'] for item in DOCUMENTS]
    return paths



def read_redirects():
    """Allow only reviewed, exact permanent migrations; never catch missing pages."""
    source = ROOT / '_redirects'
    if not source.exists():
        return None
    rules = []
    for raw in source.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) != 3 or parts[2] != '301':
            raise ValueError(f'Invalid _redirects rule: {raw}')
        old, new, _ = parts
        if not old.startswith('/') or not new.startswith('/') or '*' in old+new or ':' in old+new:
            raise ValueError(f'Only exact local paths are allowed in _redirects: {raw}')
        if old == new:
            raise ValueError(f'Redirect to self: {raw}')
        if old in sitemap_paths():
            raise ValueError(f'Redirect source is still a published route: {raw}')
        if new.split('#',1)[0] not in sitemap_paths():
            raise ValueError(f'Redirect destination is not a published route: {raw}')
        rules.append((old,new))
    if not rules:
        raise ValueError('_redirects exists but contains no migrations')
    graph = {old:new.split('#',1)[0] for old,new in rules}
    if len(graph) != len(rules):
        raise ValueError('Duplicate _redirects source')
    for start in graph:
        seen = set()
        node = start
        while node in graph:
            if node in seen:
                raise ValueError(f'Redirect loop at {node}')
            seen.add(node)
            node = graph[node]
    return source

def main():
    validate()
    redirects = read_redirects()
    if OUTPUT.exists():
        if not (OUTPUT / '.generated-by-build-pages').exists():
            raise RuntimeError('Refusing to replace public/ without generator marker')
        shutil.rmtree(OUTPUT)  # Generated assets only; source lives outside public/.
    OUTPUT.mkdir()
    (OUTPUT / '.generated-by-build-pages').write_text('Generated by build_pages.py; edit sources outside public/.\n')
    shutil.copy2(ROOT / 'style.css', OUTPUT / 'style.css')
    shutil.copy2(ROOT / 'script.js', OUTPUT / 'script.js')
    shutil.copy2(ROOT / 'contact-form.js', OUTPUT / 'contact-form.js')
    if redirects:
        shutil.copy2(redirects, OUTPUT / '_redirects')
    builders={'home':home,'about':about,'projects':projects,'experience':experience,'contact':contact,'writing':writing,'gallery':gallery,'moments':moments,'initiatives':initiatives}
    for lang in LANGS:
        for route in routes():
            local=Path(lang)/('index.html' if route=='home' else f'{route}/index.html')
            save(local,builders[route](lang))
        save(Path(lang)/'404.html',not_found(lang))
        for item in ARTICLES:
            save(Path(lang)/'writing'/item['slug']/'index.html',article_page(lang,item))
        for item in PROJECT_DETAILS:
            save(Path(lang)/'projects'/item['id']/'index.html',project_detail(lang,item))
    copy_published_media()
    save(Path('index.html'),root_landing())
    save(Path('404.html'),root_404())
    if ORIGIN:
        urls=''.join(f'<url><loc>{h(absolute(item))}</loc></url>' for item in sitemap_paths())
        save(Path('sitemap.xml'),f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
        save(Path('robots.txt'),f'User-agent: *\nAllow: /\nSitemap: {absolute("/sitemap.xml")}\n')
    else:
        save(Path('robots.txt'),'User-agent: *\nDisallow: /\n')
    print(f'Generated {len(routes())*3+5+len(ARTICLES)*3+len(PROJECT_DETAILS)*3} HTML files; {len(PROJECTS)} projects; {len(ARTICLES)} articles; {len(GALLERIES)} gallery items; {len(MOMENTS)} moments; {len(INITIATIVES)} initiatives.')
    if not INDEXING_ENABLED:
        print('Indexing disabled: noindex; canonical, hreflang and sitemap deferred.')
    else:
        print(f'Indexing enabled for {ORIGIN}.')


if __name__=='__main__':
    main()
