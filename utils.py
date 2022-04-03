import re
import json
import logging
import threading
from functools import lru_cache
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, Tuple

from tqdm import tqdm
import jieba as jiba
import fasttext

from 类 import 阵


# urllib.parse.urlparse太慢了！
def netloc(url: str) -> str:
    try:
        return re.findall('//(.*?)(?=/|\?|$)', url)[0]
    except Exception:
        return urlparse(url).netloc


# 节省内存的魔法
_fl = lru_cache(maxsize=100000)(float)
def json_loads(s):
    return json.loads(s, parse_float=_fl)


# concurrent.futures.ThreadPoolExecutor.map 会占用大量不必要的内存
class 好ThreadPoolExecutor(ThreadPoolExecutor):
    _nothing = object()
    def map(self, fn, *iterables):
        lock = threading.Lock()
        z = [*zip(*iterables)][::-1]
        res = [好ThreadPoolExecutor._nothing] * len(z)
        def gf():
            with lock:
                if z:
                    zz = z.pop()
                    f = self.submit(fn2, *zz)
                    res[len(z)] = f
        def fn2(*li, **d):
            res = fn(*li, **d)
            gf()
            return res
        for _ in range(min(len(z), self._max_workers)):
            gf()
        def result_iterator():
            nonlocal z
            try:
                while res:
                    yield res.pop().result()
            finally:
                with lock:
                    z = []
                    for fs in res:
                        if fs is not 好ThreadPoolExecutor._nothing:
                            fs.cancel()
        return result_iterator()


def 小小清洗(q: 阵, l: int) -> Iterable[Tuple[float, str]]:
    def 好(url: str):
        if url.startswith('https://'):
            url = url[8:]
        return len(url.rstrip('/').split('/')) == 1
    y = {}
    for v, url in q:
        s = netloc(url).lower()
        if y.setdefault(s, 0) >= l and not 好(url):
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


_tl = {}
def tqdm_exception_logger(e):
    s = type(e).__name__
    if s not in _tl:
        _tl[s] = tqdm(desc=f'{s}', ncols=60)
    _tl[s].update(1)


def 坏(url: str) -> float:
    s = max(0, (len(url)-30)/250)
    if '.htm' in url or '.php' in url:
        s += 0.3
    if len(url.rstrip('/').split('/')) > 3:
        s += 0.2
    s = min(s, 0.9)
    return s


lang_model = fasttext.load_model('lid.176.ftz')
def 检测语言(s: str) -> str:
    lang = lang_model.predict(s)[0][0]
    assert lang.startswith('__label__')
    return lang[9:]


def 分解(url: str):
    if url.startswith('https://'):
        url = url[8:]
    elif url.startswith('http://'):
        url = url[7:]
    else:
        return
    url = url.replace('?', '/')
    url = url.replace('#', '/')
    if url.endswith('/'):
        url = url[:-1]
    if not url or url[0] in ' /%':
        return
    sp = url.split('/')
    s = sp[0]
    yield s
    for i in sp[1:]:
        s = f'{s}/{i}'
        yield s
