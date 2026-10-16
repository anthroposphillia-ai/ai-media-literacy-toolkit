#!/usr/bin/env python3
"""02부 자동 갱신 — 새 사건을 감지해 페이지를 다시 만들고(전 부 재생성) 검증한다.

사용:
    python _tools/refresh_all.py            # 재생성 + 검증만 (push 안 함)
    python _tools/refresh_all.py --push     # 검증 통과 시 git commit + push

동작:
  1) 크론 산출물에서 카드 재추출 (교정 문장 보유 카드만 사용)
  2) 기존 교정 문장 보강 유지
  3) stories.json 에 없는 '새 사건'(회차 + 타깃 기사)을 자동 추가
  4) 02·03·05·04부 페이지 재생성 (TOC는 마지막 단계가 전체를 다시 씀)
  5) verify_book_repo.py 로 게이트 통과 확인
"""
from __future__ import annotations
import importlib.util, json, re, subprocess, sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
DATA = ROOT / "data"
PAGES = ROOT / "위키독스_책" / "pages"
CRON = Path.home() / "AppData/Local/hermes/cron/output/288500143dff"
PY = sys.executable
VERIFY = Path.home() / "AppData/Local/hermes/skills/productivity/wikidocs-publishing/scripts/verify_book_repo.py"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run(path: Path) -> None:
    r = subprocess.run([PY, str(path)], capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise SystemExit(f"[FAIL] {path.name}\n{r.stdout}\n{r.stderr}")
    print("   " + (r.stdout.strip().splitlines() or [""])[0])


def new_cards_by_block() -> list[dict]:
    """크론 산출물에서 (회차 + 타깃 기사) 블록별 B형 카드 묶음을 뽑는다."""
    headB = re.compile(r"^\s*\*\*\s*([①-⑧]{1,5})\s*[—-]\s*(.*?)\*\*\s*(.*)$")
    target = re.compile(r"^\s*[·\-]?\s*\[([^\]]+)\]\s*[`\"“](.+?)[`\"”]")
    blocks = []
    for f in sorted(CRON.glob("*.md")):
        t = f.read_text(encoding="utf-8", errors="replace")
        cut = t.rfind("## Response")
        if cut != -1:
            t = t[cut:]
        lines = t.splitlines()
        for s in [i for i, l in enumerate(lines) if "원문 점검" in l]:
            e = next((i for i in range(s + 1, len(lines))
                      if lines[i].startswith(("──", "■", "## "))), len(lines))
            targets, back = [], s - 1
            while back >= 0 and not lines[back].startswith(("■ 원문 점검", "──", "## ")):
                if lines[back].strip().startswith(("·", "-")) and "[" in lines[back]:
                    targets.insert(0, lines[back].strip())
                back -= 1
            cards, cur, fix = [], None, ""
            for ln in lines[s + 1:e]:
                m = headB.match(ln)
                if m:
                    if cur:
                        cards.append(cur)
                    cur = {"원칙": m.group(1), "요지": m.group(2).strip(), "본문": [m.group(3)]}
                elif cur is not None:
                    cur["본문"].append(ln)
            if cur:
                cards.append(cur)
            body_all = "\n".join(lines[s + 1:e])
            fm = re.search(r"바로잡은\s*문장[^:：]{0,24}[:：]\s*(.+)", body_all, re.S)
            fix = re.sub(r"\s+", " ", fm.group(1)).strip() if fm else ""
            if not targets or not cards:
                continue
            info = target.search(targets[0])
            blocks.append({
                "회차": f.stem[:10],
                "매체": (info.group(1).strip() if info else targets[0][:24]),
                "제목": (info.group(2).strip() if info else targets[0][:60]),
                "카드": [{"원칙": c["원칙"], "요지": c["요지"][:60],
                          "본문": re.sub(r"\s+", " ", " ".join(c["본문"])).strip()} for c in cards],
                "교정": fix,
            })
    return blocks


def auto_story(block: dict, card_ids: list[str], n: int) -> list:
    title = block["제목"] or f"{block['회차']} 회차 사건"
    lead = (f"수집 기록에서 자동 추가된 사건입니다. 원문은 [{block['매체']}] {block['제목']}({block['회차']})이며, "
            f"아래 판정과 교정 문장은 수집 당시의 기록 그대로입니다. 초점 문장은 다음 개정에서 보강합니다.")
    return [f"02-{n}", title, card_ids, lead, block["회차"], block["매체"], [],
            "**자동 추가된 사건입니다.** 판정 근거와 교정 문장은 검증 카드 원문을 그대로 실었습니다. "
            "이 사건의 '초점'과 도입부는 다음 개정에서 사람이 보강합니다."]


def append_new_stories() -> int:
    stories_path = DATA / "stories.json"
    data = json.loads(stories_path.read_text(encoding="utf-8"))
    cards = {c["카드ID"]: c for c in json.loads((DATA / "cards_fixed.json").read_text(encoding="utf-8"))}
    used = {cid for s in data["stories"] for cid in s[2]}
    added = 0
    for block in new_cards_by_block():
        ids = []
        for bc in block["카드"]:
            key = (bc["원칙"], bc["요지"][:40])
            for cid, c in cards.items():
                if cid in used or c["형식"] != "B" or not c["교정문장"]:
                    continue
                if c["원칙"] == bc["원칙"] and (c["요지"][:40] == key[1] or c["요지"][:40] in bc["요지"]):
                    ids.append(cid)
                    break
        if not ids:
            continue
        added += 1
        n = len(data["stories"]) + 1
        data["stories"].append(auto_story(block, ids, n))
        used.update(ids)
        print(f"   + 새 사건 02-{n}: [{block['매체']}] {block['제목'][:40]} (카드 {len(ids)}장)")
    if added:
        stories_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"   새 사건 {added}건 · 총 사건 {len(data['stories'])}건")
    return added


def main() -> None:
    push = "--push" in sys.argv
    print("[1/5] 카드 재추출·보강")
    run(TOOLS / "extract_full_cards.py")
    run(TOOLS / "apply_fixes.py")
    print("[2/5] 새 사건 감지")
    append_new_stories()
    print("[3/5] 부별 페이지 재생성 (02 → 03 → 05 → 04)")
    bp = load("build_part2", TOOLS / "build_part2.py")
    data = json.loads((DATA / "stories.json").read_text(encoding="utf-8"))
    bp.STORIES = data["stories"]
    bp.INTRO = data["intro"]
    bp.main()
    for name in ("build_part3.py", "build_part5.py", "build_part4.py"):
        load(name[:-3], TOOLS / name).main()
    print("[4/5] 게이트 검증")
    r = subprocess.run([PY, str(VERIFY), str(ROOT / "위키독스_책")], capture_output=True, text=True, encoding="utf-8")
    print(r.stdout.strip())
    if r.returncode or "OK" not in r.stdout:
        raise SystemExit("[FAIL] 검증 실패 — push하지 않습니다")
    print("[5/5] push" if push else "[5/5] push 생략 (--push 없음)")
    if push:
        repo = ROOT / "위키독스_책"
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        st = subprocess.run(["git", "status", "--porcelain"], cwd=repo,
                            capture_output=True, text=True, encoding="utf-8")
        if not (st.stdout or "").strip():
            print("   변경 없음 — commit/push 생략 (재생성 결과가 동일)")
        else:
            subprocess.run(["git", "commit", "-q", "-m", "02부 자동 갱신: 새 사건 반영 + 전 부 재생성"],
                           cwd=repo, check=True)
            subprocess.run(["git", "push", "-q", "origin", "main"], cwd=repo, check=True)
            print("   push 완료")


if __name__ == "__main__":
    main()
