from collections.abc import Mapping, MutableMapping
import copy
from pathlib import Path
import tomllib
from typing import Any

CONFIG_DEFAULT = {
    "filter": {"drawing": {"min-area": 500}},
    "crop": {"enable": False},
    "output": {
        "size": "letter",
        "template": [
            [10, 13, 301, 233],
            [314, 13, 601, 233],
            [10, 246, 301, 454],
            [314, 246, 601, 454],
            [10, 465, 202, 769],
            [212, 465, 400, 769],
            [409, 465, 601, 770],
        ],
    },
}


def merge_mapping[T: MutableMapping[str, Any]](
    base: T, updates: Mapping[str, Any]
) -> T:
    new_map = copy.deepcopy(base)
    for key, val in updates.items():
        match val:
            case Mapping():
                new_map[key] = merge_mapping(new_map.get(key, {}), val)
            case _:
                new_map[key] = val
    return new_map


def load_config(path: Path) -> dict:
    with open(path, "rb") as fp:
        conf = tomllib.load(fp)

    return merge_mapping(CONFIG_DEFAULT, conf)
