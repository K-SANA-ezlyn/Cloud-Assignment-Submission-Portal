"""
make_demo_files.py — generates files in sample_files/ for demos and tests.

Run:  python scripts/make_demo_files.py

Creates:
  demo-submission.pdf        valid PDF (passes validation)
  demo-resubmission-v2.pdf   second valid PDF (resubmission demo)
  wrong-type-demo.exe        executable bytes (rejected: extension + content)
  fake-pdf-demo.pdf          .exe bytes renamed to .pdf (rejected: magic bytes)
  oversized-demo.pdf         ~12 MB valid PDF (rejected: size) — generated only
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "sample_files"

MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
    b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
    b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
    b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
    b"4 0 obj << /Length 90 >> stream\n"
    b"BT /F1 18 Tf 72 720 Td (Cloud Assignment Portal - demo submission) Tj ET\n"
    b"endstream endobj\n"
    b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
    b"trailer << /Root 1 0 R >>\n"
    b"%%EOF\n"
)


def write(name: str, data: bytes) -> None:
    OUT.mkdir(exist_ok=True)
    path = OUT / name
    path.write_bytes(data)
    print(f"wrote {path} ({len(data)} bytes)")


def main() -> None:
    write("demo-submission.pdf", MINIMAL_PDF)
    write(
        "demo-resubmission-v2.pdf",
        MINIMAL_PDF.replace(b"demo submission", b"RESUBMITTED version 2"),
    )
    write("wrong-type-demo.exe", b"MZ\x90\x00" + b"\x00" * 256)
    write("fake-pdf-demo.pdf", b"MZ\x90\x00pretending to be a pdf")
    write("oversized-demo.pdf", MINIMAL_PDF + b"% padding " * (1024 * 1024))  # ~11 MB


if __name__ == "__main__":
    main()
