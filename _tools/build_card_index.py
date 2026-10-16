#!/usr/bin/env python3
"""사례카드.csv → 열람용 단일 HTML 인덱스(카드인덱스.html).

사용자 취향: 단순·저밀도·고판독. 원칙별 묶음 + 상단 통계 + 형식 배지.
"""
from __future__ import annotations
import csv, html
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV = ROOT / "사례카드.csv"
OUT = ROOT / "카드인덱스.html"

NAMES = {
    "①": ("의인화 금지", "AI를 인간 행위자로 만들지 않는다"),
    "②": ("책임 주체 명시", "도입·운영을 결정한 사람을 밝힌다"),
    "③": ("기술적 한계 공개", "과제·비교집합·조건·데이터 범위를 함께 밝힌다"),
    "④": ("맥락 제시", "수치를 미래 전체로 부풀리지 않는다"),
    "⑤": ("이해관계 공개", "'주장'과 '사실'을 구분한다"),
    "⑥": ("비용과 편익 동시 제시", "무엇을 얻고 무엇을 치렀나"),
    "⑦": ("검증 가능한 출처 공개", "기관·날짜·보고서명·링크"),
    "⑧": ("대안·선택지 제시", "결정론 대신 사회적 선택"),
}
COLORS = {"①": "#2563EB", "②": "#EF4444", "③": "#F59E0B", "④": "#10B981",
          "⑤": "#8B5CF6", "⑥": "#0EA5E9", "⑦": "#EC4899", "⑧": "#6366F1"}


def e(s: str) -> str:
    return html.escape(s or "")


def main() -> None:
    rows = list(csv.DictReader(CSV.open(encoding="utf-8-sig")))
    dates = sorted({r["회차"] for r in rows})
    pc = Counter(c for r in rows for c in r["원칙"])
    nB = sum(1 for r in rows if r["형식"] == "B")

    parts = [f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<title>AI 미디어 리터러시 — 사례 카드 인덱스</title>
<style>
 *{{box-sizing:border-box}}
 body{{margin:0;padding:36px 40px 80px;background:#F7F8FA;color:#171C26;
   font-family:"Malgun Gothic","맑은 고딕",sans-serif;line-height:1.62}}
 h1{{font-size:30px;margin:0 0 6px}} h2{{font-size:21px;margin:44px 0 14px;
   padding-left:12px;border-left:5px solid #cbd2dc}}
 .sub{{color:#6E7686;font-size:15px;margin-bottom:22px}}
 .stats{{display:flex;gap:12px;flex-wrap:wrap;margin:0 0 8px}}
 .stat{{background:#fff;border-radius:12px;padding:14px 18px;min-width:130px}}
 .stat b{{display:block;font-size:24px}} .stat span{{color:#6E7686;font-size:13px}}
 table{{border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;
   font-size:14px;margin-bottom:8px}}
 th,td{{padding:8px 14px;text-align:left;border-bottom:1px solid #EDF0F4}}
 th{{background:#F1F3F7;font-weight:700}}
 .card{{background:#fff;border-radius:12px;padding:16px 18px;margin:10px 0;
   border-left:6px solid #ccc}}
 .meta{{font-size:13px;color:#6E7686;margin-bottom:6px}}
 .badge{{display:inline-block;font-size:11px;font-weight:700;border-radius:6px;
   padding:2px 7px;margin-right:6px;color:#fff;background:#94A3B8}}
 .badge.b{{background:#2563EB}}
 .say{{font-weight:700;margin:6px 0 4px}}
 .fix{{background:#F0F7F2;border-radius:8px;padding:9px 12px;font-size:14px;margin-top:8px}}
 .body{{font-size:14px;color:#333A47;margin-top:8px}}
 a{{color:#2563EB}} .foot{{margin-top:46px;color:#6E7686;font-size:13px}}
</style></head><body>
<h1>AI 미디어 리터러시 — 사례 카드 인덱스</h1>
<div class="sub">원재료: AI뉴스·미디어비평 크론 산출물 {len(dates)}일({dates[0]} ~ {dates[-1]}) ·
 태깅 카드 {len(rows)}장 · 위키독스 책 2부 사례 카드 선별용</div>
<div class="stats">
 <div class="stat"><b>{len(rows)}</b><span>전체 카드</span></div>
 <div class="stat"><b>{nB}</b><span>원문 검증 카드(B형)</span></div>
 <div class="stat"><b>{len(rows)-nB}</b><span>원칙 전수 판정(A형)</span></div>
 <div class="stat"><b>{len(dates)}</b><span>수집 일수</span></div>
</div>
<h2>원칙별 분포 (많은 순 = 독자가 가장 자주 만나는 함정)</h2>
<table><tr><th>원칙</th><th>지목</th><th>비중</th><th>뜻</th></tr>"""]
    for ch, n in pc.most_common():
        parts.append(f"<tr><td><b style='color:{COLORS[ch]}'>{ch}</b> {e(NAMES[ch][0])}</td>"
                     f"<td>{n}</td><td>{n/len(rows)*100:.0f}%</td><td>{e(NAMES[ch][1])}</td></tr>")
    parts.append("</table>")

    for ch, _ in pc.most_common():
        cards = [r for r in rows if ch in r["원칙"]]
        parts.append(f"<h2 style='border-color:{COLORS[ch]}'>{ch} {e(NAMES[ch][0])} — {len(cards)}장</h2>")
        for r in cards:
            badge = "b" if r["형식"] == "B" else ""
            blabel = "원문검증" if r["형식"] == "B" else "판정"
            src = (f" · <a href='{e(r['출처URL'])}' target='_blank'>{e(r['출처매체'] or '출처')}</a>"
                   if r["출처URL"] else "")
            fix = (f"<div class='fix'><b>바로잡은 문장</b> — {e(r['바로잡은문장'][:300])}</div>"
                   if r["바로잡은문장"] else "")
            parts.append(
                f"<div class='card' style='border-left-color:{COLORS[ch]}'>"
                f"<div class='meta'><span class='badge {badge}'>{blabel}</span>"
                f"{e(r['카드ID'])} · {e(r['회차'])} · {e(r['순위'])} · 원칙 {e(r['원칙'])}{src}</div>"
                f"<div class='say'>{e(r['요지'][:120])}</div>"
                f"<div class='body'>{e(r['본문발췌'][:500])}{'…' if len(r['본문발췌'])>500 else ''}</div>"
                f"{fix}</div>")

    parts.append(f"<div class='foot'>출처: 사용자 소유 크론 산출물 · 카드 태깅은 원칙 번호 기준 · "
                 f"책 2부에는 원칙별 대표 카드만 선별 수록(저작권: 원문 발췌는 짧은 인용 + 링크)</div>"
                 f"</body></html>")
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"저장: {OUT} ({OUT.stat().st_size/1024:.0f}KB) · 카드 {len(rows)}장 · 원칙 {len(pc)}종")


if __name__ == "__main__":
    main()
