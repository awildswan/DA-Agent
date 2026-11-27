"""OKF 知识库：git 版本化的 markdown 知识块。

目录结构：<root>/<category>/<name>.md
核心纪律（对齐 daw 原则④）：
- 写入守卫：空内容拒写（fail-loud）；
- 修正优先于并存：同名覆盖，绝不新旧并存；
- git 版本化：每次写入自动 commit（提交信息带板块名 + ±行数）。
"""

import re
import subprocess
from pathlib import Path


def _norm(s: str) -> str:
    """空白归一化（同名标题匹配用）。"""
    return re.sub(r"\s+", "", s)


class OkfStore:
    def __init__(self, root: str | Path, git: bool = True):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.git = git
        if self.git:
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

    def upsert_block(self, category: str, file_name: str, block_name: str, content: str) -> dict:
        """板块级写入：在 category/file_name.md 里 upsert `## block_name` 段，保留其他块。

        - frontmatter / 整文件（# 一级标题）拒写（防 daw「把 write 当整文件保存用」的误用）；
        - 同名标题空白归一化匹配（防同名重复块）；
        - 返回回执 {category, file, block, delta}。
        """
        content = content.strip()
        if not content:
            raise ValueError("空板块内容拒写（fail-loud）")
        if content.startswith("---") or re.match(r"^#\s", content):
            raise ValueError("拒绝：疑似整文件 / frontmatter 内容（板块级写入请只给正文）")

        p = self._path(category, file_name)
        p.parent.mkdir(parents=True, exist_ok=True)
        old_text = p.read_text(encoding="utf-8") if p.exists() else ""
        old_lines = old_text.count("\n")
        norm = _norm(block_name)

        lines = old_text.splitlines()
        out = []
        i = 0
        replaced = False
        while i < len(lines):
            m = re.match(r"^##\s+(.*)$", lines[i])
            if m and _norm(m.group(1)) == norm:
                out.append(f"## {block_name}")
                out.extend(content.splitlines())
                i += 1
                while i < len(lines) and not re.match(r"^##\s+", lines[i]):
                    i += 1
                replaced = True
            else:
                out.append(lines[i])
                i += 1
        if not replaced:
            if out:
                out.append("")
            out.append(f"## {block_name}")
            out.extend(content.splitlines())

        new_text = "\n".join(out).rstrip() + "\n"
        p.write_text(new_text, encoding="utf-8")
        delta = new_text.count("\n") - old_lines
        self._commit(category, file_name, delta)
        return {"category": category, "file": file_name, "block": block_name, "delta": delta}

    def list_blocks(self) -> list[tuple[str, str]]:
        return sorted(
            (str(p.parent.relative_to(self.root)), p.stem)
            for p in self.root.rglob("*.md")
        )

    def _commit(self, category: str, name: str, delta: int) -> None:
        if not self.git:
            return
        self._run(["git", "-C", str(self.root), "add", "-A"])
        sign = "+" if delta >= 0 else ""
        self._run(
            ["git", "-C", str(self.root), "commit", "-q", "-m", f"{category}/{name} {sign}{delta}"]
        )
