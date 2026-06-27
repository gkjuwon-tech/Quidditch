import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";

const links = [
  { to: "/", label: "The Dream" },
  { to: "/engineering", label: "Engineering" },
  { to: "/codex", label: "The Code" },
  { to: "/fund", label: "Join" },
];

export default function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const loc = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    onScroll();
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => setOpen(false), [loc.pathname]);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-500 ${
        scrolled
          ? "border-b border-gold/15 bg-ink/85 backdrop-blur-md"
          : "border-b border-transparent bg-gradient-to-b from-black/50 to-transparent"
      }`}
    >
      <nav className="container-x flex h-16 items-center justify-between md:h-20">
        <Link to="/" className="group flex items-center gap-3">
          <svg width="26" height="26" viewBox="0 0 34 18" className="text-gold" fill="none">
            <path d="M1 9c5-6 9-6 12 0M33 9c-5-6-9-6-12 0" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
            <circle cx="17" cy="9" r="3.6" fill="currentColor" />
          </svg>
          <div className="leading-none">
            <div className="font-display text-lg font-bold tracking-[0.18em] text-parchment">
              NIMBUS<span className="text-gold">-9¾</span>
            </div>
            <div className="font-display text-[9px] uppercase tracking-[0.42em] text-gold/60">
              Real Quidditch
            </div>
          </div>
        </Link>

        <div className="hidden items-center gap-9 md:flex">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/"}
              className={({ isActive }) =>
                `group relative font-display text-sm tracking-[0.2em] transition-colors ${
                  isActive ? "text-gold-bright" : "text-parchment/75 hover:text-gold-soft"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {l.label}
                  <span aria-hidden
                    className={`absolute -bottom-2 left-0 h-px bg-gold transition-all duration-300 ${
                      isActive ? "w-full" : "w-0 group-hover:w-full"
                    }`}
                  />
                </>
              )}
            </NavLink>
          ))}
          <Link to="/fund" className="btn-gold !px-5 !py-2.5 text-xs">
            Support
          </Link>
        </div>

        <button
          className="text-gold md:hidden"
          aria-label="menu"
          onClick={() => setOpen((v) => !v)}
        >
          <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
            {open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M3 6h18M3 12h18M3 18h18" />}
          </svg>
        </button>
      </nav>

      {open && (
        <div className="border-t border-gold/10 bg-ink/95 px-6 py-4 md:hidden">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.to === "/"}
              className={({ isActive }) =>
                `flex items-baseline justify-between border-b border-white/5 py-3 font-display tracking-[0.2em] ${
                  isActive ? "text-gold-bright" : "text-parchment/80"
                }`
              }
            >
              <span>{l.label}</span>
            </NavLink>
          ))}
        </div>
      )}
    </header>
  );
}
