"""加载 prompt 模板（静态 prompt 与代码分离，便于版本管理 + 字节稳定）。"""

from pathlib import Path

_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    """从 prompts/<name>.md 加载；缺文件即 fail-loud（提示词唯一真相在 md，不在代码里）。"""
    p = _DIR / f"{name}.md"
    if not p.exists():
        raise FileNotFoundError(f"prompt 模板缺失：{p}（提示词只写在 md，不写在代码里）")
    return p.read_text(encoding="utf-8").strip()
