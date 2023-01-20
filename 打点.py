import os
import sys
import time
import types
import random

from tqdm import tqdm as _tqdm
from pypinyin import pinyin, Style
from prometheus_client import Gauge, Histogram, Counter, REGISTRY

import 配置


_collector_dict = {}
_id = random.randint(2**60, 2**62)
_entry = os.path.basename(sys.argv[0])
Gauge('start_time', 'start_time', labelnames=['sese_id', 'entry']).labels(sese_id=_id, entry=_entry).set(time.time())
_config_gauge = Gauge('config', 'config', labelnames=['config_key', 'sese_id', 'entry'])
for k, v in 配置.__dict__.items():
    if isinstance(v, (int, float)):
        _config_gauge.labels(config_key=k, sese_id=_id, entry=_entry).set(v)


def _翻译(s):
    if s.isascii():
        q = s
    else:
        q = '_'.join([i[0] for i in pinyin(s, style=Style.NORMAL)])
    q = q.replace('(', '_').replace(')', '_').replace('（', '_').replace('）', '_').replace(' ', '_')
    assert q.isascii(), '怪欸'
    return q


def _display(self, *li, **d):
    if self.metrics_name:
        _collector_dict[self.metrics_name].set(self.n)
        if self.total:
            _collector_dict[self.metrics_name_max].set(self.total)
    return _tqdm.display(self, *li, **d)


def tqdm(*li, **d):
    self = _tqdm(*li, **d)
    if self.desc:
        self.metrics_name = _翻译(self.desc)
        if self.metrics_name not in _collector_dict:
            _collector_dict[self.metrics_name] = Gauge(self.metrics_name, self.metrics_name, labelnames=['sese_id', 'entry']).labels(sese_id=_id, entry=_entry)
        self.metrics_name_max = _翻译(self.desc + '马克思')
        if self.metrics_name_max not in _collector_dict:
            _collector_dict[self.metrics_name_max] = Gauge(self.metrics_name_max, self.metrics_name_max, labelnames=['sese_id', 'entry']).labels(sese_id=_id, entry=_entry)
        self.display = types.MethodType(_display, self)
    return self


def tqdm面板(l: list):
    return {x: tqdm(desc=x, ncols=70) for x in l}


def 计时打点(f):
    buckets = 0.01, 0.02, 0.03, 0.05, 0.07, 0.09, 0.12, 0.15, 0.18, 0.22, 0.26, 0.31, 0.37, 0.44, 0.52, 0.61, 0.71, 0.83, 0.96, 1.12, 1.30, 1.51, 1.74, 2.02, 2.33, 2.69, 3.11, 3.58, 4.13, 4.76, 5.49, 6.32, 7.28, 8.39, 9.66, 11.12, float("inf")
    h = Histogram(_翻译(f.__name__) + '_time', f.__name__ + '计时', buckets=buckets, labelnames=['sese_id', 'entry']).labels(sese_id=_id, entry=_entry)
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
    h = Histogram(_翻译(name), name, buckets=buckets, labelnames=['sese_id', 'entry']).labels(sese_id=_id, entry=_entry)
    return h
