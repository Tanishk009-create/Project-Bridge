"""Package source only. Run using the backend virtual environment's Python."""
from pathlib import Path
import hashlib
import json
import os
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT.parent / 'Project-Bridge-Integrated.zip'
SKIP_DIRS = {'.git', 'node_modules', '.venv', '__pycache__', '.pytest_cache', '.test-tmp', '.npm-cache', '.tmp', 'logs'}

def excluded(path):
    name = path.name
    return name == 'PACKAGE-MANIFEST.json' or (name.startswith('.env') and name != '.env.example') or name.endswith(('.pyc', '.tsbuildinfo', '.db', '.db-wal', '.db-shm', '.db-journal', '.log'))

files = []
for current, directories, names in os.walk(ROOT):
    directories[:] = sorted(d for d in directories if d not in SKIP_DIRS and not d.startswith('.next'))
    for name in sorted(names):
        file = Path(current) / name
        if not excluded(file) and not file.is_symlink():
            files.append(file)

manifest = [{'path': str(file.relative_to(ROOT)).replace('\\', '/'), 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()} for file in files]
with zipfile.ZipFile(TARGET, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for file in files:
        archive.write(file, 'bridge-integrated/' + file.relative_to(ROOT).as_posix())
    archive.writestr('bridge-integrated/PACKAGE-MANIFEST.json', json.dumps(manifest, indent=2))
with zipfile.ZipFile(TARGET) as archive:
    assert archive.testzip() is None
    for record in manifest:
        assert hashlib.sha256(archive.read('bridge-integrated/' + record['path'])).hexdigest() == record['sha256']
checksum = hashlib.sha256(TARGET.read_bytes()).hexdigest()
TARGET.with_suffix('.zip.sha256').write_text(f'{checksum}  {TARGET.name}\n', encoding='utf-8')
print(f'Packaged {len(files)} source files: {TARGET} ({TARGET.stat().st_size:,} bytes)')
print(f'SHA-256: {checksum}')
