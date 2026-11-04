#!/usr/bin/env python3
"""Render the approved portrait and verified positioning copy as a 1200x630 PNG.

This is an authoring helper, not a build dependency. It needs local Chrome.
"""
from base64 import b64encode
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CHROME = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
OUTPUT = ROOT / 'assets/social/samuel-okotako-og.png'


def data_url(path, mime):
    return f'data:{mime};base64,{b64encode(path.read_bytes()).decode("ascii")}'


def main():
    if not CHROME.is_file():
        raise SystemExit('Google Chrome is required to regenerate the social image')
    portrait = data_url(ROOT / 'assets/portrait/samuel-okotako.jpg', 'image/jpeg')
    display = data_url(ROOT / 'assets/fonts/newsreader-latin-400.woff2', 'font/woff2')
    body = data_url(ROOT / 'assets/fonts/manrope-latin-variable.woff2', 'font/woff2')
    html = f'''<!doctype html><html lang="en"><meta charset="utf-8"><style>
@font-face{{font-family:Newsreader;src:url({display}) format('woff2');font-weight:400}}
@font-face{{font-family:Manrope;src:url({body}) format('woff2');font-weight:400 800}}
*{{box-sizing:border-box}}html,body{{width:1200px;height:630px;margin:0;overflow:hidden}}
body{{display:grid;grid-template-columns:760px 440px;background:#f7f6f2;color:#141917;font-family:Manrope,system-ui,sans-serif}}
main{{position:relative;padding:60px 66px 52px;border-top:12px solid #172b26}}
.mark{{font-size:18px;font-weight:800;letter-spacing:.18em;color:#172b26}}
.rule{{width:54px;height:3px;margin-top:68px;background:#c6a77b}}
h1{{max-width:650px;margin:20px 0 25px;font:400 72px/.99 Newsreader,Georgia,serif;letter-spacing:-.035em}}
p{{margin:0;font-size:19px;line-height:1.45;color:#47574e}}
.domains{{position:absolute;bottom:48px;left:66px;font-size:16px;font-weight:750;letter-spacing:.035em;color:#172b26}}
aside{{position:relative;overflow:hidden;background:#b9d8c6}}
aside img{{display:block;width:100%;height:100%;object-fit:cover;object-position:center 28%}}
aside:after{{content:'';position:absolute;inset:0;border-left:8px solid #b9d8c6;pointer-events:none}}
</style><main><div class="mark">SAMUEL OKOTAKO</div><div class="rule"></div><h1>Data holds answers.<br>I turn it into value.</h1><p>Reliable systems. Responsible use of data.</p><div class="domains">DATA ENGINEERING · MACHINE LEARNING · DATA GOVERNANCE</div></main><aside><img src="{portrait}" alt="Portrait of Samuel Okotako"></aside></html>'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory() as temp:
        source = Path(temp) / 'social.html'
        source.write_text(html, encoding='utf-8')
        command = [str(CHROME), '--headless=new', '--disable-extensions', '--disable-background-networking',
                   '--no-first-run', '--no-default-browser-check', '--hide-scrollbars',
                   '--force-device-scale-factor=1', '--window-size=1200,630',
                   f'--screenshot={OUTPUT}', source.as_uri()]
        subprocess.run(command, check=True, capture_output=True, timeout=30)
    print(OUTPUT)


if __name__ == '__main__':
    main()
