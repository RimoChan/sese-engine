import re
import os
import json
import logging
import traceback
import threading
from functools import lru_cache
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, Tuple

import lxml.html
import jieba as jiba
from tqdm import tqdm

from 类 import 阵


# urllib.parse.urlparse太慢了！
def netloc(url: str) -> str:
    try:
        l = url.split('/')
        a = l[2]
        assert '?' not in a and ' ' not in a and l[0] in ('http:', 'https:') and l[1] == ''
        return a
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


jiba.setLogLevel(logging.INFO)
def 切(s: str, 多=False):
    s = s[:10000]
    if 多:
        return jiba.lcut_for_search(s)
    else:
        return jiba.lcut(s)


_tl = {}
def tqdm_exception_logger(e, log_path=None):
    c = type(e)
    s = c.__name__
    if c.__module__ != 'builtins':
        s = c.__module__ + '.' + s
    try:
        f = e.__traceback__.tb_frame.f_globals["__file__"]
        l = e.__traceback__.tb_lineno
        s = f'[{f}:{l}]{s}'
    except Exception:
        None
    if s not in _tl:
        _tl[s] = tqdm(desc=f'{s}', ncols=60)
    _tl[s].update(1)
    if log_path:
        pid = os.getpid()
        filename = f'{log_path}/{pid}.log'
        try:
            with open(filename, 'a', encoding='utf8') as f:
                f.write('='*20+'\n'+''.join(traceback.format_exception(type(e), e, e.__traceback__)))
            if os.path.getsize(filename) > 50 * 1024 * 1024:
                os.remove(filename)
        except Exception as e:
            print(f'log failed {e}!')


def 坏(url: str) -> float:
    s = max(0, (len(url)-30)/200)
    if '.htm' in url or '.php' in url:
        s += (1-s) * 0.3
    if url.rstrip('/').count('/') > 2:
        s += (1-s) * 0.1
    if len(url) < 5 or url[4] == ':':     # startswith http:
        s += (1-s) * 0.3
    s = min(s, 0.9)
    return s


_lang_model = None
def 检测语言(s: str) -> str:
    global _lang_model
    if not _lang_model:
        import fasttext
        try:
            fasttext.FastText.eprint = lambda *args, **kwargs: None      # fasttext的警告居然关不掉
        except Exception:
            None
        _lang_model = fasttext.load_model('lid.176.ftz')
    lang = _lang_model.predict(s.replace('\n', ''))[0][0]
    assert lang.startswith('__label__')
    return lang[9:]


def 分解(url: str):
    url = url.lower()
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


_压缩 = {'div': 0, 'meta': 1, 'script': 2, 'link': 3, 'h2': 4, 'h3': 5, 'td': 6, 'input': 7, 'source': 8, 'dd': 9, 'label': 10, 'nav': 11, 'picture': 12, 'section': 13, 'button': 14, 'dt': 15, 'form': 16, 'dl': 17, 'head': 18, 'body': 19, 'html': 20, 'title': 21, 'tr': 22, 'code': 23, 'style': 24, 'strong': 25, 'h4': 26, 'i': 27, 'table': 28, 'em': 29, 'h1': 30, 'noscript': 31, 'header': 32, 'video': 33, 'footer': 34, 'b': 35, 'iframe': 36, 'tbody': 37, 'template': 38, 'hr': 39, 'pre': 40, 'small': 41, 'figure': 42, 'center': 43, 'main': 44, 'th': 45, 'h5': 46, 'h6': 47, 'fieldset': 48, 'article': 49, 'var': 50, 'option': 51, 'select': 52, 'font': 53, 'ol': 54, 'legend': 55, 'track': 56, 'aside': 57, 's': 58, 'blockquote': 59, 'area': 60, 'base': 61, 'map': 62, 'textarea': 63, 'big': 64}
def html结构特征(raw: str) -> str:
    if not raw:
        return ''
    root = lxml.html.document_fromstring(raw)
    j_root = []
    def dfs(r: lxml.html.HtmlElement, now):
        for x in r:
            if x.tag in ('a', 'p', 'li', 'ul', 'span', 'img', 'br', 'svg') or not isinstance(x.tag, str):
                continue
            c = []
            z = _压缩.get(x.tag, x.tag)
            now.append((z, c))
            dfs(x, c)
            if now[-1][1] == []:
                now[-1] = z
    dfs([root], j_root)
    return json.dumps(j_root, separators=(',', ':'))[:512]
