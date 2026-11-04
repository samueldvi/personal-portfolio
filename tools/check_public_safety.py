#!/usr/bin/env python3
"""Fail CI on obvious private artifacts or high-confidence credentials.

This is a preventive repository check, not a substitute for manual review or
GitHub secret scanning. It never prints a matched secret.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {'.py', '.js', '.cjs', '.html', '.css', '.md', '.json', '.yaml', '.yml', '.txt', '.svg', '.sh'}
PRIVATE_SUFFIXES = {'.pem', '.p12', '.pfx', '.key', '.sqlite', '.sqlite3', '.db', '.csv', '.tsv', '.xlsx', '.xls'}
PRIVATE_NAME = re.compile(r'passport|passaporto|carta.?identit|tessera.?sanitaria|codice.?fiscale|(^|[_-])iban([_.-]|$)|contratto|bank.?statement', re.I)
SECRETS = {
    'private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'AWS access key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'GitHub token': re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b'),
    'Slack token': re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{20,}\b'),
}


def check():
    issues = []
    documents = json.loads((ROOT / 'content/documents.json').read_text(encoding='utf-8'))
    approved_pdfs = set()
    for item in documents:
        approval = item.get('approval') or {}
        source = str(item.get('source') or item.get('file') or '').lstrip('/')
        public_path = str(item.get('file') or '').lstrip('/')
        if item.get('status') == 'published' and approval.get('owner') is True and approval.get('privacy_reviewed') is True and source.endswith('.pdf') and public_path.endswith('.pdf'):
            approved_pdfs.update((source, 'public/' + public_path))
    files = (path for path in ROOT.rglob('*') if path.is_file() and not any(part in {'.git', '__pycache__', 'node_modules'} for part in path.relative_to(ROOT).parts))
    for file in files:
        relative = file.relative_to(ROOT)
        label = str(relative)
        suffix = file.suffix.lower()
        if PRIVATE_NAME.search(file.name) or suffix in PRIVATE_SUFFIXES or file.name.startswith('.env'):
            issues.append(f'Private artifact name or type: {label}')
        if suffix == '.pdf' and label not in approved_pdfs:
            issues.append(f'PDF needs an explicit privacy and publication review: {label}')
        if relative.parts[0] == 'public' and (suffix not in {'.html', '.css', '.js', '.svg', '.webp', '.jpg', '.jpeg', '.png', '.woff2', '.txt', '.xml', '.pdf'} and file.name not in {'.generated-by-build-pages', '_redirects'}):
            issues.append(f'Unexpected public asset type: {label}')
        if suffix in TEXT_SUFFIXES and file.stat().st_size < 2_000_000:
            text = file.read_text(encoding='utf-8', errors='replace')
            for kind, pattern in SECRETS.items():
                if pattern.search(text):
                    issues.append(f'Possible {kind} in {label}')
    if issues:
        for issue in sorted(set(issues)):
            print(f'FAIL: {issue}', file=sys.stderr)
        return 1
    print('OK: no obvious private artifacts or high-confidence credentials in source/public files.')
    return 0


if __name__ == '__main__':
    raise SystemExit(check())
