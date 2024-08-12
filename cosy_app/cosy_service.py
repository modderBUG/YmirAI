import json

def _read_json(path):
    with open(path,"r",encoding="utf-8") as f:
        return json.load(f)


