#!/usr/bin/env python3
"""Prepare metadata-free WebP variants for a reviewed Life & Moments photo.

Build-time utility for macOS with sips and cwebp; HEIC also needs heif-convert.
It never edits the source and does not add an item to content/moments.json.
"""
import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def dimensions(source):
    result = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', str(source)], check=True, capture_output=True, text=True)
    width = re.search(r'pixelWidth: (\d+)', result.stdout)
    height = re.search(r'pixelHeight: (\d+)', result.stdout)
    if not width or not height:
        raise RuntimeError(f'Cannot read image dimensions: {source}')
    return int(width.group(1)), int(height.group(1))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path, help='Original image, kept unchanged')
    parser.add_argument('slug', help='Stable lowercase URL slug')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'assets' / 'moments')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', args.slug):
        parser.error('Slug must contain lowercase letters, digits and hyphens')
    if not args.source.is_file():
        parser.error('Source image does not exist')
    required = ['sips', 'cwebp'] + (['heif-convert'] if args.source.suffix.lower() in ('.heic', '.heif') else [])
    missing = [name for name in required if not shutil.which(name)]
    if missing:
        parser.error('Missing image tools: ' + ', '.join(missing))
    with tempfile.TemporaryDirectory() as temporary:
        intermediate = Path(temporary) / 'normalized.jpg'
        if args.source.suffix.lower() in ('.heic', '.heif'):
            run('heif-convert', str(args.source), str(intermediate))
        else:
            run('sips', '-s', 'format', 'jpeg', str(args.source), '--out', str(intermediate))
        original_width, original_height = dimensions(intermediate)
        widths = {label: min(original_width, limit) for label, limit in (('small', 640), ('medium', 1200), ('large', 1800))}
        if not args.output_dir.exists():
            args.output_dir.mkdir(parents=True)
        filenames = {width: f'{args.slug}-{width}.webp' for width in set(widths.values())}
        targets = [args.output_dir / name for name in filenames.values()]
        if any(target.exists() for target in targets):
            parser.error('A variant already exists; choose a new slug or review it manually')
        for width, name in sorted(filenames.items()):
            run('cwebp', '-quiet', '-q', '78', '-m', '6', '-resize', str(width), '0', '-metadata', 'none', str(intermediate), '-o', str(args.output_dir / name))
        media = {label: '/assets/moments/' + filenames[width] for label, width in widths.items()}
        media.update(small_width=widths['small'], medium_width=widths['medium'], width=widths['large'], height=round(original_height * widths['large'] / original_width))
        print(json.dumps(media, ensure_ascii=False, indent=2))
        print('Prepared variants only. Review image, captions, rights and publication approvals before setting status=published.')


if __name__ == '__main__':
    main()
