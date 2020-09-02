# -*- coding: utf-8 -*-

from os import PathLike
from pathlib import Path
import pickle


def make_dirs(base_dir: str,
              dirname_template: str,
              template_kwags: str) -> str:

    base_dir = Path(base_dir)
    dirname = dirname_template.format(**template_kwags)
    dir = base_dir / dirname
    if not dir.exists():
        dir.mkdir(parents=True)

    return dir


def read_pickle(path, default):
    if not isinstance(path, (str, PathLike, bytes)):
        return default

    path = Path(path)
    if path.exists():
        with path.open('rb') as rh:
            return pickle.load(rh)
    else:
        return default


def to_pickle(obj, path):
    path = Path(path)
    parent = path.parents[0]
    if not parent.exists():
        parent.mkdir(parents=True)
    with path.open('wb') as wh:
        pickle.dump(obj, wh)
