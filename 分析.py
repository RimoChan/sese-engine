import json
from collections import Counter
from typing import List, Tuple

from utils import 切


def 收缩(s):
    return (''.join([i for i in s if 'a' <= i <= 'z' or 'A' <= i <= 'Z' or '0' <= i <= '9' or '\u4e00' <= i <= '\u9fa5'])).lower()


def 分(s, 多=True):
    return [i for i in filter(None, map(收缩, 切(s, 多=多))) if i not in 停词表 and len(i) <= 32]


停词表 = set()
with open('data/标点符号.json', encoding='utf8') as f:
    for i in json.load(f):
        停词表.add(i.lower())
with open('data/en_stopwords.json', encoding='utf8') as f:
    for i in json.load(f):
        停词表.add(i.lower())


def qs(s):
    q = 分(s)
    d = {}
    n = max(8, len(q))
    for k, v in Counter(q).items():
        d[k] = min(0.2, v/n)
    return d


def 龙(title: str, description: str, text: str) -> List[Tuple[str, float]]:
    全词 = qs(title), qs(description), qs(text)
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
