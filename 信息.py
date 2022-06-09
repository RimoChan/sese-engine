import json
from pathlib import Path

import yaml

from 配置 import 存储位置


def _归1化(d):
    q = [v for k, v in d.items() if '/' not in k]
    总能量 = sum(q)
    倍 = 200000/总能量
    return {k: v*倍 for k, v in d.items()}


def 繁荣表() -> dict:
    if not (存储位置/'繁荣.json').is_file():
        return {}
    with open(存储位置/'繁荣.json', encoding='utf8') as f:
        d = json.load(f)
    d = _归1化(d)
    for k, v in d.items():
        now = k
        while True:
            now = '.'.join(now.split('.')[1:])
            if now not in d:
                break
            if d[now] < v:
                d[now] = v
    return d


def 调整表() -> dict:
    if not (Path('./data')/'调整.yaml').is_file():
        return {}
    with open(Path('./data')/'调整.yaml', encoding='utf8') as f:
        return yaml.safe_load(f)


def 屏蔽词() -> set:
    path = Path('./data')/'屏蔽词.json'
    if not path.is_file():
        return []
    return {*json.load(open(path, encoding='utf8'))}
