import re
import json
import logging
from functools import lru_cache
from urllib.parse import urlparse
from typing import Iterable, Tuple

import jieba as jiba

from 类 import 阵


# urllib.parse.urlparse太慢了！
def netloc(url: str) -> str:
    try:
        return re.findall('//(.*?)(?=/|\?|$)', url)[0]
    except Exception:
        logging.warning(f'解析{repr(url)}居然失败了！')
        return urlparse(url).netloc


# 节省内存的魔法
_fl = lru_cache(maxsize=100000)(float)
def json_loads(s):
    return json.loads(s, parse_float=_fl)


def 小小清洗(q: 阵, l: int) -> Iterable[Tuple[float, str]]:
    y = {}
    for v, url in q:
        if '\n' in url:     # 我也不知道为什么会有这个，扫一段时间之后去掉吧
            url = url.replace('\n', '')
        s = netloc(url)
        if y.setdefault(s, 0) >= l:
            continue
        y[s] += 1
        yield v, url


def 小清洗(q: 阵, l: int) -> 阵:
    return [*小小清洗(q, l)]


def 切(s: str, 多=False):
    s = s[:10000]
    if 多:
        return jiba.lcut_for_search(s)
    else:
        return jiba.lcut(s)
