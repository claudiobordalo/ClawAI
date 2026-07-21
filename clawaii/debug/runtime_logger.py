from __future__ import annotations

import json

DEBUG = True


def log(title: str, data) -> None:
    if not DEBUG:
        return

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)

    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    else:
        print(data)

    print("=" * 80)