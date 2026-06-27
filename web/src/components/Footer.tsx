import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="relative z-10 border-t border-gold/15 bg-black/40">
      <div className="container-x grid gap-10 py-16 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <div className="font-display text-2xl font-bold tracking-[0.16em] text-parchment">
            NIMBUS<span className="text-gold">-9¾</span>
          </div>
          <p className="mt-4 max-w-sm font-serif text-[15px] leading-relaxed text-parchment/65">
            Magic never existed. We engineered it instead. You're not donating — you're
            collecting the Hogwarts letter your 11-year-old self waited 25 years for.
          </p>
        </div>
        <div>
          <div className="eyebrow mb-4">Explore</div>
          <ul className="space-y-2.5 font-serif text-parchment/70">
            <li><Link to="/" className="hover:text-gold-soft">The Dream</Link></li>
            <li><Link to="/engineering" className="hover:text-gold-soft">Engineering — how</Link></li>
            <li><Link to="/codex" className="hover:text-gold-soft">The Code — ours</Link></li>
            <li><Link to="/fund" className="hover:text-gold-soft">Join — back us</Link></li>
          </ul>
        </div>
        <div>
          <div className="eyebrow mb-4">Honest bit</div>
          <p className="font-serif text-sm leading-relaxed text-parchment/55">
            We use no original logos, art, or trademarked names. We ship under our own brand
            (NIMBUS). Being legally clean is this project's seatbelt.
          </p>
          <p className="mt-4 font-display text-xs tracking-[0.25em] text-gold/50">
            Phase 0 · on paper → into the sky
          </p>
        </div>
      </div>
      <div className="border-t border-white/5 py-6 text-center font-display text-[11px] uppercase tracking-[0.3em] text-parchment/40">
        © 2026 NIMBUS-9¾ Project · Magic? No, just collision-avoidance.
      </div>
    </footer>
  );
}
