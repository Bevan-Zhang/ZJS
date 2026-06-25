"""Pure helpers for selecting threats from the active bridge batch."""
from __future__ import annotations

from typing import Any


def batch_threat_ids(state: dict[str, Any]) -> list[str]:
    """Return non-empty threat IDs in bridge submission order."""
    submitted = state.get("submitted", {})
    if not isinstance(submitted, dict):
        return []

    result: list[str] = []
    for item in submitted.values():
        if not isinstance(item, dict):
            continue
        threat_id = str(item.get("threat_id") or "").strip()
        if threat_id:
            result.append(threat_id)
    return result


def filter_batch_threats(
    threats: list[dict[str, Any]],
    threat_ids: list[str],
) -> list[dict[str, Any]]:
    """Select the active batch and return newest submissions first."""
    by_id = {
        str(item.get("id")): item
        for item in threats
        if isinstance(item, dict) and item.get("id")
    }
    return [by_id[threat_id] for threat_id in reversed(threat_ids) if threat_id in by_id]

