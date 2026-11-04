#!/usr/bin/env python3
"""Exercise local, preview and explicitly authorized production SEO modes.

All builds run in temporary copies; the real public/ tree is untouched.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://samuelokotako.com'
BRANCH = 'main'


def run_mode(name, settings, indexable):
    with TemporaryDirectory(prefix=f'portfolio-{name}-') as temp:
        site = Path(temp) / 'site'
        shutil.copytree(ROOT, site, ignore=shutil.ignore_patterns('.git', 'public', '__pycache__', '*.pyc', 'node_modules'))
        env = os.environ.copy()
        for key in ('SITE_URL', 'CF_PAGES', 'CF_PAGES_BRANCH', 'PORTFOLIO_PRODUCTION_BRANCH', 'PORTFOLIO_INDEXING'):
            env.pop(key, None)
        env.update(settings)
        for command in (('python3', '-B', 'build_pages.py'), ('python3', '-B', 'check_site.py')):
            result = subprocess.run(command, cwd=site, env=env, capture_output=True, text=True)
            if result.returncode:
                raise AssertionError(f'{name} {command[-1]} failed:\n{result.stdout}\n{result.stderr}')
        home = (site / 'public/en/index.html').read_text(encoding='utf-8')
        robots = (site / 'public/robots.txt').read_text(encoding='utf-8')
        sitemap = site / 'public/sitemap.xml'
        if indexable:
            assert f'<link rel="canonical" href="{ORIGIN}/en/">' in home
            assert f'<link rel="alternate" hreflang="x-default" href="{ORIGIN}/">' in home
            assert '<meta name="robots" content="noindex' not in home
            assert sitemap.is_file() and 'Allow: /' in robots
        else:
            assert '<meta name="robots" content="noindex' in home
            assert '<link rel="canonical"' not in home
            assert not sitemap.exists() and robots == 'User-agent: *\nDisallow: /\n'
        print(f'OK: {name} ({"indexable" if indexable else "noindex"})')


def main():
    run_mode('local', {'SITE_URL': ORIGIN}, False)
    run_mode('preview', {
        'SITE_URL': ORIGIN, 'CF_PAGES': '1', 'CF_PAGES_BRANCH': 'preview-branch',
        'PORTFOLIO_PRODUCTION_BRANCH': BRANCH, 'PORTFOLIO_INDEXING': 'enabled',
    }, False)
    run_mode('former-production-branch', {
        'SITE_URL': ORIGIN, 'CF_PAGES': '1', 'CF_PAGES_BRANCH': 'feature/portfolio-v2',
        'PORTFOLIO_PRODUCTION_BRANCH': BRANCH, 'PORTFOLIO_INDEXING': 'enabled',
    }, False)
    run_mode('public-simulation', {
        'SITE_URL': ORIGIN, 'CF_PAGES': '1', 'CF_PAGES_BRANCH': BRANCH,
        'PORTFOLIO_PRODUCTION_BRANCH': BRANCH, 'PORTFOLIO_INDEXING': 'enabled',
    }, True)
    run_cv_fixture()


def run_cv_fixture():
    """Test the hidden-until-approved CV component with temporary fake PDFs."""
    with TemporaryDirectory(prefix='portfolio-cv-fixture-') as temp:
        site = Path(temp) / 'site'
        shutil.copytree(ROOT, site, ignore=shutil.ignore_patterns('.git', 'public', '__pycache__', '*.pyc', 'node_modules'))
        documents = []
        for lang in ('it', 'en'):
            asset = site / f'assets/docs/cv-{lang}.pdf'
            asset.parent.mkdir(parents=True, exist_ok=True)
            asset.write_bytes(b'%PDF-1.4\n% Temporary test fixture only\n%%EOF\n')
            documents.append({
                'status': 'published', 'slug': f'cv-{lang}', 'kind': 'cv', 'language': lang,
                'file': f'/assets/docs/cv-{lang}.pdf', 'updated': '2026-11-03',
                'approval': {'owner': True, 'privacy_reviewed': True},
                'translations': {code: {'title': f'CV {lang.upper()}', 'description': 'Temporary test fixture'} for code in ('it', 'en', 'fr')},
            })
        register = site / 'content/documents.json'
        register.write_text(json.dumps(documents), encoding='utf-8')
        env = os.environ.copy()
        for key in ('SITE_URL', 'CF_PAGES', 'CF_PAGES_BRANCH', 'PORTFOLIO_PRODUCTION_BRANCH', 'PORTFOLIO_INDEXING'):
            env.pop(key, None)
        for command in (('python3', '-B', 'build_pages.py'), ('python3', '-B', 'check_site.py')):
            result = subprocess.run(command, cwd=site, env=env, capture_output=True, text=True)
            if result.returncode:
                raise AssertionError(f'CV fixture failed:\n{result.stdout}\n{result.stderr}')
        for lang, pdf, label in (('it', 'cv-it.pdf', 'Scarica il CV'), ('en', 'cv-en.pdf', 'Download resume'), ('fr', 'cv-en.pdf', 'Télécharger mon CV')):
            home = (site / f'public/{lang}/index.html').read_text(encoding='utf-8')
            assert f'href="/assets/docs/{pdf}" type="application/pdf" download>{label}' in home
        documents[1]['status'] = 'draft'
        register.write_text(json.dumps(documents), encoding='utf-8')
        result = subprocess.run(('python3', '-B', 'build_pages.py'), cwd=site, env=env, capture_output=True, text=True)
        assert result.returncode != 0 and 'Public CV requires one approved IT PDF' in result.stderr, 'Partial CV pair was accepted'
        documents[0]['status'] = 'draft'
        register.write_text(json.dumps(documents), encoding='utf-8')
        result = subprocess.run(('python3', '-B', 'build_pages.py'), cwd=site, env=env, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        for lang in ('it', 'en', 'fr'):
            assert 'home-contact__cv' not in (site / f'public/{lang}/index.html').read_text(encoding='utf-8')
        print('OK: CV download appears only with both approved IT/EN PDFs (temporary fixture)')


if __name__ == '__main__':
    main()
