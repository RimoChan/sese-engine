import logging
from functools import lru_cache
from urllib.parse import urlparse
from typing import Optional

from reppy.robots import Robots
import requests


class LoliError(Exception):
    ...


@lru_cache(maxsize=512)
def 萝卜(url):
    rp = Robots.fetch(url+'/robots.txt', timeout=5)
    return rp


def 真爬(url, 乖=True, timeout=5, 大小限制=None) -> str:
    q = urlparse(url)
    if 乖:
        rp = 萝卜(f'{q.scheme}://{q.netloc}')
        if not rp.allowed(url, "loli_tentacle"):
            raise LoliError('被禁了，不行！')
    resp = requests.get(url, timeout=timeout, headers={'user-agent': 'loli_tentacle'}, stream=True)
    if resp.status_code == 404:
        raise LoliError('没有！没有！')
    resp.raise_for_status()
    if 'text/html' not in resp.headers.get('Content-Type', ''):
        raise LoliError(f'类型{resp.headers.get("Content-Type")}不行！')
    if 大小限制:
        data = next(resp.iter_content(大小限制))
    else:
        data = resp.content
    if resp.encoding == 'ISO-8859-1':
        return data.decode('utf8', 'ignore')  # 猜测编码的性能太差，直接硬上
    else:
        return data.decode(resp.encoding, 'ignore')


def 爬(url, **d) -> Optional[str]:
    try:
        return 真爬(url, **d)
    except LoliError as e:
        logging.warning(f'{url} {e}')
        return None
