import json
import random
import concurrent.futures
from functools import lru_cache
from collections import Counter

from tqdm import tqdm

from utils import netloc
from 存储 import 索引空间
from 文 import 摘要, 缩


def 抽(dropout=0.5):
    df = 索引空间('./savedata/键')
    tq = tqdm(desc='抽样消耗的key', ncols=60)
    tqc = tqdm(desc='抽出的url', ncols=60)
    for k in df:
        tq.update(1)
        if random.random() < dropout:
            continue
        for v, u in df[k]:
            if random.random() > 0.001:
                continue
            tqc.update(1)
            yield u


l = [*抽()]
if len(l) < 1000:
    raise Exception('太少了，不行！')
with open('savedata/抽样.json', 'w') as f:
    f.write(json.dumps(l))
with open('savedata/抽样.json', 'r') as f:
    ly = json.loads(f.read())

l = [*{netloc(i): i for i in ly}.values()]
print(f'抽取到了{len(ly)}个网页，清洗后还剩{len(l)}个。')


random.seed(1)
random.shuffle(l)
l = l[:500000]


def zz(url):
    return 摘要(url, 乖=False)[-1]


def 很像(a, b) -> bool:
    return a.split('.')[:-1] == b.split('.')[:-1]


def zzz(url):
    href = zz(url)
    超b = 缩(url)
    w = [netloc(i) for i in href]
    w2 = [缩(i) for i in href]
    w = [i for (i, 操b) in zip(w, w2) if not 很像(操b, 超b)]
    w = [i.lower() for i in w if i]
    return w


tt = tqdm(total=len(l), ncols=60)
全d = {}
def 抽(url):
    tt.update(1)
    try:
        w = zzz(url)
    except Exception:
        return
    n = len(w)
    d = {}
    for k, v in Counter(w).items():
        d[k] = v/n
    for k, v in d.items():
        全d.setdefault(k, 0)
        全d[k] += v


[*tqdm(concurrent.futures.ThreadPoolExecutor(max_workers=32).map(抽, l))]


全d = {k: v for k, v in 全d.items() if v > 0.1}
with open('savedata/繁荣.json', 'w', encoding='utf8') as f:
    f.write(json.dumps(全d, indent=4, ensure_ascii=False))
