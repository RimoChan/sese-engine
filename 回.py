import json
import time
import random
import logging
import datetime
from typing import Tuple, Dict, Optional, List, Iterable, Callable

import numpy as np
from tqdm import tqdm
from utils import 分解, netloc

from 文 import 缩
from 配置 import 存储位置
from 存储 import 融合之门


def ip字符串(ip_list: Optional[List[str]]) -> str:
    ip_list = sorted(ip_list or [])
    ip_list = [i[:i.rfind('.')] for i in ip_list]
    return ','.join(ip_list)


def 计数() -> Tuple[Dict[str, int], ...]:
    网站之门 = 融合之门(存储位置/'网站之门')
    子域名个数 = {}
    服务器个数 = {}
    模板个数 = {}
    同ip个数 = {}
    字段覆盖量 = {}
    关键词个数 = {}
    for i, (k, v) in tqdm(enumerate(iter(网站之门.items())), desc='计数'):
        if (i+1) % 100_0000 == 0:
            模板个数 = {k: v for k, v in 模板个数.items() if v > 1}
            同ip个数 = {k: v for k, v in 同ip个数.items() if v > 1}
            服务器个数 = {k: v for k, v in 服务器个数.items() if v > 1}
            关键词个数 = {k: v for k, v in 关键词个数.items() if v > 1}
        for a, b in v.items():
            if b:
                字段覆盖量[a] = 字段覆盖量.get(a, 0) + 1
        超b = 缩(k)
        子域名个数[超b] = 子域名个数.get(超b, 0) + 1
        if t := v.get('结构'):
            模板个数[t] = 模板个数.get(t, 0) + 1
        if t := v.get('服务器类型'):
            s = ','.join(sorted(t))
            服务器个数[s] = 服务器个数.get(s, 0) + 1
        if ip := v.get('ip'):
            ip_str = ip字符串(ip)
            同ip个数[ip_str] = 同ip个数.get(ip_str, 0) + 1
        for 词 in v.get('关键词') or ():
            关键词个数[词] = 关键词个数.get(词, 0) + 1
    print(f'一级域名个数: {len(子域名个数)}')
    print(f'字段覆盖量: {字段覆盖量}')
    子域名个数 = {k: v for k, v in 子域名个数.items() if v >= 4}
    模板个数 = {k: v for k, v in 模板个数.items() if v >= 4}
    同ip个数 = {k: v for k, v in 同ip个数.items() if v >= 4}
    服务器个数 = {k: v for k, v in 服务器个数.items() if v >= 4}
    关键词个数 = {k: v for k, v in 关键词个数.items() if v >= 4}
    return 子域名个数, 模板个数, 同ip个数, 服务器个数, 关键词个数


def 超源(条件: Optional[Callable] = None, *, 子域名个数, 模板个数) -> Iterable[Tuple[str, dict, float]]:
    网站之门 = 融合之门(存储位置/'网站之门')
    for k, v in 网站之门.items():
        if 条件 and not 条件(v):
            continue
        if not v.get('链接'):
            continue
        时间 = v.get('最后访问时间', 1640000000)
        过去天数 = (int(time.time()) - 时间) // (3600*24)
        if 过去天数 > 180:
            continue
        时间倍 = 0.99 ** 过去天数
        结构 = v.get('结构')
        超b = 缩(k)
        个 = max(子域名个数.get(超b, 1), int(模板个数.get(结构, 1)*1.5))
        if 个 > 1000:
            if random.random() > 1000/个:
                continue
            个 = 1000
        域名倍 = 1 / ((max(个, 5)/5) ** 0.6)
        倍 = 时间倍 * 域名倍
        yield k, v, 倍


def 超融合(f: Iterable[Tuple[str, dict]], *, 同ip个数, 服务器个数, desc) -> Dict[str, float]:
    向量化阈值 = 0.21
    服务器表 = {}
    for k, _ in sorted(服务器个数.items(), key=lambda x: -x[1])[:63]:
        服务器表[k] = len(服务器表) + 1
    ip来源 = {}
    向量 = {}
    d = {}
    键保留阈值 = 0.02
    for i, (k, v, 倍) in tqdm(enumerate(f), desc=desc):
        if (i+1) % 20_0000 == 0:
            while len(d) > 100_0000:
                d = {k: v for k, v in d.items() if v >= 键保留阈值}
                键保留阈值 *= 1.1
        if (i+1) % 40_0000 == 0:
            ip来源 = {k: v for k, v in ip来源.items() if v >= 0.04}
        a = v['链接']
        n = len(a)
        xd = {}
        w = 1/max(n, 50)
        for url in a:
            for x in 分解(url):
                if x not in xd:
                    xd[x] = w
                else:
                    xd[x] += w
        ip_str = ip字符串(v.get('ip'))
        服务器 = (v.get('服务器类型', []) + [None])[0]
        服务器编号 = 服务器表.get(服务器, 0)
        for x, w in xd.items():
            w = min(w, 0.15) * 倍
            if x not in d:
                d[x] = w
            else:
                if d[x] > 0.2:
                    if ip_str in 同ip个数:
                        key = f'{x}-{ip_str}'
                        if ip来源.get(key, 0) > 0.4:
                            continue
                        ip来源[key] = ip来源.get(key, 0) + w
                if d[x] > 向量化阈值 and ('/' not in x) and 服务器:
                    if x not in 向量:
                        向量[x] = np.zeros(64, dtype=np.float16)
                    if d[x] > 5:
                        向量[x] = 向量[x].astype(np.float32)
                    向量[x][服务器编号] += w
                d[x] += w
    d = {k: v for k, v in d.items() if v > 0.16}
    核 = np.zeros(64, dtype=np.float32)
    for x, v in 向量.items():
        核 += v
    核长 = np.linalg.norm(核)
    新d = {}
    d_cos = {}
    for k, v in d.items():
        基k = k.split('/')[0]
        if v > 向量化阈值 and 基k in 向量:
            向量基k = 向量[基k].astype(np.float32)
            cos = np.dot(向量基k, 核) / (np.linalg.norm(向量基k) * 核长)
            assert cos < 1.01, '太大了，不行'
            d_cos[基k] = float(cos)
            新d[k] = max(v * (0.25 + cos*0.75), 向量化阈值)
        else:
            新d[k] = v
    存档(存储位置/(desc+'_cos.json'), d_cos)
    return 新d


def 存档(path, data):
    open(path, 'w', encoding='utf8').write(json.dumps(data, ensure_ascii=False, indent=2))


def 刷新():
    子域名个数, 模板个数, 同ip个数, 服务器个数, 关键词个数 = 计数()
    存档(存储位置/'子域名个数.json', 子域名个数)
    存档(存储位置/'模板个数.json', 模板个数)
    存档(存储位置/'同ip个数.json', 同ip个数)
    存档(存储位置/'服务器个数.json', 服务器个数)
    存档(存储位置/'关键词个数.json', 关键词个数)

    源1 = 超源(lambda x: x.get('https可用'), 子域名个数=子域名个数, 模板个数=模板个数)
    d1 = 超融合(源1, 同ip个数=同ip个数, 服务器个数=服务器个数, desc='计算HTTPS反向链接')
    源2 = 超源(lambda x: not x.get('https可用'), 子域名个数=子域名个数, 模板个数=模板个数)
    d2 = 超融合(源2, 同ip个数=同ip个数, 服务器个数=服务器个数, desc='计算HTTP反向链接')

    ks = {*d1, *d2}
    d = {k: d1.get(k, 0) + min(d1.get(k, 0)*0.5+d2.get(k, 0)*0.1, d2.get(k, 0)) for k in ks}
    d = {k: v for k, v in d.items() if v > 0.16}
    d = dict(sorted(d.items()))

    q = [v for k, v in d.items() if '/' not in k]
    print(f'繁荣的网页个数: {len(d)}，繁荣的网页总能量: {sum(d.values())}')
    print(f'繁荣的域名个数: {len(q)}，繁荣的域名总能量: {sum(q)}')

    存档(存储位置/'繁荣.json', d)


if __name__ == '__main__':
    while True:
        time.sleep((48 - datetime.datetime.now().hour + 2) * 3600)
        try:
            print('=======================\n刷新时间', datetime.datetime.now())
            刷新()
        except Exception as e:
            logging.exception(e)
