# -*- coding: utf-8 -*-
"""内置默认开发文档。"""

import json
import os
from typing import List, Dict


def load_default_docs() -> List[Dict[str, str]]:
    path = os.path.join(os.path.dirname(__file__), 'default_docs.json')
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            data = json.load(handle)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except Exception:
        return []
    return []