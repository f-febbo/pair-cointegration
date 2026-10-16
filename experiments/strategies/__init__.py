"""Discover only strategy families installed in this checkout."""
from importlib import import_module
from pathlib import Path

def specifications():
    result=[]
    for path in sorted(Path(__file__).parent.glob('*.py')):
        if not path.name.startswith('_'):
            result.extend(import_module(f'{__name__}.{path.stem}').specifications())
    return result
