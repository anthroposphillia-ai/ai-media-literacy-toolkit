#!/usr/bin/env python3
"""02부(사건 해부 11건) 페이지 생성 — 위키독스_책/pages/02-*.md + TOC 갱신.

카드 본문·교정 문장은 data/cards_fixed.json에서 자동으로 가져오고,
사건 도입부(lead)와 해석 한 줄만 사람이 쓴다(중복 서술 방지·정합 유지).
"""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ROOT / "위키독스_책" / "pages"
DATA = ROOT / "data"

PRINCIPLE = {
 "①": "의인화하지 않는다", "②": "책임의 주체를 명시한다", "③": "기술적 한계를 함께 공개한다",
 "④": "맥락을 함께 제시한다", "⑤": "이해관계를 공개한다", "⑥": "비용과 편익을 함께 제시한다",
 "⑦": "검증 가능한 출처를 공개한다", "⑧": "대안과 선택지를 함께 제시한다",
}

# (페이지번호, 제목, 카드ID, 도입부, 보도일, 원문매체, 추가URL, 이 사건이 보여주는 것)
STORIES = [
 ("02-1", "본사 3,000명 감축 — 'AI가 사람을 잘라냈다'는 서사", ["C081", "C082"],
  "한국어권에서 이 사건은 \"AI가 3,000명을 해고했다\"로 유통됐습니다. 원문(AP)의 사내 메모는 기술 변화를 배경으로 언급했을 뿐 **AI를 명시하지 않았고**, 감축 대상은 점포가 아닌 본사 조직입니다.",
  "2026-10-12", "AP / Grocery Dive · 게이트뉴스 · Food Trade News",
  [], "**제목이 확정한 인과를 본문이 부정하는 전형**입니다. 분모(본사 8,200명)와 범위(본사 조직)를 복원하면 같은 사건이 전혀 다르게 읽힙니다."),
 ("02-2", "법률 AI '1위'의 조건 — 하네스가 바뀌면 순위가 뒤집힌다", ["C083", "C084"],
  "회사 도표 안의 1위(19.17%)와 독립 리더보드의 7위가 같은 벤치마크에서 나왔습니다. 같은 모델이 하네스에 따라 23.58%·11.7%·6.67%로 세 번 다르게 보고된 기록도 있습니다.",
  "2026-10-12", "AI타임스 · CodePress(Vals AI 리더보드)",
  ["https://codepress.dev/benchmarks/harvey-lab"],
  "**\"1위\"는 조건 없는 숫자가 아니라 비교집합의 함수**임을 보여주는 사례입니다. 동시에 가격($0.15 vs $19.23)이라는 다른 축이 지워진 것도 함께 봅니다."),
 ("02-3", "NPU 사전학습 '0.99' — 상관계수의 의미가 뒤집힌다", ["C085", "C086", "C087"],
  "'0.99 상관계수'는 처리 속도 동등이 아니라 **학습 역학(training dynamics)의 유사도**입니다. 공개된 모델은 46M 파라미터 초소형 모델이고, 해설을 퍼뜨린 글 중 하나는 자사 제품임을 스스로 밝히고 있습니다.",
  "2026-10-15", "AI타임스 · QuantID(dev.to) · Hugging Face",
  ["https://www.aitimes.com/news/articleView.html?idxno=216272",
   "https://dev.to/quantid/how-to-prove-training-works-on-new-hardware-the-099-loss-trajectory-test-3390"],
  "**지표 이름과 지표 의미가 다를 때** 생기는 오독입니다. \"검증\"이라는 단어가 붙으면 독자는 조건을 묻지 않게 됩니다."),
 ("02-4", "에픽게임즈 'AI 우선' — 익명 소식통과 출처 없는 설문", ["C088", "C089"],
  "핵심 정보원은 \"공개 발언 권한이 없는 관계자들\"이고, 제목의 인용문은 게임 1편의 디렉터가 내부 메시지에 쓴 말입니다. 회사 입장은 \"개발자 역할을 대체하기 위한 조치가 아니다\"라고 본문에 적혀 있습니다.",
  "2026-10-12", "Bloomberg · AI타임스",
  ["https://www.aitimes.com/news/articleView.html?idxno=216254"],
  "**익명 소식통 + 출처 없는 통계 + 한쪽만 있는 비용**이 한 기사에 겹친 사례입니다. 세 가지가 동시에 나올 때 독자가 받는 인상은 사실보다 훨씬 강해집니다."),
 ("02-5", "베슬AI 발표회 — 취재가 아니라 발표 전재", ["C090", "C091", "C092"],
  "기사 첫 줄부터 \"발표회를 열고 … 발표했다\"로 시작하고, 이후 서술은 자사 주장과 대표·CTO 발언입니다. 전망(2,500억원)이 제목에서는 \"50배 급증\"으로 확정됩니다.",
  "2026-10-15", "AI타임스 · 연합뉴스 · 머니투데이 · 한국경제",
  ["https://www.yna.co.kr/amp/view/AKR20261015110000017",
   "https://www.mt.co.kr/amp/future/2026/10/15/2026101514410519454"],
  "**발표회 기사는 취재 기사보다 출처 등급이 낮다**는 것을 보여줍니다. 같은 발표를 다룬 복수 매체를 나란히 놓으면 어떤 수치가 확정이고 어떤 것이 목표인지 드러납니다."),
 ("02-6", "방송 한 시즌 삭제 — 'AI가 지웠다'에서 '인적 요인'까지", ["C093"],
  "익명 소식통을 인용한 \"AI 에이전트가 시즌을 삭제했다\"는 보도가 확산됐지만, 방송사 TV4는 같은 날 오후 **AI 책임을 부인**했고 이후 조사는 제작사의 인적 요인(백업 실패)으로 정리됐습니다.",
  "2026-10-14", "Aftonbladet · TV4 · Euronews",
  ["https://www.aftonbladet.se/nojesbladet/a/31oE8A/the-challenge-sverige-raderad-av-ai-bara-veckor-innan-premiaren",
   "https://www.euronews.com/2026/10/14/entire-swedish-reality-show-season-lost-weeks-before-premiere-amid-disputed-ai-claims"],
  "**속보의 제목이 몇 시간 뒤 뒤집히는 경우**입니다. 사례 카드에도 날짜와 함께 '이후 정정'을 붙여야 하는 이유가 여기 있습니다."),
 ("02-7", "미국 8개 주 오픈AI 소송 — 혐의를 평서문으로 옮긴 제목", ["C094", "C095", "C096"],
  "본문은 일관되게 \"주장했다·지적했다·밝혔다\"인데, 제목은 인용부호 안의 혐의를 확정된 결론처럼 만듭니다. 제재금 구체액과 정파 구성(8명 중 7명 공화당)도 빠져 있습니다.",
  "2026-10-14", "국민일보 · PYMNTS · Axios · 로이터",
  ["https://www.kmib.co.kr/article/view_amp.asp?arcid=9000022984",
   "https://www.theguardian.com/technology/2026/oct/14/openai-child-self-harm-lawsuit"],
  "**'제기했다'와 '인정됐다' 사이의 거리**를 보여줍니다. 소송 기사에서 판단 주체(법원)와 원고 구성을 함께 읽어야 하는 이유입니다."),
 ("02-8", "텐센트 에이전트 — 주체도 책임도 국가 프레임에 접힌다", ["C097", "C098", "C099", "C100", "C101"],
  "제목은 '텐센트 에이전트'로 주체를 확정하지만, 독립 연구진 보고서는 \"무엇이 평가되고 있었는지 깊이 불확실하다\"고 적습니다. 익명 소식통은 '텐센트 관계자'로 승격됐고, 연구진의 핵심 결론(\"텐센트 고유 문제가 아니다\")은 지워졌습니다.",
  "2026-10-15~16", "AI타임스 · SwarmChasers 보고서 · The Decoder",
  ["https://www.aitimes.com/news/articleView.html?idxno=216284",
   "https://swarmcha.se/posts/chinese-agent-fleet-full-report",
   "https://the-decoder.com/researchers-tracked-down-a-rogue-fleet-of-chinese-ai-agents-in-the-wild-and-actually-talked-to-it/"],
  "**한 사건이 ①·②·③·⑥·⑦·⑧을 동시에 어긴 최대 사례**입니다. 주체·출처 등급·책임 네 갈래가 모두 걸려 있어, 01부 8원칙을 한 번에 적용하는 훈련 재료로 씁니다."),
 ("02-9", "오픈AI-애플 기밀 — '주장'과 '합의'가 제목에서 사라진다", ["C102"],
  "오픈AI가 법원에 낸 서류는 \"주장\"이고 애플은 \"부인\"했으며, 실제로 제기된 소송은 없습니다. 제목은 미확정 주장을 서술문으로, 요청을 소송 예고로 바꿉니다.",
  "2026-10-14", "AI타임스 · The Next Web · Quartz",
  ["https://www.aitimes.com/news/articleView.html?idxno=216276",
   "https://thenextweb.com/news/openai-ex-employee-device-files-apple"],
  "**법률 기사에서 가장 자주 생기는 변형**입니다. 서류에 담긴 요청(일정 허가)이 기사에서 확정 사실(맞소송)로 바뀝니다."),
 ("02-10", "테스트넷 지갑 — '해킹'도 '절도'도 아니었다", ["C103", "C104", "C105", "C106"],
  "무대는 연습용 테스트넷이고 자금의 시장 가치는 0원입니다. 시드프레이즈는 이미 공개돼 있었고, 오픈AI 보고서는 \"실제 자금이 이전되거나 손실되지 않았다\"고 적습니다. 그런데 제목은 의도를 가진 범죄로 확정합니다.",
  "2026-10-16~17", "Gizmodo · CoinDesk · Crowdfund Insider · Engadget",
  ["https://www.coindesk.com/tech/2026/10/16/an-openai-agent-ran-out-of-ethereum-funds-and-took-from-a-wallet-it-did-not-own",
   "https://www.engadget.com/2288645/an-openai-test-agent-stole-test-ethereum-to-finish-a-coding-task/"],
  "**의인화(①)와 책임 접기(②)가 함께 일어나는 사례**입니다. '로그 AI'라는 표현이 기술적 실수(키 노출·백업·이그레스)를 지웁니다."),
 ("02-11", "브린 'RSI 궤도 진입' — 전망이 단계가 된다", ["C107"],
  "원문 발언은 \"타기 시작했다(starting to get onto that RSI treadmill)\"이고, 근거로 든 것은 모델 출시 간격입니다. 출시가 빠른 것이 자기개선의 증거는 아닙니다.",
  "2026-10-15~16", "AI타임스 · Business Insider",
  ["https://www.aitimes.com/news/articleView.html?idxno=216350",
   "https://businessinsider.com/sergey-brin-google-gemini-ai-argon-recursive-self-improvement-rsi-2026-10"],
  "**결정론(⑧)은 독자를 관객으로 만듭니다.** \"궤도에 진입했다\"는 문장이 사라지면 \"어디까지·얼마나 빠르게\"라는 질문이 되돌아옵니다."),
]

INTRO = """## 02부를 시작하며 — 사건 하나를 여러 원칙으로 본다

01부에서 8원칙을 각각 따로 익혔습니다. 실제 기사는 그렇게 생기지 않았습니다. **한 문장이 3~4개 원칙을 동시에 어깁니다.**

이 부는 2026년 10월 9일~17일, 9일간 수집한 AI 관련 기사 비평 22회차에서 **교정 문장까지 완성된 검증 카드 27장**을 **11개 사건**으로 묶었습니다. 사건 하나가 원칙 여러 개를 어긴 정도를 그대로 보여줍니다.

### 사건 카드 읽는 법

| 순서 | 보는 것 | 왜 |
|---|---|---|
| 1 | **제목과 리드** | 여기서 조건이 먼저 지워집니다 |
| 2 | **원문(또는 원 보고서)** | 기사가 지운 것을 복원할 유일한 근거입니다 |
| 3 | **원문이 지운 것** | 분모·비교집합·출처 등급·책임 주체 |
| 4 | **바로잡은 문장** | 대체 문장을 쓸 수 있어야 판정이 끝납니다 |
| 5 | **검증 출처** | 날짜와 링크가 없으면 카드가 아니라 의견입니다 |

### 이 부에 담긴 11개 사건

| # | 사건 | 어긴 원칙 | 카드 |
|---|---|---|---|
| 1 | 본사 3,000명 감축 | ③④⑤⑥⑦ | 2장 |
| 2 | 법률 AI '1위'의 조건 | ③④ | 2장 |
| 3 | NPU 사전학습 '0.99' | ③④⑤⑦ | 3장 |
| 4 | 에픽게임즈 'AI 우선' | ④⑤⑥⑦ | 2장 |
| 5 | 베슬AI 발표회 전재 | ②⑤⑥⑦⑧ | 3장 |
| 6 | 방송 한 시즌 삭제 | ③⑥ | 1장 |
| 7 | 8개 주 오픈AI 소송 | ②③⑤⑥⑦⑧ | 3장 |
| 8 | 텐센트 에이전트 | ①②③⑥⑦⑧ | 5장 |
| 9 | 오픈AI-애플 기밀 | ③⑧ | 1장 |
| 10 | 테스트넷 지갑 사건 | ①②③④⑥⑧ | 4장 |
| 11 | 브린 'RSI 궤도 진입' | ⑤⑧ | 1장 |

> **사례는 시효가 있습니다.** 각 사건에는 보도일과 원문 링크를 달았고, 이후 정정이 나온 경우(6번 사건)는 정정 내용까지 함께 적었습니다. 사건 카드를 인용할 때는 **반드시 날짜와 함께** 인용하시기 바랍니다.
"""


def render(story) -> str:
    num, title, ids, lead, date, media, extra, lesson = story
    cards = [c for c in CARDS if c["카드ID"] in ids]
    cards.sort(key=lambda c: ids.index(c["카드ID"]))
    urls, seen = [], set()
    for c in cards:
        for u in c["URL"]:
            if u not in seen:
                seen.add(u); urls.append(u)
    for u in extra:
        if u not in seen:
            seen.add(u); urls.append(u)
    principles = "".join(sorted({ch for c in cards for ch in c["원칙"]}))
    out = [f"## {title}", "", f"**사건 한 줄** — {lead}", "",
           "| 항목 | 내용 |", "|---|---|",
           f"| 보도일 | {date} |",
           f"| 원문 매체 | {media} |",
           f"| 어긴 원칙 | {principles} — " +
           ", ".join(f"{ch} {PRINCIPLE[ch]}" for ch in sorted({c2 for c in cards for c2 in c['원칙']})) + " |",
           f"| 카드 | {', '.join(ids)} (교정 문장 완성) |", "",
           "### 원문이 지운 것", ""]
    for c in cards:
        out += [f"**{c['요지']}** — 원칙 {c['원칙']} ({c['회차']})", "",
                c["본문"].strip(), "",
                "> **바로잡은 문장** — " + re.sub(r"\s+", " ", c["교정문장"]).strip(), ""]
    out += ["### 이 사건이 보여주는 것", "", lesson, "",
            "### 검증 출처", ""]
    for u in urls:
        dom = re.sub(r"^www\.", "", u.split("/")[2])
        out.append(f"- [{dom}]({u})")
    out.append("")
    return "\n".join(out)


def main() -> None:
    global CARDS
    CARDS = json.loads((DATA / "cards_fixed.json").read_text(encoding="utf-8"))
    PAGES.mkdir(parents=True, exist_ok=True)
    (PAGES / "02-0-intro.md").write_text(INTRO, encoding="utf-8")
    written = ["02-0-intro.md"]
    for story in STORIES:
        body = render(story)
        fn = f"{story[0]}.md"
        (PAGES / fn).write_text(body, encoding="utf-8")
        written.append(fn)

    # ── TOC 갱신(01부 + 02부)
    toc = ["# 목차", "",
           "- [01. 판정의 기준 — 8원칙](pages/01-0-intro.md)"]
    for n, t in [("1", "③ 기술적 한계를 함께 공개한다"), ("2", "⑤ 이해관계를 공개한다"),
                 ("3", "⑦ 검증 가능한 출처를 공개한다"), ("4", "④ 맥락을 함께 제시한다"),
                 ("5", "⑧ 대안과 선택지를 함께 제시한다"), ("6", "⑥ 비용과 편익을 함께 제시한다"),
                 ("7", "① 의인화하지 않는다"), ("8", "② 책임의 주체를 명시한다"),
                 ("9", "8원칙 판정 체크리스트")]:
        toc.append(f"  - [01-{n}. {t}](pages/01-{n}-{['limits','interests','sources','context','alternatives','costbenefit','anthropomorphism','responsibility','checklist'][int(n)-1]}.md)")
    toc += ["", "- [02. 사건 해부 — 한 사건, 여러 원칙](pages/02-0-intro.md)"]
    for story in STORIES:
        toc.append(f"  - [{story[0]}. {story[1]}](pages/{story[0]}.md)")
    (ROOT / "위키독스_책" / "TOC.md").write_text("\n".join(toc) + "\n", encoding="utf-8")
    print(f"02부 {len(STORIES)}개 사건 + 개요 생성 · TOC 갱신 · 카드 사용 {sum(len(s[2]) for s in STORIES)}장")


if __name__ == "__main__":
    CARDS: list[dict] = []
    main()
