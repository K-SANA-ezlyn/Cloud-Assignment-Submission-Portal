"""
generate_architecture_diagram.py — renders docs/assets/architecture.png

A clean, dependency-light (Pillow only) block diagram of the system
architecture for the README and reports. Re-run any time:
    python scripts/generate_architecture_diagram.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1180, 820
SCALE = 2  # supersampling for crisp text

BOXES = [
    # (x, y, w, h, title, subtitle, fill, outline)
    (430, 30, 320, 74, "STUDENT / TEACHER", "browser (any device)", "#eaf1ff", "#2456e6"),
    (400, 150, 380, 74, "REACT SPA  (frontend/)", "Vercel hosting · CDN · role-aware routes", "#eaf1ff", "#2456e6"),
    (330, 272, 520, 96, "FASTAPI REST API  (backend/app.py)", "CORS · rate limiting · request logging · RBAC · error contracts", "#fff7e6", "#b96d00"),
    (90, 430, 440, 96, "CLOUD DATABASE", "SQLite  ⇄  Supabase Postgres\ncloud/database_service.py · SQLAlchemy ORM", "#e9f7ee", "#1a7f4e"),
    (650, 430, 440, 96, "OBJECT STORAGE", "uploads/ folder  ⇄  Supabase private bucket\ncloud/storage_service.py · signed URLs", "#e9f7ee", "#1a7f4e"),
    (90, 580, 440, 84, "AUTH SERVICE", "bcrypt · JWT issue/verify · invite-gated roles\ncloud/auth_service.py · utils/security.py", "#f3e9ff", "#6d3fb4"),
    (650, 580, 440, 84, "OBSERVABILITY & CI/CD", "/api/health* probes · logs · GitHub Actions\npytest + build → auto-deploy", "#fdeaea", "#c6323c"),
]

ARROWS = [
    ((590, 104), (590, 150), ""),            # users -> SPA
    ((590, 224), (590, 272), "HTTPS + JWT"),  # SPA -> API
    ((430, 368), (310, 430), ""),            # API -> DB
    ((750, 368), (870, 430), ""),            # API -> storage
    ((310, 526), (310, 580), ""),            # DB -> auth (column)
    ((870, 526), (870, 580), ""),            # storage -> ops
]


def font(size, bold=True):
    name = "arialbd.ttf" if bold else "arial.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def draw(canvas, box):
    d = ImageDraw.Draw(canvas)
    for (x, y, w, h, title, sub, fill, outline) in BOXES:
        d.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=fill, outline=outline, width=3)
        d.text((x + w / 2, y + 22), title, font=font(21), fill="#1c2430", anchor="mm")
        for i, line in enumerate(sub.split("\n")):
            d.text((x + w / 2, y + 46 + i * 17), line, font=font(15, bold=False), fill="#4a5568", anchor="mm")

    for ((x1, y1), (x2, y2), label) in ARROWS:
        d.line([x1, y1, x2, y2], fill="#5a6472", width=3)
        # arrowhead
        d.polygon([(x2, y2), (x2 - 6, y2 - 12), (x2 + 6, y2 - 12)], fill="#5a6472")
        if label:
            d.text(((x1 + x2) / 2 + 12, (y1 + y2) / 2), label, font=font(15, bold=False), fill="#5a6472", anchor="lm")

    d.text((W / 2, H - 60), "Cloud-Based Student Assignment Submission & Feedback Portal",
           font=font(22), fill="#1c2430", anchor="mm")
    d.text((W / 2, H - 32), "one codebase — LOCAL mode (SQLite + folder) or CLOUD mode (Supabase) via environment variables",
           font=font(15, bold=False), fill="#5a6472", anchor="mm")


def main():
    img = Image.new("RGB", (W * SCALE, H * SCALE), "white")
    draw(img, SCALE)
    out = Path(__file__).resolve().parent.parent / "docs" / "assets" / "architecture.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img = img.resize((W, H), Image.LANCZOS)
    img.save(out)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
