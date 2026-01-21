from collections import defaultdict
from typing import Dict


request_counts: Dict[str, int] = defaultdict(int)
status_counts: Dict[int, int] = defaultdict(int)


def record(path: str, status_code: int) -> None:
    request_counts[path] += 1
    status_counts[status_code] += 1


def snapshot() -> dict:
    return {
        "requests": dict(request_counts),
        "statuses": {str(k): v for k, v in status_counts.items()},
    }
