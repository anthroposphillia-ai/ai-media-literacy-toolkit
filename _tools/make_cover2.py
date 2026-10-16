#!/usr/bin/env python3
"""《AI 미디어 리터러시》 표지 생성 — PIL 직접 조판(한글 안 깨짐).

디자인: 8원칙을 실측 비중과 함께 칩으로 노출. 단순·저밀도·고판독.
출력: 위키독스_책/assets/cover.png (1200x1600)
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 1600
BG = (250, 250, 252)
INK = (17, 22, 32)
MUTED = (108, 116, 132)
FONTS = Path("C:/Windows/Fonts")

# (원칙, 이름, 실측 비중)
ROWS = [
    ("③", "기술적 한계 공개", "27%", "#F59E0B"),
    ("⑤", "이해관계 공개", "21%", "#8B5CF6"),
    ("⑦", "검증 가능한 출처", "18%", "#EC4899"),
    ("④", "맥락 제시", "17%", "#10B981"),
    ("⑧", "대안·선택지", "13%", "#6366F1"),
    ("⑥", "비용과 편익", "11%", "#0EA5E9"),
    ("①", "의인화 금지", "7%", "#2563EB"),
    ("②", "책임 주체 명시", "7%", "#EF4444"),
]


def rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def f(name: str, size: int):
    return ImageFont.truetype(str(FONTS / name), size)


def main() -> None:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    M = 92
    d.rectangle([0, 0, W, 18], fill=rgb("#111827"))

    y = 92
    d.text((M, y), "AI 미디어 리터러시", font=f("malgunbd.ttf", 100), fill=INK); y += 128
    d.text((M, y), "AI 뉴스기사를 판정하는 8원칙", font=f("malgunbd.ttf", 56), fill=rgb("#2563EB")); y += 82
    d.rectangle([M, y, M + 150, y + 10], fill=rgb("#111827")); y += 44
    d.text((M, y), "한 문장이 몇 개 원칙을 어겼는지 세는 법", font=f("malgun.ttf", 34), fill=MUTED); y += 48
    d.text((M, y), "실제 기사 107장 판정 기록에서 뽑은 기준", font=f("malgun.ttf", 34), fill=MUTED); y += 62

    # 8원칙 칩 (2열 × 4행)
    cw, ch, gapx, gapy = 498, 104, 24, 18
    for i, (num, name, pct, col) in enumerate(ROWS):
        cx = M + (cw + gapx) * (i % 2)
        cy = y + (ch + gapy) * (i // 2)
        d.rounded_rectangle([cx, cy, cx + cw, cy + ch], 14, fill=(255, 255, 255))
        d.rounded_rectangle([cx, cy, cx + 10, cy + ch], 5, fill=rgb(col))
        d.text((cx + 30, cy + 26), num, font=f("malgunbd.ttf", 40), fill=rgb(col))
        d.text((cx + 84, cy + 32), name, font=f("malgunbd.ttf", 34), fill=INK)
        d.text((cx + cw - 96, cy + 36), pct, font=f("malgunbd.ttf", 28), fill=MUTED)
    y += (ch + gapy) * 4 + 10

    # 구성 요약
    d.line([M, y, W - M, y], fill=(224, 228, 235), width=2); y += 26
    d.text((M, y), "판정 기준 8원칙 · 사건 해부 11건 · 판정 훈련 12세트 · 발행 파이프라인", font=f("malgun.ttf", 29), fill=INK); y += 40
    d.text((M, y), "우리가 틀렸던 판정 3건과 이 책의 한계까지", font=f("malgun.ttf", 27), fill=MUTED); y += 62

    # 판정 3단계 패널
    ph = 258
    d.rounded_rectangle([M, y, W - M, y + ph], 16, fill=(241, 244, 248))
    d.text((M + 34, y + 26), "판정은 이렇게 합니다", font=f("malgunbd.ttf", 30), fill=INK)
    steps = [("1", "문제 문장을 그대로 옮겨 적는다", "요약하는 순간 판정이 흐려집니다"),
             ("2", "어긴 원칙 번호를 붙인다", "한 문장이 3~4개 원칙을 어깁니다"),
             ("3", "바로잡은 문장을 쓴다", "대체 문장을 못 쓰면 아직 판정이 아닙니다")]
    sy = y + 78
    for num, head, sub in steps:
        d.ellipse([M + 34, sy + 2, M + 66, sy + 34], fill=rgb("#111827"))
        d.text((M + 44, sy + 6), num, font=f("malgunbd.ttf", 21), fill=(255, 255, 255))
        d.text((M + 84, sy), head, font=f("malgunbd.ttf", 27), fill=INK)
        d.text((M + 84, sy + 32), sub, font=f("malgun.ttf", 23), fill=MUTED)
        sy += 60
    y += ph + 40

    d.text((M, y), "좋은 문서를 만드는 것이 아니라, 결정 지점에 걸리게 하는 것.", font=f("malgun.ttf", 26), fill=MUTED)

    d.text((M, H - 96), "wikidocs.net/book/21714", font=f("malgun.ttf", 24), fill=MUTED)
    d.text((W - M - 240, H - 96), "지은이 브룸 · 2026", font=f("malgun.ttf", 24), fill=MUTED)

    out = Path(__file__).resolve().parent.parent / "위키독스_책" / "assets" / "cover.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    print(f"저장: {out} ({out.stat().st_size/1024:.0f}KB, {W}x{H})")


if __name__ == "__main__":
    main()
