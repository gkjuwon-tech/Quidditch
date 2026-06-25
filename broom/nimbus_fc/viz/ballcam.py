"""First-person ball-cam with AR overlay -> GIF.

What the camera *inside* a ball sees: a pinhole projection of every other agent,
each tagged with an AR marker (id, range, and a threat colour). This is the
"snitch-cam" broadcast shot -- the thing that makes the highlight reel. The
camera looks along the ball's direction of travel; markers grow as things get
close, and the nearest threat is called out on the HUD.
"""

from __future__ import annotations

import numpy as np

BG = "#05070d"
FOV_DEG = 95.0


def _facing(frames, fi, name):
    """Forward unit vector of a ball from its motion across nearby frames."""
    def pos(j):
        b = next((b for b in frames[j].balls if b[0] == name and b[2]), None)
        return None if b is None else b[1]
    p0 = pos(fi)
    if p0 is None:
        return None, None
    p1 = pos(min(fi + 2, len(frames) - 1))
    if p1 is None:
        p1 = p0
    d = (p1 - p0)
    n = float(np.linalg.norm(d[:2]))
    fwd = np.array([d[0], d[1], 0.0]) / n if n > 1e-3 else np.array([1.0, 0.0, 0.0])
    return p0, fwd


def render_ballcam(rec, ball_name: str, path: str, fps: int = 20) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation, PillowWriter

    frames = rec.frames
    f_px = 1.0 / np.tan(np.deg2rad(FOV_DEG) / 2)

    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(-1, 1)
    ax.set_ylim(-0.75, 0.75)
    ax.axis("off")

    # static reticle + horizon
    ax.axhline(0, color="#16344a", lw=1)
    ax.plot([0], [0], marker="+", color="#16b3c6", ms=14, mew=1.5)
    for r in (0.15, 0.32):
        ax.add_patch(plt.Circle((0, 0), r, fill=False, ec="#102a3a",
                                lw=0.6, alpha=0.5))
    title = ax.text(0, 0.69, "", color="#ffd447", ha="center", fontsize=13,
                    family="monospace", fontweight="bold")
    hud = ax.text(-0.98, -0.69, "", color="#9fb3c8", ha="left", fontsize=10,
                  family="monospace")
    warn = ax.text(0.98, -0.69, "", color="#ff5470", ha="right", fontsize=10,
                   family="monospace")

    blips = ax.scatter([], [], s=[], zorder=5)
    labels = [ax.text(0, 0, "", color="white", fontsize=8, ha="center",
                      family="monospace", zorder=6) for _ in range(16)]

    def update(fi):
        f = frames[fi]
        cam, fwd = _facing(frames, fi, ball_name)
        for lb in labels:
            lb.set_text("")
        if cam is None:
            title.set_text(f"{ball_name.upper()}-CAM   (caught)")
            blips.set_offsets(np.empty((0, 2)))
            return [blips, *labels, title, hud, warn]
        right = np.cross(fwd, [0, 0, 1.0]); right /= np.linalg.norm(right)
        up = np.cross(right, fwd)

        pts, sizes, colors = [], [], []
        nearest = (np.inf, "")
        li = 0
        agents = [("P%d" % p[0], p[1], "#5b8cff", p[2]) for p in f.players]
        agents += [(b[0][:3].upper(), b[1],
                    "#ff5470" if b[0] == "bludger" else "#ff884d", True)
                   for b in f.balls if b[0] != ball_name and b[2]]
        for tag, apos, col, alive in agents:
            rel = apos - cam
            depth = float(np.dot(rel, fwd))
            if depth < 0.4:
                continue
            sx = f_px * float(np.dot(rel, right)) / depth
            sy = f_px * float(np.dot(rel, up)) / depth
            if abs(sx) > 1.05 or abs(sy) > 0.8:
                continue
            rng = float(np.linalg.norm(rel))
            pts.append((sx, sy))
            sizes.append(max(20, 1600 / max(rng, 1.0)))
            colors.append(col)
            if li < len(labels):
                labels[li].set_position((sx, sy + 0.06))
                labels[li].set_text(f"{tag} {rng:4.1f}m")
                labels[li].set_color(col)
                li += 1
            if rng < nearest[0]:
                nearest = (rng, tag)
        blips.set_offsets(pts if pts else np.empty((0, 2)))
        blips.set_sizes(sizes if sizes else [])
        blips.set_color(colors if colors else "white")

        spd = 0.0
        if fi > 0:
            p_prev, _ = _facing(frames, fi - 1, ball_name)
            if p_prev is not None:
                spd = np.linalg.norm(cam - p_prev) / (frames[fi].t - frames[fi - 1].t + 1e-9)
        title.set_text(f"{ball_name.upper()}-CAM   t={f.t:4.1f}s")
        hud.set_text(f"spd {spd:4.1f} m/s")
        warn.set_text(f"!! {nearest[1]} {nearest[0]:.1f}m" if nearest[0] < 6 else "")
        return [blips, *labels, title, hud, warn]

    anim = FuncAnimation(fig, update, frames=len(frames), interval=1000 / fps, blit=False)
    anim.save(path, writer=PillowWriter(fps=fps), dpi=72)
    plt.close(fig)
    from .replay import _optimize_gif
    _optimize_gif(path)
    return path
