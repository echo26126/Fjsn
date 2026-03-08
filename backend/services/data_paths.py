import os
from pathlib import Path


def resolve_data_file(filename: str) -> Path:
    current_file = Path(__file__).resolve()
    configured_dir = os.getenv("DATA_FILES_DIR", "").strip()
    candidates = []
    if configured_dir:
        candidates.append(Path(configured_dir))
    candidates.extend(
        [
            current_file.parents[2],
            Path("/app/data-input"),
            Path("/data-input"),
            current_file.parents[1],
        ]
    )
    for base in candidates:
        candidate = base / filename
        if candidate.exists():
            return candidate
    return candidates[0] / filename if candidates else Path(filename)
