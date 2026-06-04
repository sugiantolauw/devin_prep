#!/usr/bin/env python3
"""Render a static dashboard screenshot as PNG using Pillow only (no browser).

Produces docs/dashboard_screenshot.png — a representative snapshot of the
dashboard showing the four demo findings in their final states.
"""
from __future__ import annotations

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit("pip install Pillow")

# --------------- layout constants ---------------
W, H = 1200, 680
BG       = (13,  17,  23)   # #0d1117
SURFACE  = (22,  27,  34)   # #161b22
BORDER   = (33,  38,  45)   # #21262d
FG       = (230, 237, 243)  # #e6edf3
MUTED    = (139, 148, 158)  # #8b949e
GREEN    = (63,  185, 80)   # #3fb950
YELLOW   = (210, 153, 34)   # #d29922
RED      = (248, 81,  73)   # #f85149
BLUE     = (88,  166, 255)  # #58a6ff
PURPLE   = (188, 140, 255)  # #bc8cff

STATUS_COLORS = {
    "completed":   ((17, 46, 28),   GREEN),
    "running":     ((13, 37, 56),   BLUE),
    "needs_input": ((45, 31, 58),   PURPLE),
    "failed":      ((52, 17, 17),   RED),
    "pending":     ((45, 42, 18),   YELLOW),
}
SEV_COLORS = {"critical": RED, "high": (219,109,40), "medium": YELLOW, "low": MUTED}

def font(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()

def font_bold(size: int):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except OSError:
        return font(size)

def pill(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, status: str) -> None:
    bg, fg = STATUS_COLORS.get(status, (SURFACE, MUTED))
    tw = draw.textlength(text, font=font(11))
    px, py = 8, 3
    draw.rounded_rectangle([x, y, x + tw + px*2, y + 18], radius=9, fill=bg)
    draw.text((x + px, y + py), text, font=font(11), fill=fg)

def card(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, label: str, value: str, vcolor=FG) -> None:
    draw.rounded_rectangle([x, y, x+w, y+72], radius=10, fill=SURFACE, outline=BORDER)
    draw.text((x+14, y+12), label.upper(), font=font(10), fill=MUTED)
    draw.text((x+14, y+32), value, font=font_bold(26), fill=vcolor)

def render() -> Path:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # --- header ---
    d.text((28, 20), "🛡  Sentinel — Autonomous Remediation Pipeline", font=font_bold(16), fill=FG)
    d.text((28, 44), "Devin-powered  ·  repo your-org/superset  ·  mode mock  ·  auto-refreshes every 5s",
           font=font(11), fill=MUTED)
    d.line([(0, 70), (W, 70)], fill=BORDER, width=1)

    # --- metric cards ---
    cards = [
        ("Total tasks",   "4",    FG),
        ("In flight",     "0",    YELLOW),
        ("PRs opened",    "3",    GREEN),
        ("Needs human",   "1",    YELLOW),
        ("Failed",        "0",    RED),
        ("Success rate",  "100%", FG),
        ("MTTR",          "0s",   FG),
    ]
    cx = 28
    for label, val, vc in cards:
        card(d, cx, 86, 144, label, val, vc)
        cx += 156

    # --- table header ---
    ty = 186
    d.line([(28, ty), (W-28, ty)], fill=BORDER, width=1)
    cols = [("Issue", 28), ("Title", 90), ("Sev", 370), ("Status", 440),
            ("Devin session", 560), ("Pull request", 740), ("Polls", 900)]
    for label, x in cols:
        d.text((x, ty+8), label, font=font(11), fill=MUTED)
    ty += 30
    d.line([(28, ty), (W-28, ty)], fill=BORDER, width=1)

    # --- task rows ---
    rows = [
        (101, "Upgrade Flask 2.3.3 → 3.x",              "high",     "completed",   "mock-0001", "PR #9001", 3),
        (102, "Bump pandas 2.1.4 → 2.3.x",              "medium",   "completed",   "mock-0002", "PR #9002", 3),
        (103, "Replace deprecated datetime.utcnow()",    "low",      "completed",   "mock-0003", "PR #9003", 3),
        (104, "SQLAlchemy 1.4→2.0 migration plan",       "critical", "needs_input", "mock-0004", "—",        3),
    ]
    row_h = 42
    for issue, title, sev, status, session, pr, polls in rows:
        ty += row_h
        d.text((28, ty+10),  f"#{issue}",       font=font(12), fill=FG)
        d.text((90, ty+10),  title[:38],         font=font(12), fill=FG)
        d.text((370, ty+10), sev,                font=font(12), fill=SEV_COLORS.get(sev, MUTED))
        pill(d, 440, ty+8,  status, status)
        d.text((560, ty+10), session,            font=font(12), fill=BLUE)
        pr_color = BLUE if pr != "—" else MUTED
        d.text((740, ty+10), pr,                 font=font(12), fill=pr_color)
        d.text((900, ty+10), str(polls),         font=font(12), fill=MUTED)
        d.line([(28, ty+row_h), (W-28, ty+row_h)], fill=BORDER, width=1)

    out = Path("docs/dashboard_screenshot.png")
    out.parent.mkdir(exist_ok=True)
    img.save(out, "PNG")
    return out


if __name__ == "__main__":
    out = render()
    print(f"saved → {out}")
