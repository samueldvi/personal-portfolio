#!/usr/bin/env python3
"""Regression checks for the metadata gate, using local synthetic fixtures only."""
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
from check_public_safety import RAW_ORIGINAL, embedded_image_metadata


def check():
    with TemporaryDirectory() as directory:
        root = Path(directory)
        examples = {
            'clean.jpg': (b'\xff\xd8\xff\xe0\x00\x02\xff\xda\x00\x02\x00', set()),
            'with-exif.jpg': (b'\xff\xd8\xff\xe1\x00\x08Exif\x00\x00\xff\xda\x00\x02\x00', {'EXIF/XMP'}),
            'with-exif.png': (b'\x89PNG\r\n\x1a\n' + b'\x00\x00\x00\x00eXIf\x00\x00\x00\x00', {'eXIf'}),
            'with-xmp.webp': (b'RIFF\x08\x00\x00\x00WEBPXMP \x00\x00\x00\x00', {'XMP'}),
        }
        for name, (data, expected) in examples.items():
            path = root / name
            path.write_bytes(data)
            actual = embedded_image_metadata(path)
            assert actual == expected, f'{name}: expected metadata category {expected}, got {actual}'
    assert RAW_ORIGINAL.fullmatch('IMG_5750.JPG')
    assert not RAW_ORIGINAL.fullmatch('approved-portrait.jpg')
    repository = Path(__file__).resolve().parents[1]
    assert subprocess.run(['git', 'check-ignore', '-q', '--', 'editorial/.env.local'],
                          cwd=repository, check=False).returncode == 0
    assert subprocess.run(['git', 'ls-files', '--error-unmatch', 'editorial/.env.local'],
                          cwd=repository, check=False, capture_output=True).returncode != 0
    print('OK: metadata gate recognizes clean and tagged JPEG, PNG and WebP fixtures.')


if __name__ == '__main__':
    check()
