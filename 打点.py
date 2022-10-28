import time
import types
import random

from tqdm import tqdm as _tqdm
from pypinyin import pinyin, Style
from prometheus_client import Gauge, Histogram


_gauge_dict = {}
_id = random.randint(2**60, 2**62)


def _翻译(s):
    if s.isascii():
        q = s
    else:
        q = '_'.join([i[0] for i in pinyin(s, style=Style.NORMAL)])
    return q.replace('(', '_').replace(')', '_').replace('（', '_').replace('）', '_').replace(' ', '_')


def _display(self, *li, **d):
    if self.metrics_name:
        _gauge_dict[self.metrics_name].set(self.n)
        if self.total:
            _gauge_dict[self.metrics_name_max].set(self.total)
    return _tqdm.display(self, *li, **d)


def tqdm(*li, **d):
    self = _tqdm(*li, **d)
    if self.desc:
        self.metrics_name = _翻译(self.desc)
        if self.metrics_name not in _gauge_dict:
            _gauge_dict[self.metrics_name] = Gauge(self.metrics_name, self.metrics_name, labelnames=['sese_id']).labels(sese_id=_id)
        self.metrics_name_max = _翻译(self.desc + '马克思')
        if self.metrics_name_max not in _gauge_dict:
            _gauge_dict[self.metrics_name_max] = Gauge(self.metrics_name_max, self.metrics_name_max, labelnames=['sese_id']).labels(sese_id=_id)
        self.display = types.MethodType(_display, self)
    return self


def tqdm面板(l: list):
    return {x: tqdm(desc=x, ncols=70) for x in l}


def 计时打点(f):
    buckets = (.05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0, float("inf"))
    h = Histogram(_翻译(f.__name__) + '_time', f.__name__ + '计时', buckets=buckets, labelnames=['sese_id']).labels(sese_id=_id)
    t = _tqdm(bar_format='{desc}: {n:.3f}s', desc=f.__name__ + '平均用时')
    def 新f(*li, **d):
        st = time.time()
        r = f(*li, **d)
        if t.n == 0:
            now = time.time() - st
        else:
            now = t.n * 0.95 + (time.time() - st) * 0.05
        t.update(now - t.n)
        return r
    return h.time()(新f)


def 直方图打点(name, buckets):
    h = Histogram(_翻译(name), name, buckets=buckets, labelnames=['sese_id']).labels(sese_id=_id)
    return h
