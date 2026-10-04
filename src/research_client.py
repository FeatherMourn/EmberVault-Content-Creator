"""Read-only Content Creator client for Mod Research handoff records."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_research_handoff(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if payload.get("schema_version") != 1 or payload.get("application_state") != "design-only":
        raise ValueError("unsupported or unsafe research handoff")
    if payload.get("live_game_files_touched") is not False:
        raise ValueError("research handoff must be design-only")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("research handoff records must be a list")
    return records


def search_research_handoff(records: list[dict[str, Any]], query: str = "", *, kind: str | None = None) -> list[dict[str, Any]]:
    needle = query.strip().casefold()
    result = []
    for record in records:
        if kind and record.get("kind") != kind:
            continue
        if needle and needle not in json.dumps(record, sort_keys=True).casefold():
            continue
        result.append(record)
    return sorted(result, key=lambda record: record["id"])
