#!/usr/bin/env python3
"""build_part2.py 의 사건 메타데이터를 data/stories.json 으로 내보낸다(갱신 도구의 입력)."""
from __future__ import annotations
import importlib.util, json
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main() -> None:
    bp = load("build_part2", TOOLS / "build_part2.py")
    data = {"intro": bp.INTRO, "stories": [list(s) for s in bp.STORIES]}
    out = ROOT / "data" / "stories.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    n_cards = sum(len(s[2]) for s in data["stories"])
    print(f"내보냄: {out} · 사건 {len(data['stories'])}건 · 카드 {n_cards}장")


if __name__ == "__main__":
    main()
