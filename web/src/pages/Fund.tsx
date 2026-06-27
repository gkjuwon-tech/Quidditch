import { useState } from "react";
import Reveal from "../components/Reveal";
import Ornament from "../components/Ornament";

const tiers = [
  {
    price: "$5",
    name: "Believer",
    sub: "No barrier · every name counts",
    perks: ["Your name in the permanent backer roll", "Full access to the dev log"],
  },
  {
    price: "$9",
    per: "/mo",
    name: "House member",
    sub: "Recurring support",
    perks: ["Private community access", "Full dev log", "Predictable funding that keeps the project alive"],
  },
  {
    price: "$29",
    name: "Chaser",
    sub: "Merchandise + belonging",
    perks: ["Everything above", "T-shirt and sticker pack", "\u201cMagic? No, just collision-avoidance\u201d"],
  },
  {
    price: "$69",
    name: "Catch-the-Snitch No. 1",
    sub: "Pre-order the product",
    perks: ["Pre-order the avoidance-equipped chase drone", "A dream and a real object", "Everything above"],
    hot: true,
  },
  {
    price: "$199",
    name: "Seeker",
    sub: "For the dedicated",
    perks: ["Invitation to the first manned-hover livestream", "Full merchandise set", "Everything above"],
  },
  {
    price: "Contact",
    name: "First-flight witness",
    sub: "Major backers · media",
    perks: ["Be present at the first manned broom flight", "On site, in person", "A witness to history"],
  },
];

const why = [
  ["No equity dilution", "The project stays entirely in the hands of the people building it."],
  ["No board", "No pressure to pivot away from the mission toward something safer."],
  ["The crowd becomes the team", "A backer is an advocate. Supporters share and grow the project on their own."],
  ["Resilient by design", "Losing one large investor is fatal; tens of thousands of small backers are not."],
];

const channels = [
  ["One-time crowdfunding", "Starting at $5, with attainable goals so momentum builds early."],
  ["Monthly membership", "About the price of a coffee — the recurring support that sustains the work."],
  ["Merchandise", "Miniature brooms, apparel, and snitch keyrings."],
  ["\u201cCatch-the-Snitch\u201d pre-orders", "A genuine consumer product backers can buy for themselves or as a gift."],
  ["Name in the credits", "A permanent place in the backer roll."],
  ["Convention booth QR", "Support on the spot, in the moment, at live events."],
];

const presets = ["$5", "$9", "$29", "Custom"];

export default function Fund() {
  const [amount, setAmount] = useState("$5");

  return (
    <>
      {/* HERO */}
      <section className="relative flex min-h-[78svh] items-center overflow-hidden pt-20">
        <img src="/img/embers.png" alt="" className="absolute inset-0 h-full w-full object-cover opacity-60" />
        <div className="absolute inset-0 bg-gradient-to-b from-ink/85 via-ink/55 to-ink" />
        <img
          src="/img/crest.png"
          alt=""
          className="absolute right-[-4%] top-1/2 z-0 hidden w-[34rem] -translate-y-1/2 opacity-20 mix-blend-screen md:block"
        />
        <div className="container-x relative z-10">
          <Reveal>
            <p className="eyebrow">Join · Backed by its community</p>
            <h1 className="display mt-5 max-w-4xl text-4xl font-bold leading-[1.08] text-parchment md:text-6xl">
              The acceptance letter your eleven-year-old self waited for
              <br />
              <span className="gold-text">is finally arriving.</span>
            </h1>
            <p className="mt-7 max-w-2xl font-serif text-lg leading-relaxed text-parchment/75">
              We are funded by the people who love this, not by institutional capital. Rather than
              spend months convincing a single large investor, we move faster and stay free by
              earning the support of many.
            </p>
          </Reveal>
        </div>
      </section>

      {/* THE HOOK + DONATE WIDGET */}
      <section className="relative py-24">
        <div className="container-x grid items-center gap-12 md:grid-cols-2">
          <Reveal>
            <p className="eyebrow">Why this matters</p>
            <h2 className="display mt-4 text-3xl font-bold leading-tight text-parchment md:text-4xl">
              Magic was never real.
              <br />
              <span className="gold-text">We are engineering it — and you can be part of it.</span>
            </h2>
            <div className="mt-8 space-y-3">
              {[
                "No one had built this before because the cost and coordination only just became feasible.",
                "The technology is finally proven and affordable.",
                "A small contribution puts your name permanently in the record.",
              ].map((h) => (
                <div key={h} className="flex gap-3 font-serif text-parchment/75">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rotate-45 bg-gold" />
                  <span>{h}</span>
                </div>
              ))}
            </div>
          </Reveal>

          <Reveal delay={0.12}>
            <div className="card !border-gold/40 !p-8">
              <div className="font-display text-xs uppercase tracking-[0.3em] text-gold/60">One-time support</div>
              <h3 className="display mt-2 text-2xl font-bold text-parchment">It takes only a moment.</h3>
              <div className="mt-6 grid grid-cols-2 gap-3">
                {presets.map((p) => (
                  <button
                    key={p}
                    onClick={() => setAmount(p)}
                    className={`rounded-sm border px-4 py-4 font-display tracking-[0.1em] transition-all ${
                      amount === p
                        ? "border-gold bg-gold/15 text-gold-bright"
                        : "border-gold/25 text-parchment/70 hover:border-gold/60"
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
              <button className="btn-gold mt-6 w-full">
                {amount === "Custom" ? "Choose your amount" : `Support with ${amount}`}
              </button>
              <p className="mt-4 text-center font-serif text-xs text-parchment/45">
                * This is a demo page. Payment integration goes live when crowdfunding opens.
              </p>
            </div>
          </Reveal>
        </div>
      </section>

      {/* TIERS */}
      <section className="relative py-20">
        <div className="container-x">
          <Reveal>
            <p className="eyebrow text-center">Tiers</p>
            <h2 className="display mt-4 text-center text-3xl font-bold text-parchment md:text-5xl">
              Not a reward — a <span className="gold-text">place in the house</span>
            </h2>
            <Ornament className="mt-6" />
          </Reveal>
          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {tiers.map((t, i) => (
              <Reveal key={t.name} delay={i * 0.06}>
                <div
                  className={`card relative flex h-full flex-col ${
                    t.hot ? "!border-gold/60 shadow-glow" : ""
                  }`}
                >
                  {t.hot && (
                    <span className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-gold px-4 py-1 font-display text-[10px] uppercase tracking-[0.25em] text-ink">
                      Most popular
                    </span>
                  )}
                  <div className="flex items-baseline gap-1">
                    <span className="display text-3xl font-bold text-gold-bright">{t.price}</span>
                    {t.per && <span className="font-display text-sm text-parchment/50">{t.per}</span>}
                  </div>
                  <h3 className="mt-3 font-display text-lg tracking-[0.05em] text-parchment">{t.name}</h3>
                  <div className="font-display text-[11px] uppercase tracking-[0.2em] text-gold/50">{t.sub}</div>
                  <ul className="mt-5 flex-1 space-y-2.5">
                    {t.perks.map((p) => (
                      <li key={p} className="flex gap-2 font-serif text-sm leading-relaxed text-parchment/70">
                        <span className="mt-1 text-gold">✦</span>
                        <span>{p}</span>
                      </li>
                    ))}
                  </ul>
                  <button className={`mt-6 ${t.hot ? "btn-gold" : "btn-ghost"} w-full`}>
                    {t.price === "Contact" ? "Get in touch" : "Choose this tier"}
                  </button>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* WHY SMALL-MANY */}
      <section className="relative py-24">
        <div className="container-x">
          <Reveal>
            <p className="eyebrow text-center">Why many small backers</p>
            <h2 className="display mt-4 text-center text-3xl font-bold text-parchment md:text-5xl">
              Community funding is not slower — it is <span className="gold-text">freer</span>
            </h2>
          </Reveal>
          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {why.map((w, i) => (
              <Reveal key={w[0]} delay={i * 0.08}>
                <div className="card h-full">
                  <div className="font-display tracking-[0.05em] text-gold-soft">{w[0]}</div>
                  <p className="mt-3 font-serif text-sm leading-relaxed text-parchment/65">{w[1]}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* CHANNELS */}
      <section className="relative py-20">
        <div className="container-x">
          <Reveal>
            <p className="eyebrow text-center">Ways to support</p>
            <h2 className="display mt-4 text-center text-3xl font-bold text-parchment md:text-5xl">
              Many small channels, <span className="gold-text">not one large ask</span>
            </h2>
          </Reveal>
          <div className="mt-14 grid gap-4 md:grid-cols-2">
            {channels.map(([t, d], i) => (
              <Reveal key={t} delay={i * 0.05}>
                <div className="card flex items-start gap-4 !p-5">
                  <div className="font-display text-xl font-bold text-gold/40">{`0${i + 1}`}</div>
                  <div>
                    <div className="font-display tracking-[0.05em] text-gold-soft">{t}</div>
                    <p className="mt-1 font-serif text-sm leading-relaxed text-parchment/60">{d}</p>
                  </div>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* CLOSING */}
      <section className="relative overflow-hidden py-28">
        <img src="/img/embers.png" alt="" className="absolute inset-0 h-full w-full object-cover opacity-50" />
        <div className="absolute inset-0 bg-gradient-to-b from-ink via-transparent to-ink" />
        <div className="container-x relative z-10 mx-auto max-w-3xl text-center">
          <Reveal>
            <Ornament />
            <p className="mt-6 font-serif text-xl leading-relaxed text-parchment/85 md:text-2xl">
              You are not simply donating. You are helping deliver the acceptance letter your
              eleven-year-old self waited for. We intend to fly this for real — and you will be
              able to say
              <span className="gold-text"> you were there.</span>
            </p>
            <div className="mt-10">
              <a href="#top" className="btn-gold">Join now</a>
            </div>
          </Reveal>
        </div>
      </section>
    </>
  );
}
