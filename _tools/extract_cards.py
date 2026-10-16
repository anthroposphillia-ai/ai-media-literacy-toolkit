#!/usr/bin/env python3
"""AI뉴스·미디어비평 크론 산출물 → 사례 카드 추출·태깅.

입력: %LOCALAPPDATA%\\hermes\\cron\\output\\288500143dff\\*.md
출력: 사례카드.csv · 사례카드.md · 태깅통계.md
카드 1건 = 원문 점검 블록의 항목 1개(원칙 번호 + 위반 요지 + 바로잡은 문장 + 검증 출처).
"""
from __future__ import annotations
import csv, json, re, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

SRC = Path.home() / "AppData/Local/hermes/cron/output/288500143dff"
OUT = Path(__file__).resolve().parent.parent          # AI미디어리터러시/
CIRCLED = "①②③④⑤⑥⑦⑧"
PRINCIPLE_NAMES = {
    "①": "의인화 금지 — AI를 인간 행위자로 만들지 않는다",
    "②": "책임 주체 명시 — 도입·운영을 결정한 사람을 밝힌다",
    "③": "기술적 한계 공개 — 과제·비교집합·조건·데이터 범위",
    "④": "맥락 제시 — 수치를 미래 전체로 부풀리지 않는다",
    "⑤": "이해관계 공개 — '주장'과 '사실'을 구분한다",
    "⑥": "비용과 편익 동시 제시 — 무엇을 얻고 무엇을 치렀나",
    "⑦": "검증 가능한 출처 공개 — 기관·날짜·보고서명·링크",
    "⑧": "대안·선택지 제시 — 결정론 대신 사회적 선택",
}


def _blocks(text: str) -> list[list[str]]:
    """'■ 원문 점검 (8원칙)' 블록을 전부 찾아 반환(파일당 여러 이슈가 들어 있다)."""
    lines = text.splitlines()
    starts = [i for i, l in enumerate(lines) if "원문 점검" in l]
    out = []
    for s in starts:
        e = next((i for i in range(s + 1, len(lines))
                  if lines[i].startswith(("──", "■", "## "))), len(lines))
        out.append(lines[s + 1:e])
    return out


def cards_from(text: str, date: str) -> list[dict]:
    """원문 점검 블록들에서 카드 항목을 뽑는다. (앞부분 프롬프트/직전 실행분은 버린다)

    두 세대의 출력 형식을 모두 처리한다.
      A형(구형, ~10-13): `· **①의인화** — 설명`  (기사 1건 × 8원칙 전수 = 판정 실습용)
      B형(신형, 10-14~): `**①⑧ — 요지** — 원문 대조 설명` + `· *바로잡은 문장(최악)*:` (검증 사례용)
    """
    cut = text.rfind("## Response")
    if cut != -1:
        text = text[cut:]
    headB = re.compile(r"^\s*\*\*\s*([①-⑧]{1,5})\s*[—-]\s*(.*?)\*\*\s*(.*)$")
    headA = re.compile(r"^\s*·\s*\*\*\s*([①-⑧])\s*([^*]{0,14}?)\*\*\s*[—-]\s*(.*)$")
    out: list[dict] = []
    for block in _blocks(text):
        cur: dict | None = None
        for ln in block:
            mB = headB.match(ln)
            mA = None if mB else headA.match(ln)
            if mB:
                if cur:
                    out.append(cur)
                cur = {"형식": "B", "원칙": mB.group(1), "요지": mB.group(2).strip(), "본문": [mB.group(3)]}
            elif mA:
                if cur:
                    out.append(cur)
                cur = {"형식": "A", "원칙": mA.group(1), "요지": mA.group(2).strip(),
                       "본문": [mA.group(3)]}
            elif cur is not None:
                cur["본문"].append(ln)
        if cur:
            out.append(cur)

    rows = []
    for i, c in enumerate(out, 1):
        body = "\n".join(c["본문"]).strip()
        fix = ""
        fm = re.search(r"바로잡은 문장[^:：]{0,20}[:：]\s*(.+)", body, re.S)
        if fm:
            fix = fm.group(1).strip().strip("*").strip()
            body = body[:fm.start()].strip()
        urls = re.findall(r"\[([^\]]{2,80})\]\((https?://[^)\s]+)\)", body)
        domains = sorted({re.sub(r"^www\.", "", u.split("/")[2]) for _, u in urls})
        rank = "2순위" if "2순위" in c["요지"] or "2순위" in body[:120] else "1순위"
        rows.append({
            "회차": date,
            "순번": i,
            "형식": c["형식"],
            "순위": rank,
            "원칙": c["원칙"],
            "원칙_개수": len(c["원칙"]),
            "요지": re.sub(r"\s+", " ", c["요지"])[:160],
            "출처매체": ", ".join(domains),
            "출처URL": urls[0][1] if urls else "",
            "출처링크수": len(urls),
            "바로잡은문장": re.sub(r"\s+", " ", fix)[:400],
            "본문발췌": re.sub(r"\s+", " ", body)[:900],
            "본문길이": len(body),
        })
    return rows


def main() -> None:
    files = sorted(SRC.glob("*.md"))
    all_rows: list[dict] = []
    per_file = {}
    seen: set[tuple[str, str]] = set()
    seen_a: set[tuple[str, str]] = set()
    for f in files:
        date = f.stem[:10]
        rows = cards_from(f.read_text(encoding="utf-8", errors="replace"), date)
        uniq = []
        for r in rows:
            if r["형식"] == "B":
                key = (r["원칙"], r["요지"][:40])
                if key in seen:          # 이전 회차와 중복된 검증 카드는 최초 회차만 남긴다
                    continue
                seen.add(key)
            else:
                # A형은 요지가 원칙명이라 카드 동일성은 본문으로 판단한다.
                key = (r["원칙"], r["본문길이"], r["요지"])
                ka = (r["원칙"], str(r["본문길이"]) + r["바로잡은문장"][:40])
                if ka in seen_a:
                    continue
                seen_a.add(ka)
            uniq.append(r)
        per_file[date] = len(uniq)
        all_rows += uniq
    for i, r in enumerate(all_rows, 1):
        r["카드ID"] = f"C{i:03d}"

    OUT.mkdir(parents=True, exist_ok=True)
    fields = list(all_rows[0].keys())
    with (OUT / "사례카드.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(all_rows)

    # ── 통계
    pc = Counter()
    for r in all_rows:
        for ch in r["원칙"]:
            pc[ch] += 1
    dom = Counter()
    for r in all_rows:
        for d in [x.strip() for x in r["출처매체"].split(",") if x.strip()]:
            dom[d] += 1

    stats = [
        "# 사례 카드 태깅 통계",
        "",
        f"- 원재료: AI뉴스·미디어비평 {len(files)}회차 ({min(per_file)} ~ {max(per_file)})",
        f"- **추출 카드: {len(all_rows)}건**",
        f"- 1순위 {sum(1 for r in all_rows if r['순위']=='1순위')}건 · 2순위 {sum(1 for r in all_rows if r['순위']=='2순위')}건",
        f"- 복합 위반(원칙 2개 이상 지목): {sum(1 for r in all_rows if r['원칙_개수']>1)}건",
        f"- 회차당 카드: 평균 {len(all_rows)/len(files):.1f}건",
        "",
        "## 원칙별 지목 횟수 (많은 순 = 독자가 가장 자주 만나는 함정)",
        "",
        "| 원칙 | 지목 | 비중 | 무엇을 뜻하나 |",
        "|---|---|---|---|",
    ]
    for ch, n in pc.most_common():
        stats.append(f"| {ch} | {n} | {n/len(all_rows)*100:.0f}% | {PRINCIPLE_NAMES[ch].split(' — ')[1]} |")
    stats += ["", "## 출처 매체 상위 (비평 대상이 어디서 오는가)", "", "| 매체 | 건수 |", "|---|---|"]
    for d, n in dom.most_common(20):
        stats.append(f"| {d} | {n} |")
    empty = [r for r in all_rows if not r["바로잡은문장"]]
    stats += ["", f"## 품질 점검", "",
              f"- 교정 문장 없는 카드: **{len(empty)}건**" + (" ✅" if not empty else " ⚠️"),
              f"- 출처 URL 없는 카드: {sum(1 for r in all_rows if not r['출처URL'])}건",
              f"- 출처 링크 3개 이상 카드: {sum(1 for r in all_rows if r['출처링크수']>=3)}건"]
    (OUT / "태깅통계.md").write_text("\n".join(stats), encoding="utf-8")

    # ── 마크다운 카드 목록
    md = ["# 사례 카드 목록 (원칙 태깅)", ""]
    by_principle = defaultdict(list)
    for r in all_rows:
        by_principle[r["원칙"][0]].append(r)
    for ch in CIRCLED:
        rows = by_principle.get(ch, [])
        md += [f"## {ch} {PRINCIPLE_NAMES[ch]} — {len(rows)}건", ""]
        for r in rows[:60]:
            md += [f"- **{r['회차']} {r['순위']}** · 원칙 {r['원칙']} · {r['출처매체']}",
                   f"  - 요지: {r['요지']}",
                   f"  - 교정: {r['바로잡은문장'][:200]}" + ("…" if len(r['바로잡은문장']) > 200 else "")]
        md.append("")
    (OUT / "사례카드.md").write_text("\n".join(md), encoding="utf-8")

    print(f"회차 {len(files)}건 · 카드 {len(all_rows)}건 추출")
    print(f"  교정문장 있음 {len(all_rows)-len(empty)} / 없음 {len(empty)}")
    print(f"  회차당 평균 {len(all_rows)/len(files):.1f}건")
    print("  원칙 분포:", " ".join(f"{k}{v}" for k, v in pc.most_common()))
    print("  상위 매체:", ", ".join(f"{d}({n})" for d, n in dom.most_common(6)))
    print("  출력:", OUT / "사례카드.csv", OUT / "사례카드.md", OUT / "태깅통계.md")


if __name__ == "__main__":
    main()
