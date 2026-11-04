"""Load and validate the three locale dictionaries used by shared templates."""
from pathlib import Path
import json

LANGS = ('it', 'en', 'fr')
DIRECTORY = Path(__file__).resolve().parent / 'translations'


def load_locale(lang):
    bundle = json.loads((DIRECTORY / f'{lang}.json').read_text(encoding='utf-8'))
    if not isinstance(bundle, dict) or set(bundle) != {'content', 'extra', 'cases'}:
        raise ValueError(f'{lang}: expected content, extra and cases dictionaries')
    if not all(isinstance(bundle[key], dict) for key in ('content', 'extra', 'cases')):
        raise ValueError(f'{lang}: translation sections must be dictionaries')
    return bundle


BUNDLES = {lang: load_locale(lang) for lang in LANGS}
for section in ('content', 'extra', 'cases'):
    reference = set(BUNDLES['it'][section])
    for lang in LANGS:
        keys = set(BUNDLES[lang][section])
        if keys != reference:
            raise ValueError(f'{lang}: {section} translation keys differ; missing={reference-keys}, extra={keys-reference}')
        if any(value is None or value == '' for value in BUNDLES[lang][section].values()):
            raise ValueError(f'{lang}: {section} contains an empty translation')

CONTENT = {lang: BUNDLES[lang]['content'] for lang in LANGS}
EXTRA = {lang: BUNDLES[lang]['extra'] for lang in LANGS}
CASE_STUDIES = {lang: BUNDLES[lang]['cases'] for lang in LANGS}
if any(set(CASE_STUDIES[lang]) != set(CASE_STUDIES['it']) for lang in LANGS):
    raise ValueError('Case study IDs differ across translations')
for case_id in CASE_STUDIES['it']:
    reference = set(CASE_STUDIES['it'][case_id])
    for lang in LANGS:
        if set(CASE_STUDIES[lang][case_id]) != reference:
            raise ValueError(f'{lang}: case study fields differ for {case_id}')
for lang, copy in CONTENT.items():
    if len(copy['nav']) != 5 or len(copy['theme_options']) != 3:
        raise ValueError(f'{lang}: navigation/theme option count is inconsistent with shared components')
    if {key for key, _ in copy['filters']} != {key for key, _ in CONTENT['it']['filters']}:
        raise ValueError(f'{lang}: project filter keys differ')
    if len(copy['about_languages']) != 3 or any(not isinstance(item, str) or not item.strip() for item in copy['about_languages']):
        raise ValueError(f'{lang}: expected three language skills')
    if len(copy['focus']) != 3 or any(len(item) != 4 or not all(item) for item in copy['focus']):
        raise ValueError(f'{lang}: expected three complete homepage skill entries')
    if [item[3] for item in copy['focus']] != ['engineering', 'machine-learning', 'governance']:
        raise ValueError(f'{lang}: homepage skills must map to the same project categories')

for lang in LANGS:
    if set(EXTRA[lang]['moment_categories']) != set(EXTRA['it']['moment_categories']):
        raise ValueError(f'{lang}: Life & Moments category keys differ')
