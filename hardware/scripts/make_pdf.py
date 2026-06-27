#!/usr/bin/env python3
"""Assemble the hardware drawing package.

Reads the rendered CAD views (build/views/*.png) and the BOM CSVs
(bom/*_bom.csv) and lays them out as proper engineering drawing sheets:
title block, multi-view, a dimension/spec panel keyed to the software
params, and the per-part bill of materials. Also rolls up a match-fleet
cost summary (bom/SUMMARY.csv).

    python3 scripts/make_pdf.py

Outputs:
    build/drawings/<part>.pdf        one sheet per part
    build/drawings/NIMBUS_hardware_drawings.pdf   the whole package
    bom/SUMMARY.csv                  fleet rollup
"""
from __future__ import annotations

import csv
import datetime as _dt
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIEWS = os.path.join(HERE, "build", "views")
BOMDIR = os.path.join(HERE, "bom")
OUT = os.path.join(HERE, "drawings")            # committed deliverable
RENDERS = os.path.join(HERE, "renders")         # committed sheet previews
DATE = _dt.date.today().isoformat()

GOLD = "#d4af37"
INK = "#1b1b1f"
PAPER = "#fbfbf6"

# ---- per-part metadata: the dimensions/specs panel, keyed to the SW -----
PARTS = {
    "broom": dict(
        title="NIMBUS-9¾  BROOM", code="BRM",
        sub="Manned eVTOL — 1 rider, 8 ducted fans, fly-by-intent",
        dims=[
            ("Overall length", "2400 mm", "core/params.py LEN = 2.4 m"),
            ("Lift fans", "8 × EDF (internal)", "_default_fan_layout (exact x/y)"),
            ("Thrust-to-weight", "2.45 (hover @ 41%)", "analysis/flight_thermal.py"),
            ("Battery sprint", "~61 s / charge", "2600 Wh alone — a sprinter"),
            ("Match endurance", "~26 min (hybrid)", "series-hybrid: analysis/endurance_match.py"),
            ("Cooling margin", "8.1× waste heat", "lift air = coolant + heat pipes"),
            ("League ceiling", "150 m (svc ~km)", "altitude_ceiling.py + fence_ceiling"),
            ("Control input", "wave-to-fly (gesture)", "firmware/rider_input.py -> intent mapper"),
        ],
        note="Disc area is capped by what fits inside the bristle flare (the fan never "
             "protrudes), so battery-only it's a ~60 s sprinter. A slim in-shaft "
             "SERIES-HYBRID genset burning SAF lifts that to a ~26 min match (the "
             "battery becomes the peak buffer; full ~250 kW bursts kept). Fans internal, "
             "lift air = coolant. And you fly it by WAVING it: handle pose -> RiderIntent "
             "-> the existing intent mapper. FLIGHT + THERMAL + MATCH all PASS.",
    ),
    "snitch": dict(
        title="GOLDEN SNITCH", code="SNT",
        sub="Walnut-sized evasion drone — beamed-power, full-match flight",
        dims=[
            ("Shell radius", "40 mm (Ø80)", "ball/params.py snitch.radius = 0.04 m"),
            ("Mass target", "50 g (kept)", "snitch.mass = 0.05 kg"),
            ("Top speed", "19 m/s", "snitch.max_speed"),
            ("Max accel", "32 m/s²", "snitch.max_accel (absurdly agile)"),
            ("Lift", "4 × micro-EDF (internal)", "swarm core — the real flight"),
            ("Battery sprint", "~2.7 min", "1S 300 mAh alone — ≈ the fatigue_tau"),
            ("Match endurance", "continuous (beamed)", "analysis/snitch_endurance.py"),
            ("Pitch power", "~2.5 kW array", "5.8 GHz steered to the broadcast pose"),
        ],
        note="WINGS ARE THEATRE (SNT-02/03/04 flutter; lift is the internal EDF "
             "swarm SNT-05 — don't tell Potterheads). A 50 g walnut can't carry "
             "fuel like the broom, so it HARVESTS energy instead: the gold dimple-"
             "vents double as a 5.8 GHz rectenna (SNT-15/16) and a pitch array beams "
             "power onto its broadcast pose (SNT-19/20). The cell becomes a buffer "
             "(jukes on a supercap SNT-17). Form + agility kept, match filled, no pit.",
    ),
    "bludger": dict(
        title="BLUDGER", code="BLG",
        sub="The skull-cracker, with the skull-cracking removed",
        dims=[
            ("Shell radius", "150 mm (Ø300)", "ball/params.py bludger.radius = 0.15 m"),
            ("Mass", "1.2 kg (foam)", "bludger.mass — looks iron, isn't"),
            ("Top speed", "15 m/s", "bludger.max_speed"),
            ("Max accel", "22 m/s²", "bludger.max_accel (most aggressive)"),
            ("Lift", "4 × EDF (internal)", "swarm core"),
            ("Soft-tag radius", "1.5 m", "tag_radius (outside no-contact floor)"),
            ("Bat deflect", "1.6 m", "bat_radius"),
            ("Contact", "0 — software hit", "ball/avoidance.py, worst clr +0.40 m"),
        ],
        note="All threat, no contact. The 'hit' is a proximity tag registered in "
             "software ~1.5 m out; the foam shell never has to reach a person.",
    ),
    "quaffle": dict(
        title="QUAFFLE", code="QAF",
        sub="The friendly one — catch, carry, throw, score",
        dims=[
            ("Shell radius", "180 mm (Ø360)", "ball/params.py quaffle.radius = 0.18 m"),
            ("Mass", "0.5 kg", "quaffle.mass — light despite its size"),
            ("Top speed", "7 m/s", "quaffle.max_speed (gentle)"),
            ("Catch radius", "0.45 m", "quaffle.catch_radius (forgiving)"),
            ("Lift", "4 × EDF (internal)", "swarm core, soft hover"),
            ("On catch", "thrust → 0 in hand", "ball/quaffle.py capacitive sense"),
            ("Scoring", "hoop optical gate", "auto pass-through detection"),
            ("Safety", "no-contact floor", "even the nice ball won't bonk you"),
        ],
        note="Soft hover, generous catch, rides with its holder, then throws to the "
             "nearest hoop with tunable aim-assist (on for youth, off for pros).",
    ),
}

FLEET = {"broom": 14, "quaffle": 1, "bludger": 2, "snitch": 1}  # one full match


def read_bom(part):
    path = os.path.join(BOMDIR, f"{part}_bom.csv")
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    total = sum(float(r["ext_cost_usd"]) for r in rows)
    return rows, total


def _img(ax, name, title):
    ax.axis("off")
    p = os.path.join(VIEWS, f"{name}.png")
    if os.path.exists(p):
        ax.imshow(mpimg.imread(p))
    ax.set_title(title, fontsize=8, color=INK, pad=2)


def sheet(pdf, part):
    meta = PARTS[part]
    rows, total = read_bom(part)

    fig = plt.figure(figsize=(16.54, 11.69))  # A3 landscape
    fig.patch.set_facecolor(PAPER)
    gs = fig.add_gridspec(
        12, 12, left=0.03, right=0.97, top=0.93, bottom=0.04,
        hspace=0.6, wspace=0.4)

    # ---- header band ----
    hd = fig.add_axes([0.03, 0.94, 0.94, 0.05]); hd.axis("off")
    hd.add_patch(Rectangle((0, 0), 1, 1, transform=hd.transAxes,
                           facecolor=INK))
    hd.text(0.012, 0.5, meta["title"], color=GOLD, fontsize=20,
            fontweight="bold", va="center", ha="left",
            transform=hd.transAxes)
    hd.text(0.99, 0.62, meta["sub"], color="white", fontsize=9.5,
            va="center", ha="right", transform=hd.transAxes)
    hd.text(0.99, 0.26, "Project NIMBUS-9¾ · Real Quidditch · "
            "hardware full-stack", color=GOLD, fontsize=7.5,
            va="center", ha="right", transform=hd.transAxes)

    # ---- big iso ----
    ax_iso = fig.add_subplot(gs[0:6, 0:7]); _img(ax_iso, f"{part}_iso", "ISOMETRIC")
    # ---- ortho thumbs ----
    _img(fig.add_subplot(gs[0:3, 7:10]), f"{part}_side", "SIDE")
    _img(fig.add_subplot(gs[0:3, 10:12]), f"{part}_top", "TOP")
    _img(fig.add_subplot(gs[3:6, 7:12]), f"{part}_cutaway",
         "CUTAWAY — internal drive revealed")

    # ---- dimensions / spec panel ----
    axd = fig.add_subplot(gs[6:12, 0:4]); axd.axis("off")
    axd.add_patch(Rectangle((0, 0), 1, 1, transform=axd.transAxes,
                            fill=False, edgecolor=INK, lw=1.2))
    axd.text(0.04, 0.96, "KEY DIMENSIONS & SPEC", fontsize=10,
             fontweight="bold", color=INK, va="top")
    axd.text(0.04, 0.92, "(every number ties back to the flight software)",
             fontsize=6.5, style="italic", color="#555", va="top")
    y = 0.86
    for label, val, src in meta["dims"]:
        axd.text(0.04, y, label, fontsize=8, color=INK, va="top")
        axd.text(0.62, y, val, fontsize=8, color=INK, va="top",
                 fontweight="bold")
        axd.text(0.04, y - 0.028, src, fontsize=5.8, color="#777",
                 va="top", family="monospace")
        y -= 0.082
    axd.add_patch(Rectangle((0.03, 0.012), 0.94, 0.10,
                            transform=axd.transAxes, facecolor="#f0ead2",
                            edgecolor=GOLD, lw=1))
    axd.text(0.05, 0.105, "NOTE", fontsize=6.5, fontweight="bold",
             color="#8a6d1a", va="top")
    axd.text(0.05, 0.082, _wrap(meta["note"], 56), fontsize=6.3,
             color=INK, va="top")

    # ---- BOM table ----
    axb = fig.add_subplot(gs[6:12, 4:12]); axb.axis("off")
    axb.text(0.0, 1.0, f"BILL OF MATERIALS  —  {meta['code']}  "
             f"({len(rows)} line items, prototype qty 1)",
             fontsize=10, fontweight="bold", color=INK, va="top")
    cols = ["ref", "part", "spec", "qty", "unit", "ext"]
    cw = [0.07, 0.21, 0.45, 0.05, 0.10, 0.12]
    head_y = 0.94
    x = 0.0
    for c, w in zip(["REF", "PART", "SPEC", "QTY", "$ EA", "$ EXT"], cw):
        axb.text(x + 0.004, head_y, c, fontsize=6.8, fontweight="bold",
                 color="white", va="center")
        x += w
    axb.add_patch(Rectangle((0, head_y - 0.018), 1, 0.028,
                            transform=axb.transAxes, facecolor=INK, zorder=-1))
    ry = head_y - 0.04
    dy = 0.86 / max(len(rows), 1)
    dy = min(dy, 0.052)
    for i, r in enumerate(rows):
        if i % 2 == 0:
            axb.add_patch(Rectangle((0, ry - dy * 0.62), 1, dy * 0.95,
                          transform=axb.transAxes, facecolor="#efefe6",
                          zorder=-2))
        cells = [r["ref"], _clip(r["part"], 30), _clip(r["spec"], 64),
                 r["qty"], f"{float(r['unit_cost_usd']):,.0f}",
                 f"{float(r['ext_cost_usd']):,.0f}"]
        x = 0.0
        for v, w, c in zip(cells, cw, cols):
            mono = c in ("ref",)
            axb.text(x + 0.004, ry, v, fontsize=5.7, color=INK,
                     va="center", family="monospace" if mono else "sans-serif")
            x += w
        ry -= dy
    axb.text(0.0, ry - 0.01, "_" * 130, fontsize=6, color="#bbb", va="center")
    axb.text(0.74, ry - 0.05, "UNIT TOTAL (prototype):", fontsize=8.5,
             fontweight="bold", color=INK, va="center", ha="right")
    axb.text(0.88, ry - 0.05, f"${total:,.0f}", fontsize=9.5,
             fontweight="bold", color="#1a6a1a", va="center")

    # ---- title block (bottom strip) ----
    tb = fig.add_axes([0.03, 0.005, 0.94, 0.03]); tb.axis("off")
    tb.add_patch(Rectangle((0, 0), 1, 1, transform=tb.transAxes,
                           fill=False, edgecolor=INK, lw=1))
    fields = [("DRAWN", "NIMBUS HW"), ("DATE", DATE), ("UNITS", "mm / SI"),
              ("SCALE", "NTS"), ("PART", meta["code"]),
              ("REV", "v0.1"), ("CAD", f"cad/{part}.scad")]
    x = 0.0
    for k, v in fields:
        w = 1.0 / len(fields)
        tb.text(x + 0.006, 0.62, k, fontsize=5.5, color="#777",
                va="center", transform=tb.transAxes)
        tb.text(x + 0.006, 0.26, v, fontsize=7.5, color=INK, va="center",
                fontweight="bold", transform=tb.transAxes)
        x += w
    pdf.savefig(fig, facecolor=PAPER)
    fig.savefig(os.path.join(RENDERS, f"sheet_{part}.png"), facecolor=PAPER, dpi=96)
    plt.close(fig)


def cover(pdf):
    fig = plt.figure(figsize=(16.54, 11.69))
    fig.patch.set_facecolor(INK)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.text(0.5, 0.72, "NIMBUS-9¾", color=GOLD, fontsize=64,
            fontweight="bold", ha="center", va="center")
    ax.text(0.5, 0.63, "HARDWARE FULL-STACK — DRAWING PACKAGE",
            color="white", fontsize=20, ha="center", va="center")
    ax.text(0.5, 0.57, "Real Quidditch · broom + three balls · "
            "BOM · OpenSCAD CAD · drawings",
            color="#bbb", fontsize=12, ha="center", va="center")
    items = [
        "SHEET 1   BROOM        manned eVTOL, 8 internal ducted fans",
        "SHEET 2   GOLDEN SNITCH evasion drone, real flapping wings",
        "SHEET 3   BLUDGER       pursuit + soft-tag, zero contact",
        "SHEET 4   QUAFFLE       catch / carry / throw / score",
        "SHEET 5   MATCH FLEET   rollup cost for one 7v7 match",
    ]
    for i, it in enumerate(items):
        ax.text(0.28, 0.44 - i * 0.045, it, color=GOLD if i == 0 else "white",
                fontsize=11, ha="left", va="center", family="monospace")
    ax.text(0.5, 0.10, '"Magic? No. We just wrote the collision-avoidance '
            'really well."', color="#888", fontsize=11, style="italic",
            ha="center", va="center")
    ax.text(0.5, 0.055, f"generated {DATE}  ·  geometry true to "
            "nimbus_fc params  ·  v0.1", color="#666", fontsize=8,
            ha="center", va="center")
    pdf.savefig(fig, facecolor=INK)
    fig.savefig(os.path.join(RENDERS, "sheet_cover.png"), facecolor=INK, dpi=96)
    plt.close(fig)


def fleet_sheet(pdf):
    # rollup
    summ = []
    grand = 0.0
    for part, n in FLEET.items():
        _, unit = read_bom(part)
        ext = unit * n
        grand += ext
        summ.append((PARTS[part]["title"], PARTS[part]["code"], n, unit, ext))

    # write SUMMARY.csv
    with open(os.path.join(BOMDIR, "SUMMARY.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["item", "code", "match_qty", "unit_cost_usd", "ext_cost_usd"])
        for name, code, n, unit, ext in summ:
            w.writerow([name, code, n, f"{unit:.0f}", f"{ext:.0f}"])
        w.writerow(["MATCH TOTAL (1 × 7v7 + balls)", "", "", "", f"{grand:.0f}"])

    fig = plt.figure(figsize=(16.54, 11.69))
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes([0.06, 0.06, 0.88, 0.86]); ax.axis("off")
    ax.text(0.0, 1.0, "MATCH FLEET ROLLUP", fontsize=22, fontweight="bold",
            color=INK, va="top")
    ax.text(0.0, 0.95, "Hardware to field ONE real 7-v-7 match: "
            "14 brooms + 1 quaffle + 2 bludgers + 1 snitch.",
            fontsize=11, color="#444", va="top")
    heads = ["ITEM", "CODE", "MATCH QTY", "UNIT $", "EXT $"]
    xs = [0.0, 0.34, 0.46, 0.62, 0.80]
    y = 0.84
    ax.add_patch(Rectangle((0, y - 0.03), 1, 0.05, facecolor=INK))
    for h, x in zip(heads, xs):
        ax.text(x + 0.005, y - 0.005, h, fontsize=10, fontweight="bold",
                color="white", va="center")
    y -= 0.08
    for name, code, n, unit, ext in summ:
        ax.text(xs[0] + 0.005, y, name, fontsize=11, color=INK, va="center")
        ax.text(xs[1] + 0.005, y, code, fontsize=10, color=INK, va="center",
                family="monospace")
        ax.text(xs[2] + 0.005, y, str(n), fontsize=11, color=INK, va="center")
        ax.text(xs[3] + 0.005, y, f"${unit:,.0f}", fontsize=11, color=INK, va="center")
        ax.text(xs[4] + 0.005, y, f"${ext:,.0f}", fontsize=11, color=INK,
                va="center", fontweight="bold")
        y -= 0.06
    ax.plot([0, 1], [y + 0.02, y + 0.02], color="#bbb", lw=1)
    ax.text(xs[3] + 0.005, y - 0.02, "MATCH TOTAL", fontsize=13,
            fontweight="bold", color=INK, va="center", ha="left")
    grand = sum(s[4] for s in summ)
    ax.text(xs[4] + 0.005, y - 0.02, f"${grand:,.0f}", fontsize=15,
            fontweight="bold", color="#1a6a1a", va="center")
    ax.text(0.0, 0.10, "Prototype, single-unit pricing — order-of-magnitude, "
            "not a quote. Pitch infrastructure (Dementor server, UWB/RTK anchors, "
            "hoops, nets, charging pits) is a separate package.",
            fontsize=8.5, style="italic", color="#666", va="top")
    ax.text(0.0, 0.05, "The real moat isn't the bill of materials — it's the "
            "collision-avoidance software that makes all of this not kill anyone.",
            fontsize=9, color="#444", va="top")
    pdf.savefig(fig, facecolor=PAPER)
    fig.savefig(os.path.join(RENDERS, "sheet_fleet.png"), facecolor=PAPER, dpi=96)
    plt.close(fig)


def _clip(s, n):
    return s if len(s) <= n else s[: n - 1] + "…"


def _wrap(s, n):
    out, line = [], ""
    for word in s.split():
        if len(line) + len(word) + 1 > n:
            out.append(line); line = word
        else:
            line = (line + " " + word).strip()
    if line:
        out.append(line)
    return "\n".join(out)


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(RENDERS, exist_ok=True)
    # individual part PDFs
    for part in PARTS:
        with PdfPages(os.path.join(OUT, f"{part}.pdf")) as pdf:
            sheet(pdf, part)
    # the whole package
    combined = os.path.join(OUT, "NIMBUS_hardware_drawings.pdf")
    with PdfPages(combined) as pdf:
        cover(pdf)
        for part in ["broom", "snitch", "bludger", "quaffle"]:
            sheet(pdf, part)
        fleet_sheet(pdf)
    print(f"wrote {combined}")
    print(f"wrote bom/SUMMARY.csv")


if __name__ == "__main__":
    main()
