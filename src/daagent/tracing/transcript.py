"""会话 transcript 持久化（jsonl，供复盘⑫ / 打分⑬）。"""

import json
from pathlib import Path


class TranscriptStore:
    def __init__(self, path: str = "data/transcripts.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, record: dict) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def load(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in open(self.path, encoding="utf-8") if line.strip()]
