import json
from pathlib import Path


def 繁荣表():
    if Path('savedata/繁荣.json').is_file():
        with open('savedata/繁荣.json', encoding='utf8') as f:
            d = json.load(f)
        总 = sum(d.values())
        d = {k: v/总*300000 for k, v in d.items()}
        d = {k: v for k, v in d.items() if v > 0.2}
        return d
    else:
        return {}
