#!/usr/bin/env python3
"""01부 페이지(.md) → 열람용 단일 HTML 미리보기 (01부_미리보기.html).

지원 서식: h2/h3, 표(|), 불릿(-), 번호목록(1.), 인용(>), 코드블록(```), 굵게, 링크, 구분선.
사용자 취향: 단순·저밀도·고판독. 좌측 페이지 탭 내비게이션 포함.
"""
from __future__ import annotations
import html, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "위키독스_책" / "pages"
OUT = ROOT / "01부_미리보기.html"

TITLES = {
    "01-0-intro": "01. 판정의 기준 — 8원칙",
    "01-1-limits": "01-1. ③ 기술적 한계를 함께 공개한다",
    "01-2-interests": "01-2. ⑤ 이해관계를 공개한다",
    "01-3-sources": "01-3. ⑦ 검증 가능한 출처를 공개한다",
    "01-4-context": "01-4. ④ 맥락을 함께 제시한다",
    "01-5-alternatives": "01-5. ⑧ 대안과 선택지를 함께 제시한다",
    "01-6-costbenefit": "01-6. ⑥ 비용과 편익을 함께 제시한다",
    "01-7-anthropomorphism": "01-7. ① 의인화하지 않는다",
    "01-8-responsibility": "01-8. ② 책임의 주체를 명시한다",
    "01-9-checklist": "01-9. 8원칙 판정 체크리스트",
}


def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s


def md(src: str) -> str:
    out, i, lines = [], 0, src.splitlines()
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):                      # 코드블록
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(html.escape(lines[i])); i += 1
            out.append("<pre>" + "\n".join(buf) + "</pre>")
        elif re.match(r"^\|.*\|$", ln) and i + 1 < len(lines) and re.match(r"^\|[\s:\-|]+\|$", lines[i + 1]):
            head = [c.strip() for c in ln.strip().strip("|").split("|")]
            i += 2
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append("<table><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
                       + "</table>")
            continue
        elif ln.startswith("### "):
            out.append(f"<h3>{inline(ln[4:])}</h3>")
        elif ln.startswith("## "):
            out.append(f"<h2>{inline(ln[3:])}</h2>")
        elif ln.startswith("> "):
            out.append(f"<blockquote>{inline(ln[2:])}</blockquote>")
        elif ln.strip() == "---":
            out.append("<hr>")
        elif re.match(r"^[-*] ", ln):
            buf = []
            while i < len(lines) and re.match(r"^[-*] ", lines[i]):
                buf.append(f"<li>{inline(lines[i][2:])}</li>"); i += 1
            out.append("<ul>" + "".join(buf) + "</ul>"); continue
        elif re.match(r"^\d+\. ", ln):
            buf = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                buf.append(f"<li>{inline(re.sub(r'^\\d+\\. ', '', lines[i]))}</li>"); i += 1
            out.append("<ol>" + "".join(buf) + "</ol>"); continue
        elif ln.strip():
            out.append(f"<p>{inline(ln)}</p>")
        i += 1
    return "\n".join(out)


def main() -> None:
    pages = sorted(SRC.glob("01-*.md"))
    nav, bodies = [], []
    for p in pages:
        title = TITLES.get(p.stem, p.stem)
        nav.append(f"<a href='#{p.stem}'>{html.escape(title)}</a>")
        bodies.append(f"<section id='{p.stem}'><div class='tag'>{html.escape(title)}</div>"
                      f"{md(p.read_text(encoding='utf-8'))}</section>")
    doc = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<title>AI 미디어 리터러시 — 01부 미리보기</title><style>
 *{{box-sizing:border-box}}
 body{{margin:0;display:flex;background:#F7F8FA;color:#171C26;
   font-family:"Malgun Gothic","맑은 고딕",sans-serif;line-height:1.75;font-size:16px}}
 nav{{width:290px;flex:0 0 290px;background:#fff;padding:24px 18px;height:100vh;overflow:auto;
   border-right:1px solid #E5E9EF;position:sticky;top:0}}
 nav h1{{font-size:17px;margin:0 0 14px}} nav a{{display:block;padding:7px 8px;color:#333A47;
   text-decoration:none;font-size:14px;border-radius:8px}}
 nav a:hover{{background:#F1F4F8;color:#2563EB}}
 main{{flex:1;padding:40px 56px 120px;max-width:900px}}
 section{{background:#fff;border-radius:14px;padding:30px 34px;margin-bottom:22px}}
 .tag{{font-size:13px;color:#6E7686;font-weight:700;letter-spacing:.02em;
   border-bottom:1px solid #EDF0F4;padding-bottom:10px;margin-bottom:6px}}
 h2{{font-size:23px;margin:18px 0 10px}} h3{{font-size:17px;margin:26px 0 8px;color:#1F2937}}
 p{{margin:0 0 10px}} ul,ol{{margin:0 0 12px;padding-left:22px}} li{{margin:4px 0}}
 table{{border-collapse:collapse;width:100%;font-size:14px;margin:12px 0 16px}}
 th,td{{border:1px solid #E5E9EF;padding:8px 11px;text-align:left;vertical-align:top}}
 th{{background:#F1F3F7}} blockquote{{margin:12px 0;padding:10px 14px;background:#F5F8FF;
   border-left:4px solid #2563EB;border-radius:0 8px 8px 0;font-size:15px}}
 pre{{background:#F1F3F7;border-radius:8px;padding:12px;overflow:auto;font-size:13px;line-height:1.5}}
 code{{background:#F1F3F7;border-radius:4px;padding:1px 5px;font-size:14px}}
 hr{{border:0;border-top:1px solid #E5E9EF;margin:22px 0}} a{{color:#2563EB}}
</style></head><body>
<nav><h1>AI 미디어 리터러시<br><span style="font-size:12px;color:#6E7686">01부 초안 · 10페이지</span></h1>
{"".join(nav)}</nav><main>{"".join(bodies)}
<p style="color:#6E7686;font-size:13px;text-align:center">02부(사례 카드) · 03부(판정 훈련) · 04부(직접 만들기) · 05부(한계·오판) 순차 추가</p>
</main></body></html>"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"저장: {OUT} ({OUT.stat().st_size/1024:.0f}KB) · 페이지 {len(pages)}개")


if __name__ == "__main__":
    main()
