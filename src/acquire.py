"""Download the original public Kaggle archive; never read or store credentials."""
from pathlib import Path
import hashlib
import json
import zipfile
import requests

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://www.kaggle.com/api/v1/datasets/download/olistbr/brazilian-ecommerce'
FILES = {f'olist_{x}_dataset.csv' for x in ['orders','order_items','order_payments','order_reviews','customers','products','sellers','geolocation']} | {'product_category_name_translation.csv'}

def acquire():
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    archive = ROOT / 'data.zip'
    if not FILES.issubset({p.name for p in raw.glob('*.csv')}):
        if not archive.exists():
            with requests.get(URL, stream=True, timeout=(20, 180)) as r:
                r.raise_for_status()
                with archive.open('wb') as out:
                    for chunk in r.iter_content(1024 * 1024):
                        out.write(chunk)
        if not zipfile.is_zipfile(archive):
            raise RuntimeError('Kaggle did not return a ZIP. See docs/REPRODUCE.md for authenticated download.')
        with zipfile.ZipFile(archive) as z:
            for name in FILES:
                matches = [p for p in z.namelist() if Path(p).name == name]
                if len(matches) != 1:
                    raise RuntimeError(f'Expected exactly one {name}')
                with z.open(matches[0]) as src, (raw / name).open('wb') as dst:
                    while chunk := src.read(1024 * 1024):
                        dst.write(chunk)
    manifest = {'source': URL, 'dataset': 'olistbr/brazilian-ecommerce', 'files': {}}
    for name in sorted(FILES):
        p = raw / name
        manifest['files'][name] = {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
    (ROOT / 'reports').mkdir(exist_ok=True)
    (ROOT / 'reports/source_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Verified all nine source CSV files; manifest written.')

if __name__ == '__main__':
    acquire()
