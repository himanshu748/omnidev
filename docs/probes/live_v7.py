"""
Live acceptance for v0.7.0 whole-Mac RAG, fully offline.

Builds a realistic folder: a screenshot whose text exists ONLY in the image,
a decoy document, a private key and a .env that must never be indexed, then
indexes with the real embedder and asks a question answerable only via OCR.
"""

import asyncio
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / "n/omnidev/backend"))

from app.config import settings  # noqa: E402

settings.data_dir = tempfile.mkdtemp(prefix="omnidev-v7-")

from app.services import extractors, knowledge_service  # noqa: E402

ROOT = Path.home() / "omnidev-v7-livetest"


def make_screenshot(path: Path, lines: list[str]) -> None:
    """Render with a real system font, so this resembles an actual screenshot
    rather than PIL's tiny default bitmap face."""
    from PIL import Image, ImageDraw, ImageFont

    font = None
    for candidate in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNS.ttf",
    ):
        if Path(candidate).exists():
            font = ImageFont.truetype(candidate, 34)
            break
    if font is None:
        font = ImageFont.load_default()

    image = Image.new("RGB", (1100, 90 + 70 * len(lines)), "white")
    draw = ImageDraw.Draw(image)
    for index, line in enumerate(lines):
        draw.text((45, 45 + 70 * index), line, fill=(20, 20, 20), font=font)
    image.save(path)


def setup() -> None:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True)

    make_screenshot(
        ROOT / "Screenshot 2026-03-02 at 11.04.22.png",
        [
            "Vendor: Northwind Logistics",
            "Invoice INV-2026-0417   Amount due: 4,250.00 USD",
            "Payment reference QZ-88231",
        ],
    )
    (ROOT / "meeting-notes.md").write_text(
        "# Ops sync\n\nWe reviewed shipping vendors and agreed to renegotiate in Q3.\n"
        "No invoice numbers were recorded in this document.\n"
    )
    (ROOT / "budget.md").write_text("# Budget\n\nTravel and software spend for the quarter.\n")
    # These two must never be indexed.
    (ROOT / ".env").write_text("STRIPE_SECRET_KEY=sk_live_northwind_QZ_88231\n")
    (ROOT / ".ssh").mkdir()
    (ROOT / ".ssh" / "id_rsa").write_text("-----BEGIN PRIVATE KEY----- Northwind QZ-88231\n")

    print(f"folder: {ROOT}")
    print("  1 screenshot (text ONLY inside the image)")
    print("  2 markdown decoys")
    print("  1 .env + 1 id_rsa that must be refused\n")


async def main() -> None:
    setup()
    print(f"OCR available: {extractors.ocr_available()}")

    source = await knowledge_service.add_source(str(ROOT), "docs")
    started = time.time()
    await knowledge_service.index_source(source["id"])
    elapsed = time.time() - started

    status = knowledge_service.indexing_status()
    stats = await knowledge_service.index_stats()
    print(f"\nindexed in {elapsed:.1f}s")
    print(f"chunks: {stats['chunks']}  by kind: {stats['by_kind']}")
    print(f"skipped: {status['skipped']}  -> {status['message']}")

    print("\n--- Q: what is the payment reference for the Northwind invoice? ---")
    hits = await knowledge_service.search("Northwind invoice payment reference", top_k=4)
    for hit in hits:
        print(f"  [{hit['kind']}] {Path(hit['file_path']).name}  score={hit['score']}")
        print(f"      {hit['snippet'][:120].strip()}")

    top = hits[0] if hits else None
    ocr_won = bool(top and top["kind"] == "image" and "QZ-88231" in top["snippet"])

    print("\n--- exact-token query (hybrid keyword path) ---")
    exact = await knowledge_service.search("INV-2026-0417", top_k=3)
    for hit in exact:
        print(f"  [{hit['kind']}] {Path(hit['file_path']).name}")
    exact_ok = bool(exact and "INV-2026-0417" in exact[0]["snippet"])

    print("\n--- secrets must be absent from the whole index ---")
    leaked = []
    for probe in ["STRIPE_SECRET_KEY", "sk_live", "BEGIN PRIVATE KEY", "id_rsa"]:
        for hit in await knowledge_service.search(probe, top_k=10):
            if ".env" in hit["file_path"] or "id_rsa" in hit["file_path"]:
                leaked.append((probe, hit["file_path"]))
    print(f"  leaks: {leaked or 'none'}")

    mode = oct(Path(knowledge_service._db_path()).stat().st_mode & 0o777)
    print(f"\nindex file mode: {mode}")

    print("\n" + "=" * 62)
    print(f"OCR answered from image only : {'PASS' if ocr_won else 'FAIL'}")
    print(f"exact-token hybrid retrieval : {'PASS' if exact_ok else 'FAIL'}")
    print(f"no secret leaked             : {'PASS' if not leaked else 'FAIL'}")
    print(f"index not world readable     : {'PASS' if mode == '0o600' else 'FAIL'}")
    ok = ocr_won and exact_ok and not leaked and mode == "0o600"
    print("RESULT:", "V7_ACCEPTANCE_PASS" if ok else "V7_ACCEPTANCE_FAIL")


asyncio.run(main())
