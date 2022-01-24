import json
import time
import shutil
import random
from pathlib import Path
from collections import Counter
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

import requests
from tqdm import tqdm

import 分析
import 信息
from 文 import 缩, 摘要
from 存储 import 融合之门
from 配置 import 爬取线程数, 单网页最多关键词, 入口
from utils import tqdm_exception_logger


门 = 融合之门('./savedata/门')
繁荣表 = 信息.繁荣表()

a = tqdm(desc='访问url数')


if Path('savedata/网站信息.json').is_file():
    with open('savedata/网站信息.json', encoding='utf8') as f:
        网站信息: dict = json.loads(f.read())
else:
    网站信息 = {}


def 中文率(strs):
    if not strs:
        return None
    中文 = 0
    总 = 0
    for _char in strs:
        总 += 1
        if '\u4e00' <= _char <= '\u9fa5':
            中文 += 1
    r = 中文/总
    r = min(1, r*2)
    return r


def 摘(url):
    r = 摘要(url)
    if len(url) >= 250:
        return r
    title, description, text, href = r
    门[url] = title, description[:256]
    l = 分析.龙(title, description, text)
    if l:
        l = sorted(l, key=lambda x:x[1], reverse=True)[:单网页最多关键词]
        data = [url, l]
        requests.post('http://127.0.0.1:5000/l', data=json.dumps(data)).raise_for_status()
    return r


def 求质量(url):
    title, description, text, href = 摘(url)
    s = 1
    if not title:
        s *= 0.2
    if not description:
        s *= 0.7
    if not url.startswith('https'):
        s *= 0.8
    if 'm' in url.split('.'):
        s *= 0.6
    return s


def 超吸(url):
    a.update(1)
    try:
        title, description, text, href = 摘(url)
        q = urlparse(url)
        b = q.netloc
        超b = 缩(url)
        k = max([中文率(text), 中文率(title)], key=lambda x: -1 if x is None else x)

        中文度, 已访问次数, 质量 = 网站信息.get(b, (0.5, 1, None))
        if k is not None:
            中文度 = 中文度*0.9 + k*0.1
        已访问次数 += 1
        if 质量 is None:
            质量 = 求质量(f'https://{q.netloc}/')
        网站信息[b] = 中文度, 已访问次数, 质量

        中文度, 已访问次数, 质量 = 网站信息.get(超b, (0.5, 1, None))
        if 质量 is None:
            质量 = 求质量(f'https://{超b}/')
        已访问次数 += 0.1
        网站信息[超b] = 中文度, 已访问次数, 质量

        return href
    except Exception as e:
        tqdm_exception_logger(e)
        time.sleep(0.25)
        return []


def 计算兴趣(域名: str, 已访问次数: int) -> float:
    限制 = 繁荣表.get(域名, 0) * 1000 + 100
    b = 0.1**(1/限制)
    return b ** 已访问次数


def 喜欢(url) -> float:
    b = urlparse(url).netloc
    中文度, 已访问次数, 质量 = 网站信息.get(b, (0.5, 1, 1))
    超b = 缩(url)
    兴趣 = 计算兴趣(b, 已访问次数)
    if 超b == b:
        兴趣2 = 1
    else:
        _, 已访问次数2, __ = 网站信息.get(超b, (0.5, 1, 1))
        兴趣2 = 计算兴趣(超b, 已访问次数2)
    return max(0.1, 中文度) * max(0.1, 兴趣) * 质量 * max(0.1, 兴趣2)


def 重整(url_list):
    random.shuffle(url_list)
    a = []
    d = {}
    for x in url_list:
        d.setdefault(urlparse(x).netloc, []).append(x)
    for _, v in d.items():
        sn = int(len(v)**0.5)+1
        a += v[:sn]
    a.sort(key=lambda x: 喜欢(x) * random.random(), reverse=True)
    a = a[:2500]
    random.shuffle(a)
    return a


打点 = []


def bfs(start, epoch=999999):
    吸过 = set()
    pool = ThreadPoolExecutor(max_workers=爬取线程数)
    q = [start]
    for _ in range(epoch):
        新q = []
        if not q:
            break
        for i in q:
            吸过.add(i)
        for href in pool.map(超吸, q):
            for i in href:
                if i not in 吸过:
                    新q.append(i)
        新q = list(set(新q))
        上l = len(新q)
        q = 重整(新q)

        with open('savedata/网站信息.json', 'w', encoding='utf8') as f:
            f.write(json.dumps(网站信息, indent=2, ensure_ascii=False))

        c = Counter([urlparse(x).netloc for x in q])
        打点.append({
            '上次抓到的长度': 上l,
            '长度': len(q),
            '目标': dict(c.most_common(10)),
        })
        with open('打点.json', 'w', encoding='utf8') as f:
            f.write(json.dumps(打点, indent=2, ensure_ascii=False))


while True:
    bfs(入口)
