from __future__ import annotations

import json
from pathlib import Path


GOLDEN_DIR = Path(__file__).resolve().parent / "golden"


def assert_json_snapshot(name: str, payload: dict, update: bool = False) -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    path = GOLDEN_DIR / f"{name}.json"
    rendered = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if update or not path.exists():
        path.write_text(rendered, encoding="utf-8")
        return
    expected = path.read_text(encoding="utf-8")
    assert rendered == expected

