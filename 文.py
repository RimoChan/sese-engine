import re
import posixpath
from urllib.parse import urlparse
from typing import Tuple, List, Dict

import lxml.html
import tldextract

from 虫 import 爬


def 缩(url: str) -> str:
    t = tldextract.extract(url)
    return f'{t.domain}.{t.suffix}'


def 摘要(url: str, **d) -> Tuple[str, str, str, List[str], str, Dict[str, str], str]:
    if t := 爬(url, **d):
        raw, 真url, 重定向表 = t
    else:
        return '', '', '', [], url, {}, ''
    if not raw:
        return '', '', '', [], 真url, 重定向表, raw
    q = urlparse(真url)
    基 = f'{q.scheme}://{q.netloc}'

    root = lxml.html.document_fromstring(raw)

    text = []
    href = []
    title = ''
    description = ''
    def dfs(r: lxml.html.HtmlElement):
        nonlocal title, description
        if r.tag in ('script', 'style', 'svg'):
            return
        if r.tag == 'meta' and r.attrib.get('name', '').lower() == 'description':
            description = r.attrib.get('content', '')
        if r.tag == 'a':
            s = r.attrib.get('href')
            if s:
                s = s.split('#')[0]
                if s:
                    qs = urlparse(s)
                    if qs.scheme not in ('', 'http', 'https'):
                        return
                    if qs.scheme == '':
                        s = 基 + posixpath.normpath(posixpath.join(q.path, '..', qs.path))
                    try:
                        urlparse(s)
                    except Exception:
                        None
                    else:
                        href.append(s)
        s = r.text
        if s:
            if not isinstance(r.tag, str):
                return
            s = re.sub('\s+', ' ', s)
            s = s.strip()
            if s:
                if r.tag == 'title':
                    title = s
                else:
                    text.append(s)
        for x in r:
            dfs(x)
        if r.tail:
            if t := re.sub('\s+', ' ', r.tail).strip():
                text.append(t)
    dfs(root)
    return title, description, ' '.join(text), href, 真url, 重定向表, raw
