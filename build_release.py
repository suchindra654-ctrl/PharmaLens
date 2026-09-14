"""Create a portable source bundle without credentials, accounts or caches."""
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    files = list(root.glob('*.py')) + list((root / 'tests').glob('test_*.py'))
    files += [root / name for name in ('RELEASE_GUIDE.md', 'EVALUATION.md', 'setup.ps1',
              'requirements.txt', 'requirements.lock.txt', 'run.ps1', '.env.example', '.gitignore',
              '.streamlit/config.toml', 'data/catalog.json', 'data/manifest.json')]
    files += [root / 'data' / item['file'] for item in json.loads((root / 'data/catalog.json').read_text())]
    files += list((root / 'evaluation').glob('*.json'))
    destination = root / 'dist' / 'PharmaLens-Evaluated.zip'
    destination.parent.mkdir(exist_ok=True)
    with ZipFile(destination, 'w', ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, 'PharmaLens/' + path.relative_to(root).as_posix())
    with ZipFile(destination) as archive:
        assert archive.testzip() is None
        assert not any('/.local/' in name or name.endswith('/.env') for name in archive.namelist())
    print(f'{destination.name}: {len(files)} files, {destination.stat().st_size / 1048576:.2f} MB')
    update = root / 'dist' / 'PharmaLens-UI-Update.zip'
    with ZipFile(update, 'w', ZIP_DEFLATED) as archive:
        for path in files:
            relative = path.relative_to(root)
            if relative.parts[0] in ('data', '.streamlit') or relative.name in ('.env.example', '.gitignore'):
                continue
            archive.write(path, 'PharmaLens/' + relative.as_posix())
    with ZipFile(update) as archive:
        assert archive.testzip() is None
    print(f'{update.name}: code and instructions only; existing accounts, settings and PDFs preserved')
