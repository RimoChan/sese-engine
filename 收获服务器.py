import os
import logging
import threading
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from typing import Tuple

import flask
from tqdm import tqdm

from 类 import 阵
from 存储 import 索引空间
from utils import netloc, json_loads, 小清洗, 好ThreadPoolExecutor

from 配置 import 单键最多url, 单键最多相同域名url, 存储位置

logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = flask.Flask(__name__)


面板 = {x: tqdm(desc=x) for x in ['内存键数', '收到请求数', '丢弃行数']}

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


@lru_cache(maxsize=100_0000)
def 低(k: str) -> float:
    l = df.get(k, [])
    if len(l) < 单键最多url:
        return -1
    else:
        return sorted([v for v, url in l], reverse=True)[单键最多url-1]


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
    if 偏执 % 10000 == 9999:
        内存行数 = sum([len(临时df[k]) for k in [*临时df]])
        if 内存行数 > 1000_0000:
            偏执 = 0
            大清洗()
            os._exit(0)   # 我也想不通这就100行代码居然有内存泄漏，我也不知道漏在哪里了，先靠重启解决吧
    大清.release()
    return 'ok'


def 洗(item) -> Tuple[int, str]:
    k, v = item
    原v = df.get(k, [])
    if not 原v:
        if len(v) < 3:
            return 0, '丢弃'
    z = 消重(tuple(v) + tuple(原v))
    if len(z) > 单键最多url*1.1:
        z = 小清洗(sorted(z, reverse=True), 单键最多相同域名url)[:单键最多url]
    df[k] = z
    return len(z) - len(原v), '新增' if not 原v else '变长'


def 大清洗():
    global 临时df, df
    pool = 好ThreadPoolExecutor(max_workers=8)
    try:
        _临时df = 临时df
        临时df = {}
        总 = 0
        状态统计 = {}
        for i, 状态 in tqdm(pool.map(洗, _临时df.items()), ncols=70, desc='大清洗', total=len(_临时df)):
            总 += i
            状态统计[状态] = 状态统计.get(状态, 0) + 1
        print(f'\n\n\n清洗好了。\n总共增加了{总}行。\n键状态: {状态统计}')
    except Exception as e:
        print('完蛋了！')
        logging.exception(e)
        while True:
            ...


if __name__ == '__main__':
    app.run()
