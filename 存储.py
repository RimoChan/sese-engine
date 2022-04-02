import orjson
import struct
import base64
import hashlib
import urllib.parse
from typing import MutableMapping

import brotli
from rimo_storage import 超dict

from 类 import 阵


def dump2(o: 阵) -> bytes:
    c = [*zip(*o)] or ([], [])
    n = len(c[0])
    希1 = orjson.dumps(c[1])
    nz = struct.pack('i', n)
    内容 = struct.pack(f'{n}e{len(希1)}s', *c[0], 希1)
    z = b'yn0001'+nz+内容
    return z


def _load1(b: bytes) -> 阵:
    n = struct.unpack('i', b[:4])[0]
    字符串长度 = struct.unpack(f'{n}h', b[4:4+n*2])
    吸0 = struct.unpack(f'{n}e', b[4+n*2:4+n*4])
    文hint = ''.join([f'{x}s' for x in 字符串长度])
    吸1 = struct.unpack(文hint, b[4+n*4:])
    吸1 = [x.decode('utf8') for x in 吸1]
    return [*zip(吸0, 吸1)]


def _load2(b: bytes) -> 阵:
    assert b[:6]==b'yn0001', '版本不对'
    n = struct.unpack('i', b[6:10])[0]
    吸0 = struct.unpack(f'{n}e', b[10:10+n*2])
    吸1 = orjson.loads(b[10+n*2:])
    assert len(吸0)==len(吸1), '数据不完整'
    return [*zip(吸0, 吸1)]


def load(b: bytes) -> 阵:
    if b.startswith(b'yn0001'):
        return _load2(b)
    else:
        return _load1(b)


empty = dump2([])
c = lambda x: brotli.compress(x, quality=6)
d = lambda x: brotli.decompress(x) if x != b'' else empty

def 索引空间(path) -> MutableMapping[str, 阵]:
    return 超dict(path, compress=(c, d), serialize=(dump2, load))


class 融合之门(MutableMapping):
    def __init__(self, path):
        def d(x):
            try:
                return brotli.decompress(x)
            except Exception:
                return '[]'
        self.d = 超dict(path, compress=(c, d))

    def __getitem__(self, k):
        真k = hashlib.sha224(k.encode('utf8')).hexdigest()[:5]
        for kk, vv in self.d[真k]:
            if kk == k:
                return vv
        else:
            raise KeyError(k)

    def __setitem__(self, k, v):
        真k = hashlib.sha224(k.encode('utf8')).hexdigest()[:5]
        if 真k not in self.d:
            self.d[真k] = [(k, v)]
        else:
            原 = self.d[真k]
            for i, (kk, vv) in enumerate(原):
                if kk == k:
                    原[i] = kk, v
                    break
            else:
                原.append((k, v))
            self.d[真k] = 原

    def items(self):
        for l in self.d.values():
            yield from l

    __iter__ = __len__ = __delitem__ = lambda: 0/0
