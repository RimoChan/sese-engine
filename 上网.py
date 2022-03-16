import copy
import json
import time
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from typing import List

import requests
from tqdm import tqdm

import 分析
import 信息
from 文 import 缩, 摘要
from 存储 import 融合之门, 网站信息表
from 配置 import 爬取线程数, 单网页最多关键词, 入口
from utils import tqdm_exception_logger, 坏, 检测语言, netloc


门 = 融合之门('./savedata/门')
繁荣表 = 信息.繁荣表()

a = tqdm(desc='访问url数')

网站信息 = 网站信息表('savedata/网站信息')


def 摘(url):
    r = 摘要(url)
    if len(url) >= 250:
        return r
    title, description, text, href = r
    门[url] = title, description[:256]
    l = 分析.龙(title, description, text)
    if l:
        l = sorted(l, key=lambda x: x[1], reverse=True)[:单网页最多关键词]
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


默认息 = {
    '访问次数': 0,
    '质量': None,
    '语种': {},
    '链接': [],
}


def 超吸(url) -> List[str]:
    a.update(1)
    try:
        title, description, text, href = 摘(url)

        b = netloc(url)
        超b = 缩(url)
        k = 0

        息 = 网站信息.get(b) or copy.deepcopy(默认息)
        息['访问次数'] += 1
        if 息['质量'] is None:
            息['质量'] = 求质量(f'https://{b}/')
        if 息['访问次数'] < 10 or random.random() < 0.1:
            语种 = 检测语言(' '.join((title, description, text)))
            td = {k: v*0.9 for k, v in 息['语种'].items()}
            td[语种] = td.get(语种, 0) + 0.1
            息['语种'] = td
            外href = [h for h in href if 缩(h) != 超b]
            息['链接'] += random.sample(外href, min(10, len(外href)))
            if len(息['链接']) > 200:
                息['链接'] = random.sample(息['链接'], 150)
        网站信息[b] = 息

        if 超b != b:
            超息 = 网站信息.get(超b) or copy.deepcopy(默认息)
            if 超息['质量'] is None:
                超息['质量'] = 求质量(f'https://{超b}/')
            超息['访问次数'] += 0.2
            网站信息[超b] = 超息
        return href
    except Exception as e:
        tqdm_exception_logger(e)
        time.sleep(0.25)
        return []


def 重整(url_list: list):
    def 计算兴趣(域名: str, 已访问次数: int) -> float:
        限制 = 繁荣表.get(域名, 0) * 1000 + 50
        b = 0.1**(1/限制)
        return b ** 已访问次数
    def 喜欢(url: str) -> float:
        b = netloc(url)
        息 = 缓存信息[b] or copy.deepcopy(默认息)
        if 息['语种']:
            中文度 = 息['语种'].get('zh', 0) / sum(息['语种'].values())
        else:
            中文度 = 0.5
        已访问次数, 质量 = 息['访问次数'], 息['质量'] or 1
        超b = 缩(url)
        兴趣 = 计算兴趣(b, 已访问次数)
        if 超b == b:
            兴趣2 = 1
        else:
            超息 = 缓存信息[超b] or copy.deepcopy(默认息)
            已访问次数2 = 超息['访问次数']
            兴趣2 = 计算兴趣(超b, 已访问次数2)
        return max(0.2, 中文度) * max(0.1, 兴趣) * 质量 * max(0.1, 兴趣2) * (1-坏(url))
    random.shuffle(url_list)
    a = []
    d = {}
    for x in url_list:
        d.setdefault(netloc(x), []).append(x)
    for _, v in d.items():
        sn = int(len(v)**0.5)+1
        a += v[:sn]
    缓存信息 = {k: 网站信息.get(k) for k in ({netloc(url) for url in a}|{缩(url) for url in a})}
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

        c = Counter([netloc(x) for x in q])
        打点.append({
            '上次抓到的长度': 上l,
            '长度': len(q),
            '目标': dict(c.most_common(10)),
        })
        with open('打点.json', 'w', encoding='utf8') as f:
            f.write(json.dumps(打点, indent=2, ensure_ascii=False))
        if len(吸过) > 3*10**6:
            吸过 = set()


if __name__=='__main__':
    while True:
        bfs(入口)
        time.sleep(5)
