#!/usr/bin/env python3
"""A형(원칙 전수 판정) 카드 → 훈련 세트(기사 1편 × 8원칙) 구성.

크론 산출물의 '■ 타깃 (가이드 위반 기사)' 줄을 블록마다 읽어,
그 블록의 A형 카드 8장을 하나의 훈련 세트로 묶는다.
출력: data/training.json · data/training.md (검토용)
"""
from __future__ import annotations
import json, re
from pathlib import Path

SRC = Path.home() / "AppData/Local/hermes/cron/output/288500143dff"
DATA = Path(__file__).resolve().parent.parent / "data"
HEAD = re.compile(r"^\s*·\s*\*\*\s*([①-⑧])\s*([^*]{0,14}?)\*\*\s*[—-]\s*(.*)$")
TARGET = re.compile(r"^\s*[·\-]?\s*\[([^\]]+)\]\s*[`\"“](.+?)[`\"”]")


def parse_file(text: str, date: str):
    cut = text.rfind("## Response")
    if cut != -1:
        text = text[cut:]
    lines = text.splitlines()
    sets = []
    for s in [i for i, l in enumerate(lines) if "원문 점검" in l]:
        e = next((i for i in range(s + 1, len(lines))
                  if lines[i].startswith(("──", "■", "## "))), len(lines))
        # 블록 직전의 ■ 타깃 줄들 수집
        targets, back = [], s - 1
        while back >= 0 and not lines[back].startswith(("■ 원문 점검", "──", "## ")):
            if lines[back].strip().startswith(("·", "-")) and "[" in lines[back]:
                targets.insert(0, lines[back].strip())
            back -= 1
        cards, cur = [], None
        for ln in lines[s + 1:e]:
            m = HEAD.match(ln)
            if m:
                if cur:
                    cards.append(cur)
                cur = {"원칙": m.group(1), "원칙명": m.group(2).strip(), "본문": m.group(3)}
            elif cur is not None:
                cur["본문"] += " " + ln.strip()
        if cur:
            cards.append(cur)
        if not targets or len(cards) < 3:
            continue
        arts = []
        for t in targets:
            m = TARGET.search(t)
            media = m.group(1) if m else t[:20]
            title = m.group(2) if m else t[:60]
            rank = "2순위" if "2순위" in t else ("최악" if "최악" in t else "")
            pr = re.search(r"\(([①-⑧]+)\)", t)
            arts.append({"매체": media.strip(), "제목": title.strip(),
                         "순위": rank, "원칙": pr.group(1) if pr else ""})
        sets.append({"회차": date, "기사": arts,
                     "카드": [{"원칙": c["원칙"], "원칙명": c["원칙명"],
                               "본문": re.sub(r"\s+", " ", c["본문"]).strip()} for c in cards]})
    return sets


def main() -> None:
    DATA.mkdir(exist_ok=True)
    out, seen = [], set()
    for f in sorted(SRC.glob("*.md")):
        for st in parse_file(f.read_text(encoding="utf-8", errors="replace"), f.stem[:10]):
            key = (st["회차"], st["기사"][0]["제목"][:40])
            if key in seen:
                continue
            seen.add(key)
            out.append(st)
    (DATA / "training.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    md = ["# 훈련 세트 목록 (기사 1편 × 8원칙)", ""]
    for i, st in enumerate(out, 1):
        md += [f"## 세트 {i} · {st['회차']} · 카드 {len(st['카드'])}장", ""]
        for a in st["기사"]:
            md.append(f"- [{a['매체']}] {a['제목']} {a['순위']} {a['원칙']}")
        md.append("")
        for c in st["카드"]:
            md.append(f"- {c['원칙']} {c['원칙명']}: {c['본문'][:220]}")
        md.append("")
    (DATA / "training.md").write_text("\n".join(md), encoding="utf-8")

    print(f"훈련 세트 {len(out)}개 · 카드 {sum(len(s['카드']) for s in out)}장")
    for i, st in enumerate(out, 1):
        a = st["기사"][0]
        print(f"  세트{i:2d} {st['회차']} · 카드 {len(st['카드'])}장 · [{a['매체']}] {a['제목'][:52]}")


if __name__ == "__main__":
    main()
