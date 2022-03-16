import struct
import base64
import hashlib
import urllib.parse
from typing import MutableMapping

import brotli
from rimo_storage import 超dict

from 类 import 阵


def dump(o: 阵) -> bytes:
    c = [*zip(*o)] or ([], [])
    n = len(c[0])
    吸1 = [x.encode('utf8') for x in c[1]]
    字符串长度 = [len(s) for s in 吸1]
    文hint = ''.join([f'{x}s' for x in 字符串长度])
    nz = struct.pack('i', n)
    内容 = struct.pack(f'{n}h{n}e{文hint}', *字符串长度, *c[0], *吸1)
    z = nz+内容
    return z


def load(b: bytes) -> 阵:
    n = struct.unpack('i', b[:4])[0]
    字符串长度 = struct.unpack(f'{n}h', b[4:4+n*2])
    吸0 = struct.unpack(f'{n}e', b[4+n*2:4+n*4])
    文hint = ''.join([f'{x}s' for x in 字符串长度])
    吸1 = struct.unpack(文hint, b[4+n*4:])
    吸1 = [x.decode('utf8') for x in 吸1]
    return [*zip(吸0, 吸1)]


empty = dump([])
c = lambda x: brotli.compress(x, quality=6)
d = lambda x: brotli.decompress(x) if x != b'' else empty

def 索引空间(path) -> MutableMapping[str, 阵]:
    return 超dict(path, compress=(c, d), serialize=(dump, load))


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

    __iter__ = __len__ = __delitem__ = lambda: 0/0


class 网站信息表(超dict):
    def __init__(self, path):
        super().__init__(path, compress=(c, brotli.decompress))

    def encode(self, s: str)->str:
        return '_'.join(map(str, s.encode('utf8')))

    def decode(self, s: str)->str:
        a = s.split('_')
        return struct.pack(f'{len(a)}B', *map(int, a)).decode('utf8')

    def __getitem__(self, k):
        try:
            return super().__getitem__(self.encode(k))
        except brotli.error:
            print(f'读取网站信息「{k}」时解压失败了！')
            return {}

    def __setitem__(self, k, v):
        return super().__setitem__(self.encode(k), v)

    def __iter__(self):
        for i in super().__iter__():
            yield self.decode(i)
    __delitem__ = lambda: 0/0
