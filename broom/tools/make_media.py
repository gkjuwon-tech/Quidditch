#!/usr/bin/env python3
"""Render the landing-page media: a showcase match -> replay GIF + snitch-cam GIF.

    python tools/make_media.py            # writes site/assets/{replay,ballcam}.gif + poster.png

A clean showreel match: two seekers run down a tiring snitch, a Bludger sends
players off, a chaser scores a Quaffle, refereed by the Dementor.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402

from nimbus_fc.ball import params, BallBody, World  # noqa: E402
from nimbus_fc.ball.bludger import BludgerPursuit  # noqa: E402
from nimbus_fc.ball.quaffle import QuaffleBehavior  # noqa: E402
from nimbus_fc.ball.snitch import SnitchEvasion  # noqa: E402
from nimbus_fc.core.params import Params  # noqa: E402
from nimbus_fc.match.broom_agent import BroomAgent  # noqa: E402
from nimbus_fc.match.dementor import Dementor  # noqa: E402
from nimbus_fc.match.policies import chase_ball, guard_hoops  # noqa: E402
from nimbus_fc.viz import MatchRecorder, render_ballcam, render_topdown  # noqa: E402

DT = 0.0025
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "site", "assets")


def build_match():
    sp = params.snitch()
    sp.extra["fatigue_tau"] = 90.0
    sp.extra["fatigue_floor"] = 0.6
    sp.extra["danger_radius"] = 7.0
    w = World()
    w.hoops = [(np.array([46.0, 0.0, 12.0]), 1.6),
               (np.array([46.0, 7.0, 12.0]), 1.6),
               (np.array([46.0, -7.0, 12.0]), 1.6)]
    snitch = w.add_ball(BallBody(sp, [0, 0, 12]), SnitchEvasion(sp))
    quaffle = w.add_ball(BallBody(params.quaffle(), [-12, 0, 10]),
                         QuaffleBehavior(params.quaffle()))
    for i in range(2):
        a = np.pi * i + 0.3
        w.players.append(BroomAgent(i, [30 * np.cos(a), 18 * np.sin(a), 10],
                                    chase_ball(snitch), params=Params(), reach=1.4))
    w.players.append(BroomAgent(2, [-16, 0, 10], chase_ball(quaffle),
                                params=Params(), reach=1.0))
    w.players.append(BroomAgent(3, [40, 0, 12], guard_hoops(w.hoops, quaffle),
                                params=Params(), reach=1.0))
    dem = Dementor(broom_sep=3.0, margin=2.0).attach(w)
    return w, dem


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    print("simulating showcase match ...")
    w, dem = build_match()
    rec = MatchRecorder(w, fps=15, sim_dt=DT, title="NIMBUS-9¾  ·  REAL QUIDDITCH")
    rec.run(20.0, DT)
    print(f"  {len(rec.rec.frames)} frames, ended t={w.t:.1f}s, "
          f"score {dem.scoreboard(w)}")

    print("rendering top-down replay -> replay.gif")
    render_topdown(rec.rec, os.path.join(OUT, "replay.gif"), fps=15)
    print("rendering snitch-cam -> ballcam.gif")
    render_ballcam(rec.rec, "snitch", os.path.join(OUT, "ballcam.gif"), fps=15)

    # poster: pull a mid-match frame straight out of the replay GIF
    from PIL import Image
    gif = Image.open(os.path.join(OUT, "replay.gif"))
    gif.seek(min(gif.n_frames - 1, gif.n_frames // 2))
    gif.convert("RGB").save(os.path.join(OUT, "poster.png"))

    for f in ("replay.gif", "ballcam.gif", "poster.png"):
        p = os.path.join(OUT, f)
        print(f"  {f}: {os.path.getsize(p) // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
