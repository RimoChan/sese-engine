from gevent import monkey
monkey.patch_all()

import logging

import flask
from tqdm import tqdm

from 类 import 阵
from 存储 import 索引空间
from utils import netloc, json_loads, 小清洗

from 配置 import 单键最多url, 单键内存最多url, 单键最多相同域名url, 大清洗间隔

logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = flask.Flask(__name__)


##########
# 单键最多url = 100
# 单键内存最多url = 40
# 单键最多相同域名url = 5
# 大清洗间隔 = 1000
##########

偏执 = 0

面板 = {x: tqdm(desc=x) for x in ['内存键数', '小清洗次数']}

df = 索引空间('./savedata/键')

临时df = {}


def 消重(q: 阵) -> 阵:
    qq = []
    有 = set()
    for v, url in q:
        if url in 有:
            continue
        有.add(url)
        qq.append((v, url))
    return qq


@app.route('/l', methods=['POST'])
def l():
    global 偏执
    文件名, kvs = json_loads(flask.request.data)
    文件名 = 文件名.replace('\n', '')
    netloc(文件名)
    for k, v in kvs:
        if k not in 临时df:
            临时df[k] = []
        dfk = 临时df[k]
        dfk.append((v, 文件名))
        if len(dfk) > 单键内存最多url*2:
            面板['小清洗次数'].update(1)
            临时df[k] = 小清洗(sorted(dfk, reverse=True), 单键最多相同域名url)[:单键内存最多url]
    面板['内存键数'].n = len(临时df)
    面板['内存键数'].refresh()
    偏执 += 1
    if 偏执 > 大清洗间隔:
        面板['小清洗次数'].update(-面板['小清洗次数'].n)
        偏执 = 0
        大清洗()
    return 'ok'


def 大清洗():
    global 临时df, df
    新key数 = 0
    丢key数 = 0
    try:
        锁定df = 临时df.copy()
        临时df = {}
        for k, v in tqdm(锁定df.items(), ncols=70):
            原v = df.get(k, [])
            if not 原v:
                if len(v) == 1:
                    丢key数 += 1
                    continue
                新key数 += 1
            z = 消重(tuple(v) + tuple(原v))
            if len(z) > 单键最多url*1.25:
                z = 小清洗(sorted(z, reverse=True), 单键最多相同域名url)[:单键最多url]
            df[k] = z
    except Exception as e:
        print('完蛋了！')
        logging.exception(e)
        while True:
            ...
    print(f'清洗好了。丢弃了{丢key数}个key，新增了{新key数}个key。')


if __name__ == '__main__':
    app.run()
