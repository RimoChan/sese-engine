import json
import time
import logging
import datetime

from tqdm import tqdm
from utils import 分解, netloc

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


def 刷新():
    网站之门 = 融合之门(存储位置/'网站之门')
    d = {}
    for i, (k, v) in tqdm(enumerate(iter(网站之门.items())), desc='域名个数'):
        a = v.get('链接')
        if not a:
            continue
        时间 = v.get('最后访问时间', 1648300000)
        过去天数 = (int(time.time()) - 时间) // (3600*24)
        if 过去天数 > 180:
            continue
        时间倍 = 0.99 ** 过去天数
        n = len(a)
        xd = {}
        w = 1/max(n, 50)
        for url in a:
            for x in 分解(url):
                真w = w * (1 - 域名相似(k, netloc(url))) * 时间倍
                if x not in xd:
                    xd[x] = 真w
                else:
                    xd[x] += 真w
        for x, w in xd.items():
            w = min(w, 0.15)
            if x not in d:
                d[x] = w
            else:
                d[x] += w
        if (i+1) % 100_0000 == 0:
            d = {k: v for k, v in d.items() if v >= 0.03}
    print('好！')
    d = {k: v for k, v in d.items() if v > 0.16}
    d = dict(sorted(d.items()))

    q = [v for k, v in d.items() if '/' not in k]
    print(f'繁荣的域名个数: {len(q)}，繁荣的域名总能量: {sum(q)}')

    s = json.dumps(d, ensure_ascii=2, indent=2)
    with open(存储位置/'繁荣.json', 'w') as f:
        f.write(s)


if __name__ == '__main__':
    while True:
        time.sleep((24 - datetime.datetime.now().hour + 2) * 3600)
        try:
            print('刷新时间', datetime.datetime.now())
            刷新()
        except Exception as e:
            logging.exception(e)
