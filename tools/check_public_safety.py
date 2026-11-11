#!/usr/bin/env python3
"""Fail CI on obvious private artifacts or high-confidence credentials.

This is a preventive repository check, not a substitute for manual review or
GitHub secret scanning. It never prints a matched secret.
"""
from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {'.py', '.js', '.cjs', '.html', '.css', '.md', '.json', '.yaml', '.yml', '.txt', '.svg', '.sh'}
PRIVATE_SUFFIXES = {'.pem', '.p12', '.pfx', '.key', '.sqlite', '.sqlite3', '.db', '.csv', '.tsv', '.xlsx', '.xls', '.log', '.bak', '.tmp', '.zip'}
RAW_ORIGINAL = re.compile(r'^IMG_.*\.(?:heic|jpe?g|png)$', re.I)
PRIVATE_NAME = re.compile(r'passport|passaporto|carta.?identit|tessera.?sanitaria|codice.?fiscale|(^|[_-])iban([_.-]|$)|contratto|bank.?statement', re.I)
SECRETS = {
    'private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'AWS access key': re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'GitHub token': re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b'),
    'Slack token': re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{20,}\b'),
}


def embedded_image_metadata(file):
    """Return metadata container names without reading or reporting their values."""
    data = file.read_bytes()
    found = set()
    if file.suffix.lower() in {'.jpg', '.jpeg'} and data.startswith(b'\xff\xd8'):
        offset = 2
        while offset + 4 <= len(data) and data[offset] == 0xff:
            marker = data[offset + 1]
            if marker == 0xda:  # Entropy-coded image data begins here.
                break
            size = int.from_bytes(data[offset + 2:offset + 4], 'big')
            if size < 2 or offset + 2 + size > len(data):
                break
            if marker == 0xe1:
                found.add('EXIF/XMP')
            elif marker == 0xed:
                found.add('IPTC')
            elif marker == 0xfe:
                found.add('comment')
            offset += 2 + size
    elif file.suffix.lower() == '.png' and data.startswith(b'\x89PNG\r\n\x1a\n'):
        offset = 8
        while offset + 12 <= len(data):
            size = int.from_bytes(data[offset:offset + 4], 'big')
            kind = data[offset + 4:offset + 8]
            if kind in {b'eXIf', b'tEXt', b'zTXt', b'iTXt', b'tIME'}:
                found.add(kind.decode('ascii'))
            offset += 12 + size
    elif file.suffix.lower() == '.webp' and data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        offset = 12
        while offset + 8 <= len(data):
            kind = data[offset:offset + 4]
            size = int.from_bytes(data[offset + 4:offset + 8], 'little')
            if kind in {b'EXIF', b'XMP '}:
                found.add(kind.decode('ascii').strip())
            offset += 8 + size + size % 2
    return found


def check():
    issues = []
    documents = json.loads((ROOT / 'content/documents.json').read_text(encoding='utf-8'))
    approved_pdfs = set()
    tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0'))
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
        # The local editor config is deliberately outside Git and the public build.
        # Never read or report its contents; a tracked or unignored copy still fails.
        if label == 'editorial/.env.local':
            ignored = subprocess.run(['git', 'check-ignore', '-q', '--', label], cwd=ROOT,
                                     check=False).returncode == 0
            if ignored and label not in tracked:
                continue
        suffix = file.suffix.lower()
        safe_example = file.name == '.env.example' and all(
            not line.strip() or line.lstrip().startswith('#') or re.fullmatch(r'[A-Z][A-Z0-9_]*=', line.strip())
            for line in file.read_text(encoding='utf-8').splitlines()
        )
        if PRIVATE_NAME.search(file.name) or suffix in PRIVATE_SUFFIXES or (file.name.startswith('.env') and not safe_example):
            issues.append(f'Private artifact name or type: {label}')
        if label in tracked and (RAW_ORIGINAL.fullmatch(file.name) or suffix == '.heic' or file.name == '.DS_Store'):
            issues.append(f'Raw or local-only artifact tracked by Git: {label}')
        if suffix in {'.jpg', '.jpeg', '.png', '.webp'} and (relative.parts[0] == 'assets' or relative.parts[:2] == ('public', 'assets') or label == 'samuel-profile.jpg'):
            metadata = embedded_image_metadata(file)
            if metadata:
                issues.append(f'Embedded image metadata in {label}: {", ".join(sorted(metadata))}')
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
