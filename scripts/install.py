#!/usr/bin/env python3
"""Install the seven skill directories without overwriting existing skills."""
import argparse
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('geoscience-paper-writing', 'sedimentary-geology-zh', 'sedimentary-geology-en',
         'geophysics-zh', 'geophysics-en', 'unconventional-petroleum-zh', 'unconventional-petroleum-en')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    default = Path(os.environ.get('CODEX_HOME') or (Path.home() / '.codex')) / 'skills'
    parser.add_argument('--destination', type=Path, default=default)
    args = parser.parse_args()
    target = args.destination.expanduser()
    existing = [str(target / name) for name in NAMES if (target / name).exists()]
    if existing:
        print('Installation stopped: these skills already exist:', file=sys.stderr)
        print('\n'.join(existing), file=sys.stderr)
        return 1
    if any(not (ROOT / 'skills' / name / 'SKILL.md').is_file() for name in NAMES):
        print('Installation stopped: source skill bundle is incomplete.', file=sys.stderr)
        return 1
    target.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        shutil.copytree(ROOT / 'skills' / name, target / name,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    print(f'Installed {len(NAMES)} skills to {target}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
