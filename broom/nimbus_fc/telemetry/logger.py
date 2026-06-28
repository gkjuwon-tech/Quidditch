"""Telemetry: gather per-tick rows, write CSV, print terminal summaries.

Deliberately no plotting dependency -- a little ASCII sparkline keeps the demo
readable over SSH. If you want real plots, tools/plot.py uses matplotlib.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TelemetryLog:
    rows: list[dict] = field(default_factory=list)

    def append(self, **kw) -> None:
        self.rows.append(kw)

    def to_csv(self, path: str) -> None:
        if not self.rows:
            return
        keys = list(self.rows[0].keys())
        with open(path, "w") as f:
            f.write(",".join(keys) + "\n")
            for r in self.rows:
                f.write(",".join(f"{r[k]:.5g}" if isinstance(r[k], float)
                                 else str(r[k]) for k in keys) + "\n")

    def column(self, key: str) -> list:
        return [r[key] for r in self.rows]

    def sparkline(self, key: str, width: int = 60) -> str:
        vals = self.column(key)
        if not vals:
            return ""
        lo, hi = min(vals), max(vals)
        rng = hi - lo or 1.0
        chars = "▁▂▃▄▅▆▇█"
        step = max(1, len(vals) // width)
        line = "".join(
            chars[min(len(chars) - 1, int((vals[i] - lo) / rng * (len(chars) - 1)))]
            for i in range(0, len(vals), step)
        )
        return f"{key:>10} [{lo:7.2f} .. {hi:7.2f}] {line}"

    def summary(self, keys: list[str], width: int = 60) -> str:
        return "\n".join(self.sparkline(k, width) for k in keys)
