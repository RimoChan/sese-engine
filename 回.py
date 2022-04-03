import json
import time
import random
import logging
import datetime
from collections import Counter

from tqdm import tqdm
from utils import 分解

from 配置 import 存储位置
from 存储 import 融合之门


def 刷新():
    网站之门 = 融合之门(存储位置/'网站之门')
    d = {}
    for i, (k, v) in tqdm(enumerate(iter(网站之门.items())), desc='域名个数'):
        a = v.get('链接')
        if not a:
            continue
        n = len(a)
        xd = {}
        w = 1/max(n, 50)
        for url in a:
            for x in 分解(url):
                if x not in xd:
                    xd[x] = w
                else:
                    xd[x] += w
        for x, w in xd.items():
            w = min(w, 0.15)
            if x not in d:
                d[x] = w
            else:
                d[x] += w
        if i % 100_0000 == 999999:
            d = {k: v for k, v in d.items() if v >= 0.03}
    print('好！')
    d = {k: v for k, v in d.items() if v > 0.16}
    d = {k: v for k, v in sorted(d.items())}

    q = [v for k, v in d.items() if '/' not in k]
    print(f'繁荣的域名个数: {len(q)}，繁荣的域名总能量: {sum(q)}')

    s = json.dumps(d, ensure_ascii=2, indent=2)
    with open(存储位置/'繁荣.json', 'w') as f:
        f.write(s)


if __name__ == '__main__':
    while True:
        time.sleep((24 - datetime.datetime.now().hour) * 3600)
        try:
            print('刷新时间', datetime.datetime.now())
            刷新()
        except Exception as e:
            logging.exception(e)
