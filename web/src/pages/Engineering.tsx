import { Link } from "react-router-dom";
import Reveal from "../components/Reveal";
import Ornament from "../components/Ornament";

const intent = [
  ["Tilt the handle forward", "Interpreted as intent to advance; accelerates within a safe speed envelope."],
  ["Lean to the left", "Initiates a left turn, constrained by a maximum bank angle."],
  ["Pull the throttle grip", "Climbs, limited by a soft altitude ceiling."],
  ["Do nothing", "Holds an automatic hover. The craft cannot fall."],
];

const layers = [
  {
    n: "Layer 1",
    t: "Centralized avoidance — Dementor",
    d: "Every craft reports a centimeter-accurate position via RTK-GPS and UWB. The server runs collision prediction hundreds of times per second and issues avoidance commands by priority rule.",
    tag: "Software",
  },
  {
    n: "Layer 2",
    t: "Onboard avoidance — LiDAR and vision",
    d: "If the central server fails, each craft avoids obstacles using its own LiDAR. The invariant that a ball must never strike a person is hardcoded into firmware and cannot be overridden.",
    tag: "Edge",
  },
  {
    n: "Layer 3",
    t: "Physical safety — materials",
    d: "Airbag shells, foam, and ducted fans throughout. No exposed propellers. Helmets, goggles, and five-point harnesses. Stadium netting and crash mats. Contact does not injure.",
    tag: "Material",
  },
];

const energy = [
  {
    title: "Broom — series hybrid",
    problem: "A 120 kg manned eVTOL cannot complete a full match on batteries alone.",
    fix: "A micro-turbine generator running on sustainable fuel supplies average power, while the battery is reassigned to a 250 kW peak buffer.",
    stats: [
      ["Match endurance", "25.7 min"],
      ["Thrust-to-weight", "1.77"],
      ["Genset", "29.8 kg"],
      ["Fuel (SAF)", "15 kg"],
    ],
  },
  {
    title: "Snitch — beamed power",
    problem: "A 50 g sphere has no disk area, draws roughly 22 W, and carries only 1.1 Wh — exhausted in about 2.7 minutes.",
    fix: "Instead of carrying energy, it receives it. A 5.8 GHz phased array beams power, and the gold dimple vents double as a conformal rectenna. Added mass: zero.",
    stats: [
      ["Match endurance", "Continuous"],
      ["Pit stops", "0"],
      ["Beam power", "~2.5 kW"],
      ["Added mass", "~0 g"],
    ],
  },
];

const specs = [
  ["Flight volume", "100 m × 50 m × 15–20 m"],
  ["Team composition", "7 vs 7 — 14 eVTOLs"],
  ["Maximum altitude", "~15 m per league rules"],
  ["Bludger ruling", "Proximity detection triggers a timed penalty hover"],
  ["Snitch capture", "Enclosure within the hitbox for a set interval"],
  ["Kill switch", "All craft halt within 0.1 s and land simultaneously"],
];

const balls = [
  { dot: "bg-quaffle", t: "Quaffle — gentle and slow", d: "The scoring ball, thrown by hand. Capacitive touch and an IMU register a catch and cut thrust to zero. Finger safety is the first priority.", img: "quaffle_hero" },
  { dot: "bg-bludger", t: "Bludger — the disruptor", d: "The fastest and most aggressive object. It halts 10–30 cm before contact. A hit is a proximity ruling, never a physical collision.", img: "bludger_hero" },
  { dot: "bg-gold", t: "Snitch — the decisive objective", d: "The pinnacle of predictive evasion. It anticipates a pursuer's future position and breaks the opposite way, using chaotic feints to resist learning.", img: "snitch_hero" },
];

export default function Engineering() {
  return (
    <>
      {/* HERO */}
      <section className="relative flex min-h-[72svh] items-center overflow-hidden pt-20">
        <img src="/img/blueprint.png" alt="" className="absolute inset-0 h-full w-full object-cover opacity-40" />
        <div className="absolute inset-0 bg-gradient-to-b from-ink/80 via-ink/60 to-ink" />
        <div className="container-x relative z-10">
          <Reveal>
            <p className="eyebrow">Engineering · How it flies</p>
            <h1 className="display mt-5 max-w-4xl text-4xl font-bold leading-[1.06] text-parchment md:text-6xl">
              Not magic — a <span className="gold-text">rigorous collision-avoidance system.</span>
            </h1>
            <p className="mt-6 max-w-2xl font-serif text-lg leading-relaxed text-parchment/75">
              Fourteen pilots contest the air while three balls fly autonomously. Keeping them from
              colliding is eighty percent of the project. Making it beautiful is the rest.
            </p>
          </Reveal>
        </div>
      </section>

      {/* ARCHITECTURE */}
      <section className="relative py-24">
        <div className="container-x">
          <Reveal>
            <p className="eyebrow text-center">System architecture</p>
            <h2 className="display mt-4 text-center text-3xl font-bold text-parchment md:text-5xl">
              The <span className="gold-text">Dementor</span> sees everything
            </h2>
            <Ornament className="mt-6" />
          </Reveal>

          <Reveal delay={0.1}>
            <div className="mx-auto mt-12 max-w-4xl">
              <div className="card text-center !border-gold/40">
                <div className="font-display text-xs uppercase tracking-[0.3em] text-gold/60">Central server · GCS</div>
                <div className="display mt-1 text-2xl font-bold text-gold-soft">Dementor</div>
                <p className="mt-2 font-serif text-sm text-parchment/65">
                  Real-time tracking of all craft, collision-avoidance arbitration, scoring and
                  foul rulings, and the master kill switch.
                </p>
              </div>
              <div className="mx-auto my-4 h-8 w-px bg-gradient-to-b from-gold/60 to-transparent" />
              <div className="grid gap-4 sm:grid-cols-3">
                {[
                  ["Broom eVTOLs", "14 craft · manned"],
                  ["Three balls", "Swarm drones · autonomous"],
                  ["Stadium infrastructure", "Anchors, netting, beam antennas"],
                ].map(([t, d]) => (
                  <div key={t} className="card text-center">
                    <div className="font-display tracking-[0.1em] text-parchment">{t}</div>
                    <div className="mt-1 font-serif text-sm text-parchment/55">{d}</div>
                  </div>
                ))}
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* FLY BY INTENT */}
      <section className="relative py-24">
        <div className="container-x grid items-center gap-12 md:grid-cols-2">
          <Reveal>
            <p className="eyebrow">Fly-by-intent</p>
            <h2 className="display mt-4 text-3xl font-bold leading-tight text-parchment md:text-4xl">
              The pilot <span className="gold-text">does not steer.</span>
            </h2>
            <p className="mt-6 font-serif text-lg leading-relaxed text-parchment/70">
              Allowing an untrained person to fly freely would be dangerous within seconds. Instead,
              the pilot supplies <strong className="text-gold-soft">intent only</strong>, and the
              flight computer executes it. The design goal is a single sentence:
            </p>
            <blockquote className="mt-6 border-l-2 border-gold/60 pl-5 font-display text-xl italic text-gold-bright">
              "It must be impossible to crash through poor flying."
            </blockquote>
          </Reveal>
          <Reveal delay={0.12}>
            <div className="overflow-hidden rounded-md border border-gold/20">
              <div className="grid grid-cols-2 bg-gold/10 font-display text-xs uppercase tracking-[0.2em] text-gold-soft">
                <div className="p-4">Pilot input</div>
                <div className="border-l border-gold/20 p-4">What actually happens</div>
              </div>
              {intent.map(([a, b], i) => (
                <div key={i} className="grid grid-cols-2 border-t border-white/5 text-sm">
                  <div className="p-4 font-serif text-parchment/80">{a}</div>
                  <div className="border-l border-gold/10 p-4 font-serif text-parchment/60">{b}</div>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* INSIDE-OUT BALL */}
      <section className="relative py-24">
        <div className="container-x">
          <Reveal>
            <p className="eyebrow text-center">Core invention</p>
            <h2 className="display mt-4 text-center text-3xl font-bold text-parchment md:text-5xl">
              The inside-out <span className="gold-text">drone ball</span>
            </h2>
            <p className="mx-auto mt-6 max-w-3xl text-center font-serif text-lg leading-relaxed text-parchment/70">
              Conventional designs wrap a shell around a drone, which blocks airflow and prevents
              lift. We invert the concept:
              <strong className="text-gold-soft"> a shock-absorbing airbag shell on the outside, a swarm of tiny micro-drones within.</strong>{" "}
              Thrust escapes through the shell's dimple vents, which also serve as camera ports.
            </p>
          </Reveal>
          <div className="mt-14 grid gap-6 md:grid-cols-3">
            {balls.map((b, i) => (
              <Reveal key={b.t} delay={i * 0.08}>
                <div className="card group h-full text-center">
                  <div className="flex h-36 items-center justify-center">
                    <img src={`/img/${b.img}.png`} alt={b.t} className="max-h-32 animate-floaty object-contain transition-transform duration-700 group-hover:scale-110" />
                  </div>
                  <div className="mt-4 flex items-center justify-center gap-2">
                    <span className={`h-2.5 w-2.5 rounded-full ${b.dot}`} />
                    <h3 className="font-display tracking-[0.05em] text-gold-soft">{b.t}</h3>
                  </div>
                  <p className="mt-2 font-serif text-sm leading-relaxed text-parchment/65">{b.d}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* SAFETY LAYERS */}
      <section className="relative py-24">
        <div className="container-x">
          <Reveal>
            <p className="eyebrow text-center">Three-layer safety</p>
            <h2 className="display mt-4 text-center text-3xl font-bold text-parchment md:text-5xl">
              If one layer fails, <span className="gold-text">no one is hurt</span>
            </h2>
          </Reveal>
          <div className="mt-14 grid gap-6 md:grid-cols-3">
            {layers.map((l, i) => (
              <Reveal key={l.n} delay={i * 0.1}>
                <div className="card h-full">
                  <div className="flex items-center justify-between">
                    <span className="font-display text-xs uppercase tracking-[0.3em] text-gold/60">{l.n}</span>
                    <span className="rounded-full border border-gold/30 px-3 py-1 font-display text-[10px] uppercase tracking-[0.2em] text-gold-soft">
                      {l.tag}
                    </span>
                  </div>
                  <h3 className="mt-4 font-display text-lg leading-snug text-parchment">{l.t}</h3>
                  <p className="mt-3 font-serif text-[15px] leading-relaxed text-parchment/65">{l.d}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ENERGY */}
      <section className="relative overflow-hidden py-24">
        <img src="/img/embers.png" alt="" className="absolute inset-0 h-full w-full object-cover opacity-30" />
        <div className="absolute inset-0 bg-gradient-to-b from-ink via-ink/80 to-ink" />
        <div className="container-x relative z-10">
          <Reveal>
            <p className="eyebrow text-center">Lasting a full match</p>
            <h2 className="display mt-4 text-center text-3xl font-bold text-parchment md:text-5xl">
              The power problem, <span className="gold-text">solved two ways</span>
            </h2>
            <p className="mx-auto mt-6 max-w-3xl text-center font-serif text-lg leading-relaxed text-parchment/70">
              One philosophy, opposite levers. The broom{" "}
              <strong className="text-gold-soft">carries its energy</strong>; the snitch{" "}
              <strong className="text-gold-soft">receives it.</strong>
            </p>
          </Reveal>
          <div className="mt-14 grid gap-6 md:grid-cols-2">
            {energy.map((e, i) => (
              <Reveal key={e.title} delay={i * 0.1}>
                <div className="card h-full !border-gold/30">
                  <h3 className="display text-xl font-bold text-gold-soft">{e.title}</h3>
                  <div className="mt-5 rounded-sm border border-quaffle/30 bg-quaffle/5 p-4">
                    <div className="font-display text-[11px] uppercase tracking-[0.2em] text-quaffle">Problem</div>
                    <p className="mt-1 font-serif text-sm text-parchment/75">{e.problem}</p>
                  </div>
                  <div className="mt-3 rounded-sm border border-gold/30 bg-gold/5 p-4">
                    <div className="font-display text-[11px] uppercase tracking-[0.2em] text-gold">Solution</div>
                    <p className="mt-1 font-serif text-sm text-parchment/75">{e.fix}</p>
                  </div>
                  <div className="mt-5 grid grid-cols-2 gap-3">
                    {e.stats.map(([k, v]) => (
                      <div key={k} className="rounded-sm border border-white/5 bg-white/[0.02] p-3 text-center">
                        <div className="display text-xl font-bold text-gold-bright">{v}</div>
                        <div className="mt-1 font-display text-[10px] uppercase tracking-[0.2em] text-parchment/50">{k}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
          <Reveal delay={0.2}>
            <p className="mt-8 text-center font-serif text-sm text-parchment/50">
              The calculations are verified in code —{" "}
              <Link to="/codex" className="text-gold-soft underline-offset-4 hover:underline">
                view hardware/analysis/snitch_endurance.py ▸
              </Link>
            </p>
          </Reveal>
        </div>
      </section>

      {/* SPECS */}
      <section className="relative py-24">
        <div className="container-x">
          <Reveal>
            <p className="eyebrow text-center">The pitch · proposed spec</p>
            <h2 className="display mt-4 text-center text-3xl font-bold text-parchment md:text-5xl">
              The field and the <span className="gold-text">rules</span>
            </h2>
          </Reveal>
          <Reveal delay={0.1}>
            <div className="mx-auto mt-12 max-w-3xl divide-y divide-white/5 rounded-md border border-gold/15">
              {specs.map(([k, v]) => (
                <div key={k} className="flex items-center justify-between gap-4 p-5">
                  <span className="font-display tracking-[0.1em] text-parchment/80">{k}</span>
                  <span className="text-right font-serif text-gold-soft">{v}</span>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
