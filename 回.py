import json
import time
import random
import logging
import datetime
from typing import Tuple, Dict, Optional, List

from tqdm import tqdm
from utils import 分解, netloc

from 文 import 缩
from 配置 import 存储位置
from 存储 import 融合之门


def 域名相似(a: str, b: str) -> float:
    a = a.split('.')[:-1]
    if a and a[0]=='www':
        a = a[1:]
    a = {*a}
    b = b.split('.')[:-1]
    if b and b[0]=='www':
        b = b[1:]
    b = {*b}
    return len(a & b) / max(1, len(a | b))


def ip字符串(ip_list: Optional[List[str]]) -> str:
    ip_list = sorted(ip_list or [])
    ip_list = [i[:i.rfind('.')] for i in ip_list]
    return ','.join(ip_list)


def 计数() -> Tuple[Dict[str, int], Dict[str, int]]:
    网站之门 = 融合之门(存储位置/'网站之门')
    子域名个数 = {}
    模板个数 = {}
    同ip个数 = {}
    for i, (k, v) in tqdm(enumerate(iter(网站之门.items())), desc='计数'):
        if (i+1) % 100_0000 == 0:
            模板个数 = {k: v for k, v in 模板个数.items() if v > 1}
        超b = 缩(k)
        子域名个数[超b] = 子域名个数.get(超b, 0) + 1
        if t:=v.get('结构'):
            模板个数[t] = 模板个数.get(t, 0) + 1
        if ip:=v.get('ip'):
            ip_str = ip字符串(ip)
            同ip个数[ip_str] = 同ip个数.get(ip_str, 0) + 1
    print(f'一级域名个数: {len(子域名个数)}')
    子域名个数 = {k: v for k, v in 子域名个数.items() if v >= 4}
    模板个数 = {k: v for k, v in 模板个数.items() if v >= 4}
    同ip个数 = {k: v for k, v in 同ip个数.items() if v >= 4}
    return 子域名个数, 模板个数, 同ip个数


def 刷新():
    子域名个数, 模板个数, 同ip个数 = 计数()
    with open(存储位置/'子域名个数.json', 'w', encoding='utf8') as f:
        f.write(json.dumps(子域名个数, ensure_ascii=False, indent=2))
    with open(存储位置/'模板个数.json', 'w', encoding='utf8') as f:
        f.write(json.dumps(模板个数, ensure_ascii=False, indent=2))
    with open(存储位置/'同ip个数.json', 'w', encoding='utf8') as f:
        f.write(json.dumps(同ip个数, ensure_ascii=False, indent=2))
    网站之门 = 融合之门(存储位置/'网站之门')
    ip来源 = {}
    d = {}
    for i, (k, v) in tqdm(enumerate(iter(网站之门.items())), desc='计算反向链接'):
        if (i+1) % 100_0000 == 0:
            d = {k: v for k, v in d.items() if v >= 0.04}
            ip来源 = {k: v for k, v in ip来源.items() if v >= 0.04}
        a = v.get('链接')
        if not a:
            continue
        超b = 缩(k)
        时间 = v.get('最后访问时间', 1648300000)
        过去天数 = (int(time.time()) - 时间) // (3600*24)
        if 过去天数 > 180:
            continue
        时间倍 = 0.99 ** 过去天数
        协议倍 = 0.5 * bool(v.get('https可用')) + 0.5
        结构 = v.get('结构')
        个 = max(子域名个数.get(超b, 1), 模板个数.get(结构, 1))
        if 个 > 1000:
            if random.random() > 1000/个:
                continue
            个 = 1000
        域名倍 = 1 / ((max(个, 5)/5) ** 0.6)
        n = len(a)
        xd = {}
        w = 1/max(n, 50)
        for url in a:
            for x in 分解(url):
                真w = w * (1 - 域名相似(k, netloc(url)))
                if x not in xd:
                    xd[x] = 真w
                else:
                    xd[x] += 真w
        倍 = 时间倍 * 域名倍 * 协议倍
        ip_str = ip字符串(v.get('ip'))
        for x, w in xd.items():
            w = min(w, 0.15) * 倍
            if x not in d:
                d[x] = w
            else:
                if ip_str in 同ip个数 and d[x] > 0.2:
                    key = f'{x}-{ip_str}'
                    if ip来源.get(key, 0) > 0.4:
                        # print(key, ip来源[key], d[x])
                        continue
                    ip来源[key] = ip来源.get(key, 0) + w
                d[x] += w

    print('好！')
    d = {k: v for k, v in d.items() if v > 0.16}
    d = dict(sorted(d.items()))

    q = [v for k, v in d.items() if '/' not in k]
    print(f'繁荣的域名个数: {len(q)}，繁荣的域名总能量: {sum(q)}')

    with open(存储位置/'繁荣.json', 'w') as f:
        f.write(json.dumps(d, ensure_ascii=2, indent=2))


if __name__ == '__main__':
    while True:
        time.sleep((24 - datetime.datetime.now().hour + 2) * 3600)
        try:
            print('刷新时间', datetime.datetime.now())
            刷新()
        except Exception as e:
            logging.exception(e)
