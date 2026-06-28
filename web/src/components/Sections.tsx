import Reveal from "./Reveal";

const balls = [
  {
    color: "#e0563f",
    name: "Quaffle",
    tag: "The gentle one",
    body: "The main ball players carry and throw. A capacitive touch sensor reads ‘caught’ and drops thrust to zero, so it never buzzes in your hands. Throw it and the drone quietly corrects the arc.",
    quip: "“The ball that has to be safest. Finger protection, priority one.”",
  },
  {
    color: "#9aa0aa",
    name: "Bludger",
    tag: "The one that hates you",
    body: "Make it out of iron and everyone dies. So: a black airbag shell. LiDAR predictive avoidance stops it 10 cm before contact. Scoring is by proximity, not impact.",
    quip: "“Doesn’t hurt when it hits you, but the record says you’re dead. Like life.”",
  },
  {
    color: "#f4d27a",
    name: "Golden Snitch",
    tag: "The god of this game",
    body: "A walnut-sized golden sphere with a champion evasion AI inside. It predicts the chaser’s future position and flees the other way. You must cup it for N milliseconds to catch it.",
    quip: "“We crammed a drone-racing evasion AI into a walnut.”",
  },
];

const layers = [
  {
    no: "01",
    title: "Central avoidance — “The Dementor”",
    body: "Every craft reports its position to the central server in centimetres via RTK-GPS and UWB. It predicts collisions hundreds of times per second and, when a risky pair appears, orders one of them to dodge within 0.05 s.",
  },
  {
    no: "02",
    title: "Onboard avoidance — edge autonomy",
    body: "If the central server dies or comms drop, every craft dodges on its own with its own LiDAR. The invariant ‘a ball never strikes a person’ is hard-coded into firmware — unchangeable.",
  },
  {
    no: "03",
    title: "Physical safety — materials",
    body: "And if something still touches: airbags, foam, ducted fans everywhere. Zero exposed propellers. Players wear helmets, goggles and five-point harnesses. The arena has a carrier-deck-style arrest net.",
  },
];

const phases = [
  { ph: "Phase 0", now: true, badge: "NOW", title: "On paper", body: "Spec, rulebook, safety concept. Zero hardware, zero code. You are here." },
  { ph: "Phase 1", title: "Balls first", body: "Just the three balls as swarm drones, no people. Empty gym. Nothing to kill." },
  { ph: "Phase 2", title: "Uncrewed broom", body: "Fly a sandbag dummy. Validate geofencing, auto-hover, crash safety. The dummy doesn’t cry." },
  { ph: "Phase 3", title: "First crewed solo", body: "One safety marshal, low altitude, over the net. The first footage of a human actually flying." },
  { ph: "Phase 4", title: "1 vs 1", body: "Two players, one ball, a mini match. Collision avoidance under real conditions." },
  { ph: "Phase 5", title: "Full match", body: "7 vs 7, all three balls. An invited crowd. The historic opening match." },
];

export default function Sections() {
  return (
    <div className="pages">
      {/* HERO — copy sits below the 3D wordmark, panel-free so 3D reads through */}
      <section className="screen hero-screen" id="top">
        <div className="hero-copy">
          <div className="kicker">CODENAME · NIMBUS-9¾ · PHASE 0</div>
          <p className="hero-sub">
            In 2001, Quidditch was a <b>fantasy</b>.
            <br />
            In 2026, it’s an <b>engineering project</b>.
          </p>
          <p className="hero-note">
            Not CGI. Not wires. Not magic. Just a collision-avoidance algorithm
            we wrote really, really well.
          </p>
        </div>
        <div className="scrollcue">
          SCROLL<i />
        </div>
      </section>

      {/* MANIFESTO */}
      <section className="screen" id="manifesto">
        <div className="content">
          <Reveal>
            <div className="eyebrow">Why nobody has done this</div>
            <p className="pull">
              Human sport has always been <b>two-dimensional</b>. We were trapped
              on the X and Y axes. <b>The Z-axis was empty.</b> The sky was empty.
            </p>
          </Reveal>
          <Reveal>
            <p className="lead">
              The people who could build it had no money. The people with money
              never read Harry Potter. But look — <b>eVTOLs</b> already have
              thousands of crewed test flights. <b>Drone swarms</b> put 2,000
              craft over an Olympic opening ceremony. <b>LiDAR</b> now costs about
              as much as a parcel. The parts are all on the shelf. We’re just
              assembling them in a <b>gloriously stupid way</b>. That’s the
              innovation.
            </p>
          </Reveal>
        </div>
      </section>

      {/* BALLS */}
      <section className="screen tall" id="balls">
        <div className="content">
          <Reveal>
            <div className="eyebrow">The core invention</div>
            <h2 className="h2">
              The inside-out <em>drone-ball</em>
            </h2>
            <p className="lead">
              Until now, people wrapped a shell around a drone. The propeller wash
              gets trapped and it won’t fly. We flip it: a soft airbag shell on the
              outside, an absurdly small swarm drone on the inside, looking out.
              The crowd just sees a ball that flies with a will of its own. That’s
              magic — the word we use for engineering that’s been hidden well.
            </p>
          </Reveal>
          <div className="grid3">
            {balls.map((b, i) => (
              <Reveal key={b.name} className="card" style={{ transitionDelay: `${i * 90}ms` }}>
                <div className="card__dot" style={{ background: b.color, color: b.color }} />
                <h3>{b.name}</h3>
                <span className="tag">{b.tag}</span>
                <p>{b.body}</p>
                <p className="quip">{b.quip}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* SAFETY */}
      <section className="screen tall" id="safety">
        <div className="content">
          <Reveal>
            <div className="eyebrow">The triple safety net — where lives are decided</div>
            <h2 className="h2">
              Nobody dies. <em>Even if two systems fail.</em>
            </h2>
            <p className="lead">
              It’s a sport where 14 people fly drones and body-check each other
              midair while three balls fly autonomously. Keeping them from
              colliding is 80% of the project. The other 20% is “make it look
              cool.”
            </p>
          </Reveal>
          <div className="layers">
            {layers.map((l, i) => (
              <Reveal key={l.no} className="layer" style={{ transitionDelay: `${i * 80}ms` }}>
                <div className="layer__no">{l.no}</div>
                <div>
                  <h4>{l.title}</h4>
                  <p>{l.body}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* ROADMAP */}
      <section className="screen tall" id="roadmap">
        <div className="content">
          <Reveal>
            <div className="eyebrow">Roadmap — staying alive, one stage at a time</div>
            <h2 className="h2">
              2030, <em>the RQL opening match.</em>
            </h2>
            <p className="lead">
              Someone in the stands is crying. Whether or not it’s J.K. Rowling,
              we don’t care. Because we flew.
            </p>
          </Reveal>
          <div className="road">
            {phases.map((p, i) => (
              <Reveal
                key={p.ph}
                className={`phase ${p.now ? "now" : ""}`}
                style={{ transitionDelay: `${i * 60}ms` }}
              >
                {p.badge && <span className="badge">{p.badge}</span>}
                <span className="ph">{p.ph}</span>
                <h5>{p.title}</h5>
                <p>{p.body}</p>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* CTA + FOOTER */}
      <section className="screen cta-screen" id="cta">
        <div className="cta-inner">
          <Reveal>
            <h2 className="h2 cta-h">
              Let’s go. Let’s fly the first <em>real broom</em> in human history.
            </h2>
            <div className="row">
              <a className="btn" href="https://github.com/gkjuwon-tech/Quidditch" target="_blank" rel="noreferrer">
                Get the investor deck
              </a>
              <a className="btn btn--ghost" href="https://github.com/gkjuwon-tech/Quidditch" target="_blank" rel="noreferrer">
                Read the full spec
              </a>
            </div>
            <p className="hero-note cta-note">
              “It’s not magic. We just wrote the collision-avoidance algorithm
              really, really well.”
            </p>
          </Reveal>
        </div>
        <footer className="footer">
          <div>NIMBUS-9¾ · Quidditch, made real — Phase 0, on paper</div>
          <div className="footer__links">
            <span className="soon">Codex (soon)</span>
            <span className="soon">Engineering (soon)</span>
            <span className="soon">Sponsorship (soon)</span>
            <a href="https://github.com/gkjuwon-tech/Quidditch" target="_blank" rel="noreferrer">
              GitHub ↗
            </a>
          </div>
        </footer>
      </section>
    </div>
  );
}
