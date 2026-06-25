#!/usr/bin/env python3
"""Benchmark the control core: Python backend vs Rust backend.

What matters for a manned flight controller is not average speed, it is
WORST-CASE latency and jitter. At 400 Hz the inner loop has a 2500 us budget
per tick; blow it (e.g. a GC pause) and the loop destabilizes. We measure the
per-tick latency distribution for both backends and count deadline misses.

    python tools/bench.py [n_iters]
"""

from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from nimbus_fc.control.backend import make_backend, rust_available  # noqa: E402
from nimbus_fc.core.params import Params  # noqa: E402
from nimbus_fc.core.types import Setpoint, State  # noqa: E402

RT_RATE_HZ = 400.0
BUDGET_US = 1e6 / RT_RATE_HZ  # 2500 us per tick


def _representative_state() -> State:
    # A typical in-flight state: tilted, moving, off-target (exercises full cascade).
    return State(
        pos=np.array([3.0, -2.0, 6.0]),
        vel=np.array([4.0, 1.0, -0.5]),
        quat=np.array([0.985, 0.02, 0.17, 0.03]),
        omega=np.array([0.05, -0.1, 0.08]),
    )


def _representative_sp() -> Setpoint:
    return Setpoint(pos=np.array([10.0, 8.0, 9.0]), yaw=0.3)


def bench(backend_name: str, n: int) -> dict:
    p = Params()
    core = make_backend(p, backend_name)
    state, sp, dt = _representative_state(), _representative_sp(), p.dt

    for _ in range(2000):              # warm up (caches, branch predictor, JIT-less)
        core.control(state, sp, dt)

    lat = np.empty(n, dtype=np.float64)
    for i in range(n):
        t0 = time.perf_counter_ns()
        core.control(state, sp, dt)
        lat[i] = (time.perf_counter_ns() - t0) * 1e-3  # us

    misses = int(np.sum(lat > BUDGET_US))
    return {
        "name": backend_name,
        "mean": lat.mean(), "median": np.median(lat),
        "p99": np.percentile(lat, 99), "p999": np.percentile(lat, 99.9),
        "max": lat.max(), "min": lat.min(),
        "throughput_hz": 1e6 / lat.mean(),
        "deadline_misses": misses, "n": n,
    }


def _row(r: dict) -> str:
    return (f"  {r['name']:<7} "
            f"mean={r['mean']:8.2f}  median={r['median']:8.2f}  "
            f"p99={r['p99']:8.2f}  p99.9={r['p999']:8.2f}  max={r['max']:9.2f}  "
            f"miss={r['deadline_misses']:>6}/{r['n']}")


def main(argv: list[str]) -> int:
    n = int(argv[0]) if argv else 200_000
    print(f"control-tick latency over {n:,} iterations (microseconds)")
    print(f"real-time budget at {RT_RATE_HZ:.0f} Hz = {BUDGET_US:.0f} us/tick\n")

    results = [bench("python", n)]
    if rust_available():
        results.append(bench("rust", n))
    else:
        print("  (rust core not built; run: cd rust/nimbus_core && cargo build --release)\n")

    for r in results:
        print(_row(r))

    if len(results) == 2:
        py, ru = results
        print(f"\n  speedup (mean):   {py['mean'] / ru['mean']:6.1f}x")
        print(f"  speedup (p99.9):  {py['p999'] / ru['p999']:6.1f}x  <- worst-case is the safety metric")
        print(f"  speedup (max):    {py['max'] / ru['max']:6.1f}x")
        print(f"  deadline misses:  python={py['deadline_misses']}  rust={ru['deadline_misses']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
