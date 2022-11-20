import re
import time
import json
import math
import heapq
import logging
import threading
import concurrent.futures
from fnmatch import fnmatch
from itertools import islice
from functools import lru_cache
from collections import Counter
from urllib.parse import unquote
from typing import List, Tuple, Optional, Iterator, Dict

import jieba
import flask
import requests
import Levenshtein
import prometheus_client
from waitress import serve

from rimo_utils.计时 import 计时
from rimo_storage import cache

from 打点 import 计时打点
from utils import netloc, 切, 坏, 分解
import 文
import 信息
from 网站 import 超网站信息
from 存储 import 索引空间, 融合之门
from 分析 import 分
from 配置 import 使用在线摘要, 在线摘要限时, 单键最多url, 存储位置, 权重每日衰减, 语种权重, 连续关键词权重, 反向链接权重, 减权关键词, 减权关键词权重, 人服务器端口

logging.getLogger('werkzeug').setLevel(logging.ERROR)
threading.excepthook = lambda x: print(f'{x.thread} 遇到了exception: {repr(x.exc_value)}')

app = flask.Flask(__name__)
prometheus_client.start_http_server(14953)

反向索引 = 索引空间(存储位置/'键')
门 = 融合之门(存储位置/'门')

调整表 = 信息.调整表()
屏蔽词 = 信息.屏蔽词()


@app.route('/search')
def search():
    resp = _search()
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


_息 = lru_cache(maxsize=4096)(lambda b, _: 超网站信息[b])
息 = lambda b: _息(b, int(time.time())//(3600*24))


def _search():
    try:
        q = flask.request.args.get('q', '') or bytes.fromhex(flask.request.args.get('qh', '')).decode('utf8')
        kiss = []
        site = None
        for x in q.split():
            if t := re.findall('^site:(.*)$', x):
                site = t[0]
            else:
                kiss += 分(x, 多=False)
        kiss = [i for i in kiss if i not in 屏蔽词]
        assert len(kiss) < 20, '太多了，不行！'
        a, b = map(int, flask.request.args.get('slice', '0:10').split(':'))
        assert 0 <= a < b and b-a <= 20, '太长了，不行！'
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
            response=json.dumps(data, indent=2, ensure_ascii=False),
            status=200,
            mimetype='application/json',
        )
    except Exception as e:
        logging.exception(e)
        return app.response_class(
            response=json.dumps({'信息': str(e)}, indent=2, ensure_ascii=False),
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


def _连续性(s: str, keys: List[str]) -> int:
    return sum([(a+b in s) for a, b in zip(keys[:-1], keys[1:])])


def _重复性(l: List[str]) -> Iterator[int]:
    def q(a: str, b: str):
        if not a or not b:
            return 0
        return 1 - Levenshtein.distance(a, b) / max(len(a), len(b))
    if l:
        s = {l[0]}
        yield 0
    for i in l[1:]:
        yield max([q(i, j) for j in s])
        s.add(i)


def 初步查询(keys: list, sli: slice, site: Optional[str] = None) -> Tuple[List[Tuple[float, str]], Dict[str, dict], int, Dict[str, int]]:
    记录 = {}
    默认值 = {}
    with 计时(f'取索引{keys}'):
        for key in keys:
            l = 反向索引.get(key, [])
            if len(l) < 单键最多url:
                默认值[key] = 1/10000 * (max(100, len(l)) / 单键最多url)
            else:
                默认值[key] = max(1/10000, sorted([x[0] for x in l], reverse=True)[:单键最多url][-1] / 2)
            for v, url in l:
                记录.setdefault(url, {})[key] = v
    d = {}
    with 计时(f'取域名{keys}'):
        候选 = [*记录.items()]
        locs = [netloc(url) for url, vs in 候选]
        域名计数 = Counter(locs)
        if site:
            z = [(item, loc) for item, loc in zip(候选, locs) if fnmatch(loc, site) or fnmatch(loc, '*.'+site)]
            if not z:
                候选, locs = [], []
            else:
                候选, locs = zip(*z)
        总数 = len(候选)
    with 计时(f'相关性{keys}'):
        相关s = []
        for url, vs in 候选:
            相关 = 1
            for key in keys:
                vp = vs.get(key) or 默认值[key]
                if vp > 0.06:
                    vp = math.log((vp-0.06)*40+1) / 40 + 0.06
                相关 *= vp
            相关s.append(相关)
        相关性阈值 = 0
        if len(相关s) > sli.stop + 10:
            相关性阈值 = sorted(相关s, reverse=True)[sli.stop + 10] / 10
    with 计时(f'裁剪{keys}'):
        if 候选:
            候选, locs, 相关s = zip(*[(a, b, c) for a, b, c in zip(候选, locs, 相关s) if c > 相关性阈值])
    with 计时(f'荣{keys}'):
        荣s = [1 + 信息.荣(url)*反向链接权重 for url, vs in 候选]
    with 计时(f'初重{keys}'):
        for (url, vs), loc, 荣, 相关 in zip(候选, locs, 荣s, 相关s):
            调整 = 调整表.get(loc, 1)
            不喜欢 = 坏(url)
            d[url] = 相关*荣*(1-不喜欢)*调整, 相关, 荣, (1-不喜欢), 1, 1, 调整, 1, 1, 1, 1
    with 计时(f'初排序{keys}'):
        q = sorted([(v, k) for k, v in d.items()], reverse=True)
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=256)

    坏词 = {*减权关键词}
    with 计时(f'网站信息{keys}'):
        现在 = int(time.time())
        def r(item):
            v, k = item
            网站 = 息(netloc(k))
            语种 = 网站.语种
            词 = 网站.关键词 or []
            中文度 = 语种.get('zh', 0)
            怪文度 = sum(语种.values()) - 语种.get('zh', 0) - 语种.get('en', 0) - 语种.get('ja', 0)
            语种倍 = 1 + 中文度*语种权重 - 怪文度*语种权重
            时间 = 网站.最后访问时间 or 1648000000
            过去天数 = (现在 - 时间) // (3600*24)
            过去天数 = max(0, min(180, 过去天数-1))
            时间倍 = 权重每日衰减 ** 过去天数
            url时间 = 1648000000
            if t := 门.get(k, []):
                if len(t) > 3:
                    url时间 = t[3]
            url过去天数 = (现在 - url时间) // (3600*24)
            url时间倍 = 1
            if url过去天数 > 30:
                url时间倍 = ((2 + 权重每日衰减)/3) ** url过去天数
            词倍 = 1 - min(len({*词} & 坏词)*减权关键词权重, 0.5)
            vv = v[0]*语种倍*时间倍*词倍*url时间倍, v[1], v[2], v[3], 语种倍, v[5], v[6], 时间倍, v[8], 词倍, url时间倍
            return (vv, k)
        q[:256] = [*pool.map(r, q[:256])]
    q.sort(reverse=True)
    with 计时(f'重复性{keys}'):
        def r2(v, k, h, x):
            if h < 0.5:
                重复倍 = 1
            else:
                重复倍 = 1-(h-0.5)
            连续倍 = 连续关键词权重 ** x
            vv = v[0]*重复倍*连续倍, v[1], v[2], v[3], v[4], 重复倍, v[6], v[7], 连续倍, v[9], v[10]
            return vv, k
        def rf(item):
            v, url = item
            return (门.get(url) or [''])[0]
        题 = [*pool.map(rf, q[:64])]
        续 = [_连续性(s, keys) for s in 题]
        复 = _重复性(题)
        q[:80] = [r2(v, k, h, x) for (v, k), h, x in zip(q[:80], 复, 续)]
    with 计时(f'重排序{keys}'):
        qq = [*islice(重排序(q), sli.start, sli.stop, sli.step)]
    return qq, 记录, 总数, 域名计数


@计时打点
def 查询(keys: list, sli=slice(0, 10), site: Optional[str] = None):
    with 计时(f'初步查询{keys}'):
        q, 记录, 总数, 域名计数 = 初步查询(keys, sli, site)
    res = []
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=len(q)+1)
    for (v, url), y in zip(q, pool.map(缓存摘要, [i[1] for i in q])):
        if y and y[0]:
            title, description, text = y
            if '//zh.wikipedia.org' in url:
                text = text.replace('维基百科，自由的百科全书', '').replace('跳到导航', '').replace('跳到搜索', '').replace('本條目存在以下問題 ，請協助 改善本條目 或在 討論頁 針對議題發表看法。', '').replace('此條目 可参照 英語維基百科 相應條目来扩充 。', '').replace('此條目 需要补充更多 来源', '').replace('请协助補充多方面 可靠来源 以 改善这篇条目', '').replace('此條目 没有列出任何 参考或来源', '').replace('維基百科所有的內容都應該 可供查證 。', '')
                text = re.sub(' *（重定向自[^）]*?） *', ' ', text)
            msg = {
                '标题': title,
                '描述': 预览(keys, description),
                '文本': 预览(keys, text),
            }
        else:
            if g := 门.get(url):
                title, description, text = (g + [''])[:3]
                print(f'从门中拿到了{url}')
                msg = {
                    '标题': title,
                    '描述': 预览(keys, description),
                    '文本': 预览(keys, text),
                }
            else:
                msg = None
        if msg:
            if not msg['描述'] and not msg['文本']:
                msg['描述'] = description[:80]
                msg['文本'] = text[:80]
            if msg['文本']:
                if msg['描述'] in msg['标题']:
                    msg['描述'] = ''
                elif len(msg['描述']) < 3 and len(msg['文本']) >= 3:
                    msg['描述'] = ''
        原因 = {'内容与关键词相关': v[1], '反向链接加成': v[2], 'URL格式': v[3], '域名的语种': v[4], '标题与其他结果重复': v[5], '对域名的预调整': v[6], '我们对这个域名的认知过期了': v[7], '连续的关键词': v[8], '域名的内容': v[9], '我们对这个URL的认知过期了': v[10]}
        res.append({
            '分数': v[0],
            '原因': {k: v for k, v in 原因.items() if not 0.999 < v < 1.001},
            '网址': unquote(url),
            '信息': msg,
            '相关性': {k: 记录[url].get(k, 0) for k in keys},
            '相同域名个数': 域名计数.get(netloc(url)),
        })
    return res, 总数


def 预览(k, text) -> str:
    return _预览(k, text, 1000) or _预览(k, text, 7500)


def _预览(k, text, limit) -> str:
    窗口长 = 32
    最后出现位置 = {x: -1 for x in k}
    c = jieba.lcut(text[:limit])
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
    b1 = best[1]
    if b1 < 窗口长:
        a, b = 0, 窗口长+12
    else:
        a, b = b1-窗口长, b1+12
    r = ''.join(c[a: b])
    if len(c) > b:
        r += '...'
    return r


@cache.disk_cache(path=存储位置/'缓存摘要', serialize='json')
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
    except requests.exceptions.RequestException as e:
        print(f'获取「{url}」时遇到了{repr(e)}！')
        return None
    except Exception as e:
        logging.exception(e)
        return None


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=人服务器端口)
