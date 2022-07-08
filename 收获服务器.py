import os
import random
import logging
import threading
from functools import lru_cache
from typing import Tuple

import flask
from tqdm import tqdm

from 信息 import 荣
from 类 import 阵
from 存储 import 索引空间
from utils import netloc, json_loads, 小清洗, 好ThreadPoolExecutor

from 配置 import 单键最多url, 单键最多相同域名url, 存储位置, 大清洗行数, 新增键需url数

logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = flask.Flask(__name__)


面板 = {x: tqdm(desc=x) for x in ['内存键数', '收到请求数', '丢弃行数', '小清洗次数']}

df = 索引空间(存储位置/'键')
临时df = {}
偏执 = 0
大清 = threading.Lock()


def 消重(q: 阵) -> 阵:
    qq = []
    有 = set()
    for v, url in q:
        if url in 有:
            continue
        有.add(url)
        qq.append((v, url))
    return qq


def 降解(q: 阵) -> 阵:
    qq = []
    有 = set()
    for v, url in sorted(q, key=lambda x: -len(x[1])):
        k = url
        if k.startswith('https://'):
            k = k[8:]
        elif k.startswith('http://'):
            k = k[7:]
        if k.endswith('/'):
            k = k[:-1]
        if k in 有:
            continue
        有.add(k)
        qq.append((v, url))
    return qq


@lru_cache(maxsize=100_0000)
def 低(k: str) -> float:
    l = df.get(k, [])
    if len(l) < 单键最多url:
        return -1
    else:
        return min(0.05, sorted([v for v, url in l], reverse=True)[单键最多url-1])


@app.route('/l', methods=['POST'])
def l():
    global 偏执
    文件名, kvs = json_loads(flask.request.data)
    文件名 = 文件名.replace('\n', '')
    netloc(文件名)
    面板['收到请求数'].update(1)
    for k, v in kvs:
        if k not in 临时df:
            临时df[k] = []
        dfk = 临时df[k]
        if len(dfk) > 15 and v < 低(k):
            面板['丢弃行数'].update(1)
            continue
        dfk.append((v, 文件名))
    面板['内存键数'].n = len(临时df)
    面板['内存键数'].refresh()
    大清.acquire()
    偏执 += 1
    if (偏执+1) % 10000 == 0:
        内存行数 = sum([len(临时df[k]) for k in [*临时df]])
        if 内存行数 > 大清洗行数:
            偏执 = 0
            大清洗()
            os._exit(0)   # 我也想不通这就100行代码居然有内存泄漏，我也不知道漏在哪里了，先靠重启解决吧
    大清.release()
    return 'ok'


def 洗(item) -> Tuple[int, str]:
    k, v = item
    原v = df.get(k, [])
    if not 原v:
        if len(v) < 新增键需url数:
            return 0, '丢弃'
    z = 消重(tuple(v) + tuple(原v))
    if random.random() < 0.02:
        z = 降解(z)
    if len(z) > 单键最多url*1.1 or random.random() < 0.02:
        面板['小清洗次数'].update(1)
        zt = 小清洗(sorted(z, key=lambda x: x[0] * (1 + 荣(x[1])), reverse=True), 单键最多相同域名url)
        z = zt[:单键最多url]
    if len(z) > 30 and random.random() < 0.2:
        z = sorted(z, reverse=True, key=lambda x: x[1])  # 让压缩算法高兴
    df[k] = z
    diff = len(z) - len(原v)
    状态 = '?'
    if not 原v:
        状态 = '新增'
    elif diff > 0:
        状态 = '变长'
    elif diff == 0:
        状态 = '不变'
    elif diff < 0:
        状态 = '变短'
    return diff, 状态


def 大清洗():
    global 临时df
    pool = 好ThreadPoolExecutor(max_workers=8)
    try:
        _临时df = 临时df
        临时df = {}
        状态统计 = {}
        状态值统计 = {}
        items = [*_临时df.items()]
        random.shuffle(items)
        for i, 状态 in tqdm(pool.map(洗, items), ncols=70, desc='大清洗', total=len(_临时df)):
            状态统计[状态] = 状态统计.get(状态, 0) + 1
            状态值统计[状态] = 状态值统计.get(状态, 0) + i
        print(f'\n\n\n\n大清洗好了。\n增加了{sum(状态值统计.values())}行。\n键状态: {状态统计}\n键状态值: {状态值统计}')
    except Exception as e:
        print('完蛋了！')
        logging.exception(e)
        while True:
            ...


if __name__ == '__main__':
    app.run()
