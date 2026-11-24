"""OKF 知识库：git 版本化的 markdown 知识块。

目录结构：<root>/<category>/<name>.md
核心纪律（对齐 daw 原则④）：
- 写入守卫：空内容拒写（fail-loud）；
- 修正优先于并存：同名覆盖，绝不新旧并存；
- git 版本化：每次写入自动 commit（提交信息带板块名 + ±行数）。
"""

import subprocess
from pathlib import Path


class OkfStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._ensure_git()

    def _run(self, cmd) -> None:
        """跑 git 命令（静默；无 git 环境则跳过）。"""
        try:
            subprocess.run(
                cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except FileNotFoundError:
            pass

    def _path(self, category: str, name: str) -> Path:
        return self.root / category / f"{name}.md"

    def _ensure_git(self) -> None:
        if not (self.root / ".git").exists():
            self._run(["git", "init", "-q", str(self.root)])
        self._run(["git", "-C", str(self.root), "config", "user.name", "daagent"])
        self._run(["git", "-C", str(self.root), "config", "user.email", "daagent@local"])

    def write(self, category: str, name: str, content: str) -> dict:
        """写入知识块（空内容拒写；同名覆盖 = 修正优先于并存）。返回回执 {板块, ±行数}。"""
        content = content.strip()
        if not content:
            raise ValueError("空内容拒写（fail-loud）")
        p = self._path(category, name)
        p.parent.mkdir(parents=True, exist_ok=True)
        old_lines = p.read_text(encoding="utf-8").count("\n") + 1 if p.exists() else 0
        p.write_text(content + "\n", encoding="utf-8")
        new_lines = content.count("\n") + 1
        delta = new_lines - old_lines
        self._commit(category, name, delta)
        return {"category": category, "name": name, "delta": delta}

    def read(self, category: str, name: str) -> str | None:
        p = self._path(category, name)
        return p.read_text(encoding="utf-8").strip() if p.exists() else None

    def list_blocks(self) -> list[tuple[str, str]]:
        return sorted(
            (str(p.parent.relative_to(self.root)), p.stem)
            for p in self.root.rglob("*.md")
        )

    def _commit(self, category: str, name: str, delta: int) -> None:
        self._run(["git", "-C", str(self.root), "add", "-A"])
        sign = "+" if delta >= 0 else ""
        self._run(
            ["git", "-C", str(self.root), "commit", "-q", "-m", f"{category}/{name} {sign}{delta}"]
        )
