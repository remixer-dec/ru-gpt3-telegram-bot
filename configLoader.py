import os
import json


class JSONObject:
    def __init__(self, dict):
        vars(self).update(dict)


cfg_file = open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf8')
cfg = json.loads(cfg_file.read(), object_hook=JSONObject)
