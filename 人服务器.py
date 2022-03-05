from waitress import serve

import re
import json
import math
import heapq
import logging
import threading
import concurrent.futures
from fnmatch import fnmatch
from itertools import islice
from urllib.parse import unquote
from typing import Tuple, Optional

import flask
import requests

from rimo_utils.计时 import 计时
from rimo_storage import cache

from utils import netloc, 切, 坏
import 文
import 信息
from 存储 import 索引空间, 融合之门
from 分析 import 分
from 配置 import 使用在线摘要, 在线摘要限时, 单键最多url


logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = flask.Flask(__name__)

反向索引 = 索引空间('./savedata/键')
门 = 融合之门('./savedata/门')

繁荣表 = 信息.繁荣表()


with open('./data/屏蔽词.json', encoding='utf8') as f:
    屏蔽词 = {*json.load(f)}


@app.route('/search')
def search():
    resp = _search()
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/test')
def test():
    return app.response_class(
        response=json.dumps(1),
        status=200,
        mimetype='application/json',
    )


def _search():
    try:
        q = flask.request.args.get('q', '')
        kiss = []
        site = None
        for x in q.split():
            if t:=re.findall('^site:(.*)$', x):
                site = t[0]
            else:
                kiss += 分(x, 多=False)
        kiss = [i for i in kiss if i not in 屏蔽词]
        assert len(kiss) < 20, '太多了，不行！'
        a, b = map(int, flask.request.args.get('slice', '0:10').split(':'))
        assert 0 <= a < b and b-a <= 10, '太长了，不行！'
        sli = slice(a, b)
        with 计时(kiss):
            结果, 总数 = 查询(kiss, sli, site)
            data = {
                '分词': kiss,
                '数量': {i: (len(反向索引[i]) if i in 反向索引 else 0) for i in kiss},
                '结果': 结果,
                '总数': 总数,
            }
        return app.response_class(
            response=json.dumps(data, indent=4, ensure_ascii=False),
            status=200,
            mimetype='application/json',
        )
    except Exception as e:
        logging.exception(e)
        return app.response_class(
            response=json.dumps({'信息': str(e)}, indent=4, ensure_ascii=False),
            status=500,
            mimetype='application/json',
        )


def 重排序(q):
    d = {}
    倍 = {}
    堆 = []
    for v, url in q:
        d.setdefault(netloc(url).lower(), []).append((v, url))
    for k, l in d.items():
        倍[k] = 1
        l.sort()
        x = l.pop()
        heapq.heappush(堆, (-x[0][0], x, k))
    while 堆:
        _, x, k = heapq.heappop(堆)
        yield x
        if d[k]:
            倍[k] /= 8
            x = d[k].pop()
            heapq.heappush(堆, (-x[0][0]*倍[k], x, k))


def 初步查询(keys: list, sli: slice, site: Optional[str]=None):
    记录 = {}
    默认值 = {}
    for key in keys:
        l = 反向索引.get(key, [])
        if len(l) < 单键最多url:
            默认值[key] = 1/10000 * (max(100, len(l)) / 单键最多url)
        else:
            默认值[key] = max(1/10000, sorted([x[0] for x in l], reverse=True)[:单键最多url][-1] / 2)
        for v, url in l:
            记录.setdefault(url, {})[key] = v
    d = {}
    for url, vs in 记录.items():
        loc = netloc(url)
        if site and not (fnmatch(loc, site) or fnmatch(loc, '*.'+site)):
            continue
        繁荣 = 繁荣表.get(loc, 0)
        不喜欢 = 坏(url)
        p = 1
        for key in keys:
            p *= vs.get(key, 默认值[key])
        d[url] = p*math.log2(2+繁荣)*(1-不喜欢), p, 繁荣, 不喜欢
    q = [(v, k) for k, v in d.items()]
    qq = [*islice(重排序(q), sli.start, sli.stop, sli.step)]
    return qq, 记录, len(d)


def 查询(keys: list, sli=slice(0, 10), site: Optional[str]=None):
    with 计时(f'初步查询{keys}'):
        q, 记录, 总数 = 初步查询(keys, sli, site)
    res = []
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=len(q)+1)
    for (v, url), y in zip(q, pool.map(缓存摘要, [i[1] for i in q])):
        if y and y[0]:
            title, description, text = y
            msg = {
                '标题': title,
                '描述': 预览(keys, description),
                '文本': 预览(keys, text),
                '文本长度': len(text),
            }
        else:
            if g := 门.get(url):
                title, description = g
                text = ''
                print(f'从门中拿到了{url}')
                msg = {
                    '标题': title,
                    '描述': 预览(keys, description),
                    '文本': text,
                    '文本长度': None,
                }
            else:
                msg = None
        if msg and (not msg['描述'] and not msg['文本']):
            msg['描述'] = description[:80]
            msg['文本'] = text[:80]
        res.append({
            '分数': {'终': v[0], '相关': v[1], '繁荣': v[2], '不喜欢': v[3]},
            '网址': unquote(url),
            '信息': msg,
            '相关性': {k: 记录[url].get(k, 0) for k in keys},
        })
    return res, 总数


def 预览(k, text) -> str:
    return _预览(k, text, 1000) or _预览(k, text, 7500)


def _预览(k, text, limit) -> str:
    窗口长 = 32
    最后出现位置 = {x: -1 for x in k}
    c = 切(text[:limit])
    best = (0, 0)
    for i, s in enumerate(c):
        s = s.lower()
        if s in 最后出现位置:
            最后出现位置[s] = i
            bs = len([v for v in 最后出现位置.values() if v > i-窗口长])
            if bs > best[0]:
                best = (bs, i)
    if best[0] == 0:
        return ''
    else:
        b1 = best[1]
        if b1 < 窗口长:
            a, b = 0, 窗口长+12
        else:
            a, b = b1-窗口长, b1+12
        r = ''.join(c[a: b])
        if len(c) > b:
            r += '...'
        return r


@cache.disk_cache(path='./savedata/缓存摘要', serialize='json')
def _缓存摘要(url: str) -> Tuple[str, str, str]:
    if threading.current_thread().name == 'slow':
        r = 文.摘要(url, 乖=False, timeout=60, 大小限制=60000)
        print(f'慢慢获取「{url}」成功了！')
        return r[:3]
    return 文.摘要(url, 乖=False, timeout=在线摘要限时, 大小限制=60000)[:3]


def 缓存摘要(url: str):
    if not 使用在线摘要:
        return None
    try:
        return _缓存摘要(url)
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        print(f'获取「{url}」时网络不好！')
        threading.Thread(target=lambda: _缓存摘要(url), name='slow').start()
        return None
    except Exception as e:
        logging.exception(e)
        return None


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=4950)
