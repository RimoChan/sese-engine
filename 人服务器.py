from waitress import serve

import json
import math
import logging
import threading
import concurrent.futures
from itertools import islice
from urllib.parse import unquote
from typing import Tuple

import flask
import requests

from rimo_utils.计时 import 计时
from rimo_storage import cache

from utils import netloc, 小小清洗, 切
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
        kiss = 分(flask.request.args.get('q', ''), 多=False)
        kiss = [i for i in kiss if i not in 屏蔽词]
        assert len(kiss) < 20, '太多了，不行！'
        a, b = map(int, flask.request.args.get('slice', '0:7').split(':'))
        assert 0 <= a < b and b-a <= 10, '太长了，不行！'
        sli = slice(a, b)
        with 计时(kiss):
            结果, 总数 = 查询(kiss, sli)
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


def 坏(url):
    s = max(0, (len(url)-35)/400)
    if '.htm' in url or '.php' in url:
        s += 0.3
    if len(url.rstrip('/').split('/')) > 3:
        s += 0.2
    s = min(s, 0.9)
    return s


def 初步查询(keys: list, sli: slice):
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
        繁荣 = 繁荣表.get(netloc(url), 0)
        不喜欢 = 坏(url)
        p = 1
        for key in keys:
            p *= vs.get(key, 默认值[key])
        d[url] = p*math.log2(2+繁荣)*(1-不喜欢), p, 繁荣, 不喜欢
    q = sorted([(v, k) for k, v in d.items()], reverse=True)
    qq = [*islice(小小清洗(q, 1), sli.start, sli.stop, sli.step)]
    return qq, 记录, len(d)


def 查询(keys: list, sli=slice(0, 7)):
    with 计时(f'初步查询{keys}'):
        q, 记录, 总数 = 初步查询(keys, sli)
    res = []
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=len(q)+1)
    for (v, url), y in zip(q, pool.map(缓存摘要, [i[1] for i in q])):
        if y:
            title, description, text = y
            msg = {
                '标题': title,
                '描述': 预览(keys, description),
                '文本': 预览(keys, text),
                '文本长度': len(text),
            }
        else:
            g = 门.get(url)
            if g:
                title, description = g
                print(f'从门中拿到了{url}')
                msg = {
                    '标题': title,
                    '描述': 预览(keys, description),
                    '文本': '',
                    '文本长度': None,
                }
            else:
                msg = None
        res.append({
            '分数': {'终': v[0], '相关': v[1], '繁荣': v[2], '不喜欢': v[3]},
            '网址': unquote(url),
            '信息': msg,
            '相关性': {k: 记录[url].get(k, 0) for k in keys},
        })
    return res, 总数


def 预览(k, text):
    窗口长 = 32
    最后出现位置 = {x: -1 for x in k}
    c = 切(text[:3000])
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
            a, b = 0, 窗口长+10
        else:
            a, b = b1-窗口长, b1+10
        r = ''.join(c[a: b])
        if len(c) > b:
            r += '...'
        return r


@cache.disk_cache(path='./savedata/缓存摘要', serialize='json')
def _缓存摘要(url: str) -> Tuple[str, str, str]:
    if threading.current_thread().name == 'slow':
        r = 文.摘要(url, 乖=False, timeout=60)
        print(f'慢慢获取「{url}」成功了！')
        return r[:3]
    return 文.摘要(url, 乖=False, timeout=在线摘要限时, 大小限制=10000)[:3]


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
