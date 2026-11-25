"""可观测 Trace：按环节记录 span（名称 + 耗时）。

简化版（对齐 MODULE_DESIGN ⑭ Trace 的核心）：每环节一个 span，出错了能看哪一环耗时异常。
完整版（OTel 双表 + firstRow 指纹 + 成本核算）接真实数据后补。
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field


@dataclass
class Span:
    name: str
    duration_ms: float
    meta: dict = field(default_factory=dict)


class Trace:
    def __init__(self):
        self.spans: list[Span] = []

    @contextmanager
    def span(self, name: str, **meta):
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self.spans.append(Span(name, (time.perf_counter() - t0) * 1000, meta))

    def summary(self) -> str:
        return " · ".join(f"{s.name} {s.duration_ms:.0f}ms" for s in self.spans)
