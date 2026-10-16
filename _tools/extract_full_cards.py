#!/usr/bin/env python3
"""사례 카드 전문 추출·감사 — 02부 교정 문장 보강 작업의 입력을 만든다.

출력
  data/cards.json      카드 전문(본문 全文 포함) — 후속 작업의 원천
  data/cards_full/C###.md   카드 1건 = 파일 1개(작업 단위)
  data/보강대상.md      교정 문장이 없는 카드 목록(작업 지시서)
"""
from __future__ import annotations
import json, re
from pathlib import Path

SRC = Path.home() / "AppData/Local/hermes/cron/output/288500143dff"
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CIRCLED = "①②③④⑤⑥⑦⑧"
BAD = ("샘플 자기검증", "전수 점검", "자기검증")


def blocks(text: str):
    lines = text.splitlines()
    for s in [i for i, l in enumerate(lines) if "원문 점검" in l]:
        e = next((i for i in range(s + 1, len(lines))
                  if lines[i].startswith(("──", "■", "## "))), len(lines))
        yield lines[s + 1:e]


def parse(text: str, date: str):
    cut = text.rfind("## Response")
    if cut != -1:
        text = text[cut:]
    headB = re.compile(r"^\s*\*\*\s*([①-⑧]{1,5})\s*[—-]\s*(.*?)\*\*\s*(.*)$")
    headA = re.compile(r"^\s*·\s*\*\*\s*([①-⑧])\s*([^*]{0,14}?)\*\*\s*[—-]\s*(.*)$")
    cards = []
    for block in blocks(text):
        cur = None
        for ln in block:
            mB = headB.match(ln)
            mA = None if mB else headA.match(ln)
            if mB:
                if cur:
                    cards.append(cur)
                cur = {"형식": "B", "원칙": mB.group(1), "요지": mB.group(2).strip(), "본문": [mB.group(3)]}
            elif mA:
                if cur:
                    cards.append(cur)
                cur = {"형식": "A", "원칙": mA.group(1), "요지": mA.group(2).strip(), "본문": [mA.group(3)]}
            elif cur is not None:
                cur["본문"].append(ln)
        if cur:
            cards.append(cur)
    out = []
    for c in cards:
        body = "\n".join(c["본문"]).strip()
        # 교정 문장 후보: ① '바로잡은 문장…:' 뒤 문장 ② '바로잡'이 들어간 문장
        fix = ""
        m = re.search(r"바로잡은\s*문장[^:：]{0,24}[:：]\s*(.+)", body, re.S)
        if m:
            fix = m.group(1).strip()
            body = body[:m.start()].strip()
        else:
            m2 = re.search(r"[^\n]*바로잡[^\n]*", body)
            if m2:
                fix = m2.group(0).strip()
        urls = [u for _, u in re.findall(r"\[([^\]]{2,80})\]\((https?://[^)\s]+)\)", body)]
        out.append({
            "회차": date, "형식": c["형식"], "원칙": c["원칙"], "요지": re.sub(r"\s+", " ", c["요지"])[:200],
            "본문": re.sub(r"[ \t]+", " ", body).strip(),
            "교정문장": re.sub(r"\s+", " ", fix).strip(),
            "URL": urls,
            "자기검증": any(b in body[:80] for b in BAD),
        })
    return out


def main() -> None:
    DATA.mkdir(exist_ok=True)
    (DATA / "cards_full").mkdir(exist_ok=True)
    rows, seenB, seenA = [], set(), set()
    for f in sorted(SRC.glob("*.md")):
        for r in parse(f.read_text(encoding="utf-8", errors="replace"), f.stem[:10]):
            if r["형식"] == "B":
                k = (r["원칙"], r["요지"][:40])
                if k in seenB:
                    continue
                seenB.add(k)
            else:
                k = (r["원칙"], str(len(r["본문"])) + r["교정문장"][:40])
                if k in seenA:
                    continue
                seenA.add(k)
            rows.append(r)
    for i, r in enumerate(rows, 1):
        r["카드ID"] = f"C{i:03d}"

    (DATA / "cards.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    B = [r for r in rows if r["형식"] == "B" and not r["자기검증"]]
    A = [r for r in rows if r["형식"] == "A" and not r["자기검증"]]
    nodefix = [r for r in B if not r["교정문장"]]
    nourl = [r for r in B if not r["URL"]]

    for r in rows:
        (DATA / "cards_full" / f"{r['카드ID']}.md").write_text(
            f"# {r['카드ID']} · {r['회차']} · {r['형식']}형 · 원칙{r['원칙']} · {r['요지']}\n\n"
            f"URL: {', '.join(r['URL']) or '(없음)'}\n\n## 카드 본문\n\n{r['본문']}\n\n"
            f"## 기존 교정 문장\n\n{r['교정문장'] or '(없음 — 보강 대상)'}\n",
            encoding="utf-8")

    lines = ["# 02부 02 카드 보강 대상 (교정 문장 없음)", "",
             f"- B형(검증 카드) 전체: **{len(B)}장**",
             f"- 교정 문장 보유: {len(B)-len(nodefix)}장 / **없음: {len(nodefix)}장**",
             f"- 출처 URL 없음: {len(nourl)}장",
             f"- A형(판정 카드, 참고): {len(A)}장", "", "## 보강 대상 목록", ""]
    for r in nodefix:
        lines += [f"### {r['카드ID']} · {r['회차']} · 원칙{r['원칙']} · {r['요지']}", "",
                  f"- URL: {', '.join(r['URL']) or '(없음)'}",
                  f"- 본문(앞 400자): {r['본문'][:400]}", ""]
    (DATA / "보강대상.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"카드 {len(rows)}장 (B {len(B)} · A {len(A)} · 자기검증 제외 "
          f"{len(rows)-len(B)-len(A)}장)")
    print(f"  B형 교정문장 없음: {len(nodefix)}장 · URL 없음: {len(nourl)}장")
    print(f"  출력: data/cards.json · data/cards_full/ · data/보강대상.md")
    print("  원칙 분포(B):", " ".join(f"{c}{sum(1 for r in B if c in r['원칙'])}" for c in CIRCLED))


if __name__ == "__main__":
    main()
