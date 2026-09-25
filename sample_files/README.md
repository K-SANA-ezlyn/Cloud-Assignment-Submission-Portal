# Sample Files (dummy data)

| File | Use case | Expected result when uploaded |
|---|---|---|
| `demo-submission.pdf` | valid submission | accepted → status SUBMITTED |
| `demo-resubmission-v2.pdf` | resubmission demo | accepted as attempt #2 |
| `wrong-type-demo.exe` | wrong extension | rejected (HTTP 415) |
| `fake-pdf-demo.pdf` | `.exe` bytes renamed to `.pdf` | rejected by magic-byte check (415) |
| `oversized-demo.pdf` | size-limit test (~11 MB) | rejected (HTTP 413) — generate with the script |

`oversized-demo.pdf` is intentionally not committed (large binary).
Regenerate everything at any time:

```bash
python scripts/make_demo_files.py
```

All content is DUMMY — no real student data is ever needed.
