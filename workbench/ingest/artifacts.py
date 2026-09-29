"""UTF-8 JSON artifacts used by the ingest recipes."""

import json
from pathlib import Path


def read_artifact(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("artifact must be a JSON object")
    return data


def write_artifact(path, data):
    if not isinstance(data, dict):
        raise ValueError("artifact must be a JSON object")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return data


def read_staged_manifest(jobs_folder, reference):
    """Read one relative JSON manifest without leaving its conversation folder."""
    if not isinstance(reference, str) or not reference.strip():
        raise ValueError("staged manifest reference must be a non-empty string")
    folder = Path(jobs_folder).resolve()
    candidate = Path(reference)
    if candidate.is_absolute() or candidate.suffix.lower() != ".json":
        raise ValueError("staged manifest must be a relative .json path")
    target = (folder / candidate).resolve()
    if not target.is_relative_to(folder):
        raise ValueError("staged manifest must stay inside this conversation")
    if not target.is_file():
        raise ValueError(f"staged manifest not found: {reference}")
    data = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("staged manifest must be a JSON object")
    return data
