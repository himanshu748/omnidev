"""Index the real ~/Desktop, which holds 19 iCloud-evicted screenshots.

Before the guard, reading one of these blocked forever at 0% CPU. This run
must finish, skip them, and say so.
"""
import asyncio, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path.home() / "n/omnidev/backend"))
from app.config import settings
settings.data_dir = tempfile.mkdtemp(prefix="omnidev-desktop-")
from app.services import knowledge_service, file_guards

async def main():
    desktop = knowledge_service.screenshots_folder()
    evicted = sum(1 for p in desktop.glob("*") if p.is_file() and file_guards.is_evicted(p))
    print(f"screenshots folder: {desktop}")
    print(f"evicted files present: {evicted}")

    source = await knowledge_service.add_source(str(desktop), "docs")
    t0 = time.time()
    await asyncio.wait_for(knowledge_service.index_source(source["id"]), timeout=480)
    elapsed = time.time() - t0

    status = knowledge_service.indexing_status()
    stats = await knowledge_service.index_stats()
    print(f"\nfinished in {elapsed:.1f}s (did NOT hang)")
    print(f"chunks {stats['chunks']}, by kind {stats['by_kind']}")
    print(f"skipped {status['skipped']}")
    print(f"message: {status['message']}")
    ok = status["skipped"].get("evicted", 0) >= 1 and status["error"] is None
    print("RESULT:", "EVICTED_GUARD_WORKS" if ok else "CHECK_MANUALLY")

asyncio.run(main())
