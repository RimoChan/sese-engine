import json
from pathlib import Path


def 繁荣表():
    if not Path('savedata/繁荣.json').is_file():
        return {}
    with open('savedata/繁荣.json', encoding='utf8') as f:
        d = json.load(f)
    总 = sum(d.values())
    d = {k: v/总*300000 for k, v in d.items()}
    for k, v in d.items():
        now = k
        while True:
            now = '.'.join(now.split('.')[1:])
            if now not in d:
                break
            if d[now] < v:
                d[now] = v
    return d
