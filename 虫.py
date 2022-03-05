import logging
from functools import lru_cache
from urllib.parse import urlparse
from typing import Optional

from reppy.robots import Robots
import requests

from 配置 import 爬虫的名字

logging.getLogger('urllib3.connection').setLevel(logging.CRITICAL)  # urllib3太吵了

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
        if not rp.allowed(url, 爬虫的名字):
            raise LoliError('被禁了，不行！')
    resp = requests.get(url, timeout=timeout, headers={'user-agent': 爬虫的名字}, stream=True)
    if resp.status_code == 404:
        raise LoliError('没有！没有！')
    resp.raise_for_status()
    if 'text/html' not in resp.headers.get('Content-Type', ''):
        raise LoliError(f'类型{resp.headers.get("Content-Type")}不行！')
    if 大小限制:
        data = b''
        for b in resp.iter_content(4096):
            data += b
            if len(data)>大小限制:
                break
    else:
        data = resp.content
    if resp.encoding == 'ISO-8859-1':   # 猜测编码的性能太差，直接硬上
        try:
            return data.decode('utf8')  
        except Exception:
            try:
                return data.decode('gbk')
            except Exception:
                return data.decode('utf8', 'ignore')
    else:
        return data.decode(resp.encoding, 'ignore')


def 爬(url, **d) -> Optional[str]:
    try:
        return 真爬(url, **d)
    except LoliError as e:
        logging.info(f'{url} {e}')
        return None
