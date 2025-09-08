import json
from collections import Counter
from typing import List, Tuple, Dict

from utils import 切


def 收缩(s) -> str:
    return (''.join([i for i in s if 'a' <= i <= 'z' or 'A' <= i <= 'Z' or '0' <= i <= '9' or '\u4e00' <= i <= '\u9fa5'])).lower()


def 分(s, 多=True) -> List[str]:
    return [i for i in filter(None, map(收缩, 切(s, 多=多))) if i not in 停词表 and len(i) <= 32]


停词表 = set()
with open('data/标点符号.json', encoding='utf8') as f:
    for i in json.load(f):
        停词表.add(i.lower())


def qs(s, w=1) -> Dict[str, float]:
    q = 分(s)
    d = {}
    n = max(8, len(q))
    for k, v in Counter(q).items():
        d[k] = min(0.2, v/n) * w
    return d


def 龙(title: str, description: str, text: str) -> List[Tuple[str, float]]:
    全词 = qs(title), qs(description, 0.5), qs(text)
    l = []
    for i in 全词:
        l += i.keys()
    vs = []
    for k in set(l):
        v = 0
        for d in 全词:
            v += d.get(k, 0)
        vs.append((k, v))
    return vs
