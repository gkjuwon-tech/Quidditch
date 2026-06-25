"""Top-down AR replay renderer -> GIF (broadcast/spectator view).

Dark "AR overlay" look: glowing pitch, hoops, player markers with id labels and
motion trails, the three balls in their colours, and a HUD with match clock,
score and an event ticker. Pure matplotlib; saved via PillowWriter.
"""

from __future__ import annotations

import numpy as np

BG = "#0b1020"
LINE = "#16b3c6"
BALL_STYLE = {
    "quaffle": ("#ff5470", 70),
    "bludger": ("#c9d1d9", 60),
    "snitch": ("#ffd447", 90),
}
TEAM = ["#36d399", "#5b8cff", "#36d399", "#5b8cff", "#36d399", "#5b8cff"]


def render_topdown(rec, path: str, fps: int = 25, trail: int = 16) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter
    from matplotlib.patches import Circle, Rectangle

    frames = rec.frames
    lo, hi = rec.pitch_lo, rec.pitch_hi

    fig, ax = plt.subplots(figsize=(11, 6.2))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(lo[0] - 4, hi[0] + 4)
    ax.set_ylim(lo[1] - 4, hi[1] + 4)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.add_patch(Rectangle((lo[0], lo[1]), hi[0] - lo[0], hi[1] - lo[1],
                           fill=False, ec=LINE, lw=2, alpha=0.7))
    for c, r in rec.hoops:
        ax.add_patch(Circle((c[0], c[1]), r, fill=False, ec="#ffd447", lw=2, alpha=0.8))

    title = ax.text(0.5, 1.04, rec.title, transform=ax.transAxes, color="white",
                    ha="center", fontsize=15, fontweight="bold")
    hud = ax.text(0.01, 1.04, "", transform=ax.transAxes, color="#9fb3c8",
                  ha="left", fontsize=11, family="monospace")
    ticker = ax.text(0.5, -0.05, "", transform=ax.transAxes, color="#ffd447",
                     ha="center", fontsize=11, family="monospace")

    player_dots = ax.scatter([], [], s=90, zorder=5)
    player_labels = []
    trail_lines = {}
    ball_dots = {name: ax.scatter([], [], s=sz, color=col, zorder=6,
                                  edgecolors="white", linewidths=0.5)
                 for name, (col, sz) in BALL_STYLE.items()}
    ball_trails = {name: ax.plot([], [], color=col, lw=1.2, alpha=0.5)[0]
                   for name, (col, _) in BALL_STYLE.items()}

    npl = len(frames[0].players) if frames else 0
    for i in range(npl):
        player_labels.append(ax.text(0, 0, "", color="white", fontsize=8,
                                     ha="center", va="center", zorder=7))
        trail_lines[i] = ax.plot([], [], color=TEAM[i % len(TEAM)], lw=1.5, alpha=0.4)[0]

    last_event = {"txt": "", "t": -9}

    def update(fi):
        f = frames[fi]
        # players
        offs = np.array([p[1][:2] for p in f.players]) if f.players else np.empty((0, 2))
        cols = [TEAM[i % len(TEAM)] for i in range(len(f.players))]
        edge = ["#ff5470" if p[2] else "white" for p in f.players]  # red ring if sent off
        player_dots.set_offsets(offs)
        player_dots.set_color(cols)
        player_dots.set_edgecolors(edge)
        player_dots.set_linewidths(2.0)
        for i, p in enumerate(f.players):
            player_labels[i].set_position((p[1][0], p[1][1] + 1.8))
            player_labels[i].set_text(f"P{p[0]}")
            seg = [frames[j].players[i][1][:2] for j in range(max(0, fi - trail), fi + 1)
                   if i < len(frames[j].players)]
            if seg:
                seg = np.array(seg)
                trail_lines[i].set_data(seg[:, 0], seg[:, 1])
        # balls
        for name, dot in ball_dots.items():
            cur = next((b for b in f.balls if b[0] == name), None)
            if cur is None or not cur[2]:
                dot.set_offsets(np.empty((0, 2)))
                ball_trails[name].set_data([], [])
                continue
            dot.set_offsets([cur[1][:2]])
            seg = []
            for j in range(max(0, fi - trail), fi + 1):
                b = next((b for b in frames[j].balls if b[0] == name and b[2]), None)
                if b is not None:
                    seg.append(b[1][:2])
            if seg:
                seg = np.array(seg)
                ball_trails[name].set_data(seg[:, 0], seg[:, 1])
        # HUD
        hud.set_text(f"t={f.t:5.1f}s   score {f.score}")
        if f.event:
            last_event["txt"] = f.event
            last_event["t"] = f.t
        if f.t - last_event["t"] < 3.0:
            ticker.set_text(last_event["txt"][:70])
        else:
            ticker.set_text("")
        return [player_dots, *player_labels, *trail_lines.values(),
                *ball_dots.values(), *ball_trails.values(), hud, ticker, title]

    anim = FuncAnimation(fig, update, frames=len(frames), interval=1000 / fps, blit=False)
    anim.save(path, writer=PillowWriter(fps=fps), dpi=72)
    plt.close(fig)
    _optimize_gif(path)
    return path


def _optimize_gif(path: str) -> None:
    """Shrink the GIF: reduce to an adaptive palette and enable optimization."""
    try:
        from PIL import Image, ImageSequence
        im = Image.open(path)
        frames = [f.copy().convert("P", palette=Image.ADAPTIVE, colors=64)
                  for f in ImageSequence.Iterator(im)]
        dur = im.info.get("duration", 50)
        frames[0].save(path, save_all=True, append_images=frames[1:],
                       loop=0, duration=dur, optimize=True, disposal=2)
    except Exception:
        pass
