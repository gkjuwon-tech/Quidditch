import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import Reveal from "../components/Reveal";
import Ornament from "../components/Ornament";

const values = [
  { n: "I", k: "Real flight", v: "A pilot leaves the ground on a one-person eVTOL. No CG, no wires, no illusion." },
  { n: "II", k: "Survivable by design", v: "Crash-absorbing shells and proximity-based soft-kill scoring replace blunt force. The sport is built to be walked away from." },
  { n: "III", k: "Open and auditable", v: "Every line of flight code is public. Transparency is the foundation of trust." },
  { n: "IV", k: "Funded by its community", v: "Backed by the people who love it, not by institutional capital." },
];

const fleet = [
  { img: "broom_hero", verb: "FLY", label: "The Broom", d: "A single-seat eVTOL you ride. The flight computer handles stability so the pilot can focus on the game.", w: "col-span-2 md:col-span-2" },
  { img: "quaffle_hero", verb: "PLAY", label: "The Quaffle", d: "The scoring ball. Carried and thrown through the hoops. Deliberately slow and predictable." },
  { img: "bludger_hero", verb: "AVOID", label: "The Bludger", d: "An autonomous disruptor. Contact is soft by design, but a registered hit removes a player from the round." },
  { img: "snitch_hero", verb: "CATCH", label: "The Snitch", d: "A walnut-sized autonomous evader and the decisive objective of every match. Designed to be caught only through coordinated pursuit.", w: "col-span-2 md:col-span-2" },
];

const roadmap = [
  { y: "Phase 0", t: "On paper", d: "Specification, rulebook, and code. The current stage.", now: true },
  { y: "Phase 1", t: "Balls first", d: "Unmanned validation of the three autonomous game objects." },
  { y: "Phase 3", t: "First manned flight", d: "A pilot flies a match-spec broom for the first time." },
  { y: "Phase 5", t: "Full match", d: "A complete seven-versus-seven exhibition match." },
  { y: "Beyond", t: "The league", d: "Broadcast, structured competition, and a growing community." },
];

export default function Home() {
  return (
    <>
      {/* ===== HERO ===== */}
      <section className="relative flex min-h-[100svh] items-center justify-center overflow-hidden">
        <div className="absolute inset-0 z-0">
          <img
            src="/img/hero_stadium.png"
            alt=""
            className="h-full w-full scale-105 object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-ink/70 via-ink/40 to-ink" />
          <div className="absolute inset-0 bg-gradient-to-t from-ink via-transparent to-ink/60" />
        </div>

        <motion.img
          src="/img/snitch_hero.png"
          alt="Golden Snitch"
          className="absolute right-[8%] top-[16%] z-10 w-40 drop-shadow-[0_0_45px_rgba(246,201,69,0.55)] md:w-64"
          initial={{ opacity: 0, scale: 0.6 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.4, delay: 0.4 }}
        />

        <div className="container-x relative z-20 text-center">
          <motion.p
            className="eyebrow mb-6"
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
          >
            The world's first real Quidditch · NIMBUS-9¾
          </motion.p>
          <motion.h1
            className="display text-4xl font-bold leading-[1.05] text-parchment sm:text-6xl md:text-7xl"
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.25 }}
          >
            Magic was never real.
            <br />
            <span className="gold-text">So we engineered it.</span>
          </motion.h1>
          <motion.p
            className="mx-auto mt-7 max-w-2xl font-serif text-lg leading-relaxed text-parchment/75 md:text-xl"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.45 }}
          >
            In 2001, Quidditch was a story. In 2026, it is an engineering program.
            The sensors are affordable, the safety case is sound, and the team is assembled.
          </motion.p>
          <motion.div
            className="mt-10 flex flex-wrap items-center justify-center gap-4"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.65 }}
          >
            <Link to="/fund" className="btn-gold">
              Join the mission
            </Link>
            <Link to="/engineering" className="btn-ghost">
              See how it flies ▸
            </Link>
          </motion.div>
        </div>

        <motion.div
          className="absolute bottom-8 left-1/2 z-20 -translate-x-1/2 text-center"
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <div className="font-display text-[10px] uppercase tracking-[0.4em] text-gold/60">
            Scroll to discover
          </div>
          <div className="mx-auto mt-2 h-8 w-px bg-gradient-to-b from-gold/70 to-transparent" />
        </motion.div>
      </section>

      {/* ===== MISSION ===== */}
      <section className="relative py-28">
        <div className="container-x">
          <Reveal>
            <p className="eyebrow text-center">This is not fiction.</p>
            <h2 className="display mt-4 text-center text-3xl font-bold text-parchment md:text-5xl">
              It is a <span className="gold-text">mission.</span>
            </h2>
            <Ornament className="mt-6" />
            <p className="mx-auto mt-6 max-w-3xl text-center font-serif text-lg leading-relaxed text-parchment/70">
              We are engineers and lifelong readers building the first real-world sport in which
              people fly — safe, fair, and genuinely thrilling.
            </p>
          </Reveal>

          <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {values.map((v, i) => (
              <Reveal key={v.k} delay={i * 0.08}>
                <div className="card h-full text-center">
                  <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full border border-gold/30 font-display text-lg text-gold">
                    {v.n}
                  </div>
                  <h3 className="font-display text-lg tracking-[0.1em] text-gold-soft">{v.k}</h3>
                  <p className="mt-3 font-serif text-[15px] leading-relaxed text-parchment/65">{v.v}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ===== FLEET / EXPERIENCE ===== */}
      <section className="relative overflow-hidden py-24">
        <div className="container-x">
          <Reveal>
            <p className="eyebrow text-center">The experience we are building</p>
            <h2 className="display mt-4 text-center text-3xl font-bold text-parchment md:text-5xl">
              Fly. Play. Avoid. <span className="gold-text">Catch.</span>
            </h2>
          </Reveal>

          <div className="mt-16 grid grid-cols-2 gap-5 md:grid-cols-3">
            {fleet.map((f, i) => (
              <Reveal key={f.verb} delay={i * 0.08} className={f.w}>
                <div className="card group flex h-full flex-col items-center overflow-hidden text-center">
                  <div className="relative flex h-44 w-full items-center justify-center">
                    <img
                      src={`/img/${f.img}.png`}
                      alt={f.label}
                      className="max-h-40 w-auto object-contain transition-transform duration-700 group-hover:scale-110 animate-floaty drop-shadow-[0_18px_40px_rgba(0,0,0,0.6)]"
                    />
                  </div>
                  <div className="mt-4">
                    <div className="font-display text-xs uppercase tracking-[0.4em] text-gold/60">
                      {f.verb}
                    </div>
                    <div className="display text-2xl font-bold text-parchment">{f.label}</div>
                    <p className="mt-2 font-serif text-sm leading-relaxed text-parchment/65">{f.d}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ===== WHY NOBODY ===== */}
      <section className="relative py-24">
        <div className="container-x grid items-center gap-12 md:grid-cols-2">
          <Reveal>
            <p className="eyebrow">Why has no one built this?</p>
            <h2 className="display mt-4 text-3xl font-bold leading-tight text-parchment md:text-4xl">
              The barrier was never the technology.
              <br />
              <span className="gold-text">It was capital, coordination, and conviction.</span>
            </h2>
            <p className="mt-6 font-serif text-lg leading-relaxed text-parchment/70">
              eVTOLs, drone swarms, vision tracking, LiDAR, and predictive avoidance are all
              available off the shelf. Five years ago, LiDAR was prohibitively expensive. Today it
              is commodity hardware. The cost curve has finally crossed the line that makes this
              practical.
            </p>
            <Link to="/engineering" className="btn-ghost mt-8">
              Read the technical case ▸
            </Link>
          </Reveal>
          <Reveal delay={0.15}>
            <div className="grid gap-4">
              {[
                ["Capital", "A fleet of manned eVTOLs, an autonomous swarm, and a stadium require investment ahead of any return."],
                ["Regulation", "Autonomous craft operating above people demand a rigorous safety case. A closed, controlled venue makes that tractable."],
                ["Cross-discipline", "Aerospace, software, and sport governance rarely sit at the same table. This project requires all three."],
                ["Conviction", "It needed a team willing to treat a beloved story as a serious engineering target."],
              ].map(([t, d], i) => (
                <div key={i} className="card flex gap-4 !p-5">
                  <div className="font-display text-2xl font-bold text-gold/40">{`0${i + 1}`}</div>
                  <div>
                    <div className="font-display tracking-[0.1em] text-gold-soft">{t}</div>
                    <p className="mt-1 font-serif text-sm leading-relaxed text-parchment/60">{d}</p>
                  </div>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* ===== ROADMAP ===== */}
      <section className="relative py-24">
        <div className="container-x">
          <Reveal>
            <p className="eyebrow text-center">The road ahead</p>
            <h2 className="display mt-4 text-center text-3xl font-bold text-parchment md:text-5xl">
              Into the sky, <span className="gold-text">safely</span>
            </h2>
          </Reveal>
          <div className="mt-16 grid gap-8 md:grid-cols-5">
            {roadmap.map((r, i) => (
              <Reveal key={r.y} delay={i * 0.08}>
                <div className="relative text-center">
                  <div
                    className={`mx-auto mb-4 h-3 w-3 rotate-45 ${
                      r.now ? "bg-gold shadow-gold animate-pulseGlow" : "border border-gold/50 bg-ink"
                    }`}
                  />
                  <div className="font-display text-xs uppercase tracking-[0.3em] text-gold/60">{r.y}</div>
                  <div className="display mt-1 text-lg font-bold text-parchment">{r.t}</div>
                  <p className="mt-2 font-serif text-sm leading-relaxed text-parchment/60">{r.d}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ===== CLOSING CTA ===== */}
      <section className="relative overflow-hidden py-32">
        <img src="/img/embers.png" alt="" className="absolute inset-0 h-full w-full object-cover opacity-60" />
        <div className="absolute inset-0 bg-gradient-to-b from-ink via-transparent to-ink" />
        <div className="container-x relative z-10 text-center">
          <Reveal>
            <h2 className="display text-3xl font-bold leading-tight text-parchment md:text-5xl">
              Be part of this.
              <br />
              <span className="gold-text">The brooms are waiting.</span>
            </h2>
            <p className="mx-auto mt-6 max-w-2xl font-serif text-lg text-parchment/75">
              Any contribution moves this forward. We intend to fly it for real — and you will have
              helped make it happen.
            </p>
            <div className="mt-10 flex flex-wrap justify-center gap-4">
              <Link to="/fund" className="btn-gold">Support the mission</Link>
              <Link to="/codex" className="btn-ghost">Read our code ▸</Link>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
