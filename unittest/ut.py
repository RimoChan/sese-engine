from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))
import os
os.chdir('..')

import re
import json
import time
import random
from urllib.parse import urlparse

import lzma
import jieba
from tqdm import tqdm

from utils import netloc, 分解
from 存储 import dump2, load
from 分析 import 收缩, 停词表, 分
from 文 import 摘要


with lzma.open('unittest/urls.json.xz', 'rt') as f:
    urls = json.loads(f.read())


def 测分解():
    assert \
        [*分解('https://docs.python.org/zh-cn/3/library/random.html')] == \
        [*分解('http://docs.python.org/zh-cn/3/library/random.html')] == \
        ['docs.python.org', 'docs.python.org/zh-cn', 'docs.python.org/zh-cn/3', 'docs.python.org/zh-cn/3/library', 'docs.python.org/zh-cn/3/library/random.html']
    assert \
        [*分解('https://docs.python.org/zh-cn/3/library/stdtypes.html#str.split')] == \
        [*分解('http://docs.python.org/zh-cn/3/library/stdtypes.html#str.split')] == \
        ['docs.python.org', 'docs.python.org/zh-cn', 'docs.python.org/zh-cn/3', 'docs.python.org/zh-cn/3/library', 'docs.python.org/zh-cn/3/library/stdtypes.html', 'docs.python.org/zh-cn/3/library/stdtypes.html/str.split']
测分解()


def 测大量分解():
    for i in tqdm(urls, ncols=60):
        l = [*分解(i)]
        assert len(l) == 0 or len(l) < i.count('/') + i.count('?') + i.count('#')
        assert all(['/' in x for x in l[1:]])
测大量分解()


def 测存(seed):
    a = []
    random.seed(seed)
    for _ in range(random.randint(1000, 80000)):
        n = random.randint(1, 1000)
        s = random.getrandbits(n*8).to_bytes(n, 'big').hex()
        a.append((random.random(), s))
    b = load(dump2(a))
    for (v1, s1), (v2, s2) in zip(a, b):
        assert -0.01 < v1-v2 < 0.01
        assert s1 == s2
for i in tqdm(range(5), ncols=60):
    测存(i)


def 测netloc():
    for i in tqdm(urls, ncols=60):
        a = netloc(i)
        b = urlparse(i).netloc
        if a != b:
            raise Exception(f'url={repr(i)}, 新={repr(a)}, 真={repr(b)}, urlparse={urlparse(i)}')
测netloc()


def 测netloc速度():
    def 旧netloc(url: str) -> str:
        try:
            return re.findall('//(.*?)(?=/|\?|$)', url)[0]
        except Exception:
            return urlparse(url).netloc
    start = time.time()
    for i in urls:
        netloc(i)
    necloc用时 = time.time() - start
    start = time.time()
    for i in urls:
        旧netloc(i)
    旧necloc用时 = time.time() - start
    print(f'{necloc用时=}, {旧necloc用时=}')
    assert necloc用时 < 旧necloc用时
for _ in range(3):
    测netloc速度()


def 测摘要():
    title, description, text, href, 真url, 重定向表, raw, 服务器类型 = 摘要('https://github.com/')
    assert len(title) < len(description) < len(text)
    assert len(raw) > len(title + description + text)
    assert href
    assert 'github' in title.lower()
    assert 服务器类型 == 'GitHub.com'
测摘要()


def 测切(url):
    r = 摘要(url, timeout=10)
    title, description, text = r[:3]
    def 分0(s):
        return [i for i in filter(None, map(收缩, jieba.lcut_for_search(s[:10000]))) if i not in 停词表 and len(i) <= 32]
    l = [url, len(text), len(分(text)), 分(title)==分0(title), 分(description)==分0(description), 分(text)==分0(text)]
    print(l)
    assert all(l)
for i in ['https://docs.python.org/', 'https://librian.net/', 'https://sese.yyj.moe/', 'https://github.com/', 'https://docs.python.org/zh-cn/3/', 'https://www.yahoo.co.jp/', 'https://www.dlsite.com/']:
    测切(i)


def 测import():
    import 收获服务器
    import 人服务器
    import 上网
    import 回
测import()


print('没问题了！')
