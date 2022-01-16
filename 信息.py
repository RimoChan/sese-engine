import json


def 繁荣表():
    with open('savedata/繁荣.json', encoding='utf8') as f:
        d = json.load(f)
    总 = sum(d.values())
    d = {k: v/总*300000 for k, v in d.items()}
    d = {k: v for k, v in d.items() if v > 0.2}
    return d
