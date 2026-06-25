#!/usr/bin/env python3
"""Plot a scenario CSV (optional; needs matplotlib).

    python tools/plot.py scenarios/out/battery.csv [--save out.png]

Renders the ground track, altitude, speed, attitude and battery so a scenario
reads as a picture. Falls back to a clear message if matplotlib isn't present.
"""

from __future__ import annotations

import argparse
import csv
import sys


def load(path: str):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    cols = {k: [float(r[k]) for r in rows] for k in rows[0] if k != "state"}
    cols["state"] = [r["state"] for r in rows]
    return cols


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--save", default=None, help="write PNG instead of showing")
    args = ap.parse_args(argv)

    try:
        import matplotlib
        if args.save:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed. `pip install matplotlib` to plot, "
              "or read the ASCII telemetry from scenarios/run.py.")
        return 1

    c = load(args.csv)
    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(args.csv)

    ax[0, 0].plot(c["x"], c["y"]); ax[0, 0].set_title("ground track")
    ax[0, 0].set_xlabel("x [m]"); ax[0, 0].set_ylabel("y [m]")
    ax[0, 0].axhline(0, lw=0.3); ax[0, 0].axvline(0, lw=0.3)
    ax[0, 0].set_aspect("equal", "box")

    ax[0, 1].plot(c["t"], c["z"]); ax[0, 1].set_title("altitude")
    ax[0, 1].set_xlabel("t [s]"); ax[0, 1].set_ylabel("z [m]")

    ax[1, 0].plot(c["t"], c["speed"], label="speed")
    ax[1, 0].plot(c["t"], c["pitch"], label="pitch [deg]")
    ax[1, 0].plot(c["t"], c["roll"], label="roll [deg]")
    ax[1, 0].set_title("speed & attitude"); ax[1, 0].set_xlabel("t [s]")
    ax[1, 0].legend()

    ax[1, 1].plot(c["t"], c["soc"], color="tab:green")
    ax[1, 1].set_title("battery SoC [%]"); ax[1, 1].set_xlabel("t [s]")

    fig.tight_layout()
    if args.save:
        fig.savefig(args.save, dpi=110)
        print(f"saved {args.save}")
    else:
        plt.show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
