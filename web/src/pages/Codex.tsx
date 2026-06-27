import { useMemo, useState } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Link } from "react-router-dom";
import Reveal from "../components/Reveal";
import { groups, allFiles, stats, type CodeFile } from "../code/exhibit";

const langLabel: Record<CodeFile["lang"], string> = {
  python: "Python",
  rust: "Rust",
  cpp: "OpenSCAD",
};

export default function Codex() {
  const [activeId, setActiveId] = useState<string>(allFiles[0].id);
  const [copied, setCopied] = useState(false);
  const active = useMemo(() => allFiles.find((f) => f.id === activeId)!, [activeId]);
  const lineCount = active.source.split("\n").length;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(active.source);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      /* clipboard may be blocked; no-op */
    }
  };

  return (
    <>
      {/* HERO */}
      <section className="relative overflow-hidden pt-28 pb-12">
        <div className="container-x">
          <Reveal>
            <p className="eyebrow">The Codex</p>
            <h1 className="display mt-5 text-4xl font-bold leading-[1.06] text-parchment md:text-6xl">
              Our <span className="gold-text">source code.</span>
            </h1>
            <p className="mt-6 max-w-2xl font-serif text-lg leading-relaxed text-parchment/75">
              The actual source of our flight-control stack, presented in full — from the avoidance
              algorithms to the beamed-power endurance analysis and the parametric CAD.
            </p>
            <div className="mt-8 flex flex-wrap gap-8">
              {[
                [stats.files, "Files"],
                [stats.lines.toLocaleString(), "Lines of source"],
                ["3", "Languages (Py·Rust·SCAD)"],
                ["5", "Subsystems"],
              ].map(([n, l]) => (
                <div key={l}>
                  <div className="display text-3xl font-bold text-gold-bright md:text-4xl">{n}</div>
                  <div className="mt-1 font-display text-[11px] uppercase tracking-[0.25em] text-parchment/50">{l}</div>
                </div>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      {/* EXHIBIT */}
      <section className="relative pb-28">
        <div className="container-x">
          <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
            {/* FILE TREE */}
            <aside className="lg:sticky lg:top-24 lg:self-start">
              <div className="rounded-md border border-gold/15 bg-black/30 p-4 backdrop-blur-sm">
                <div className="mb-3 px-2 font-display text-[11px] uppercase tracking-[0.3em] text-gold/50">
                  nimbus_fc / hardware
                </div>
                {groups.map((g) => (
                  <div key={g.id} className="mb-4">
                    <div className="flex items-center gap-2 px-2 py-1 font-display text-xs uppercase tracking-[0.2em] text-gold-soft/80">
                      <span className="text-gold">{g.icon}</span> {g.label}
                    </div>
                    <ul className="mt-1">
                      {g.files.map((f) => {
                        const on = f.id === activeId;
                        return (
                          <li key={f.id}>
                            <button
                              onClick={() => setActiveId(f.id)}
                              className={`group flex w-full items-center gap-2 rounded-sm px-3 py-2 text-left font-sans text-[13px] transition-colors ${
                                on
                                  ? "bg-gold/10 text-gold-bright"
                                  : "text-parchment/60 hover:bg-white/5 hover:text-parchment"
                              }`}
                            >
                              <span className={`h-1.5 w-1.5 shrink-0 rotate-45 ${on ? "bg-gold" : "bg-gold/30"}`} />
                              <span className="truncate">{f.path.split("/").pop()}</span>
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                ))}
              </div>
            </aside>

            {/* VIEWER */}
            <div className="min-w-0">
              <div className="overflow-hidden rounded-md border border-gold/20 bg-[#0c0a08]">
                {/* file header */}
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-gold/15 bg-black/40 px-5 py-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="flex gap-1.5">
                        <span className="h-3 w-3 rounded-full bg-quaffle/70" />
                        <span className="h-3 w-3 rounded-full bg-gold/70" />
                        <span className="h-3 w-3 rounded-full bg-emerald-500/60" />
                      </span>
                      <span className="truncate font-mono text-[13px] text-parchment/80">{active.path}</span>
                    </div>
                    <h2 className="mt-2 font-display text-lg text-gold-soft">{active.title}</h2>
                    <p className="mt-1 max-w-2xl font-serif text-sm leading-relaxed text-parchment/60">{active.blurb}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="rounded-full border border-gold/30 px-3 py-1 font-display text-[10px] uppercase tracking-[0.2em] text-gold-soft">
                      {langLabel[active.lang]}
                    </span>
                    <span className="font-mono text-xs text-parchment/40">{lineCount} lines</span>
                    <button
                      onClick={copy}
                      className="rounded-sm border border-gold/30 px-3 py-1.5 font-display text-[11px] uppercase tracking-[0.2em] text-gold-soft transition-colors hover:bg-gold/10"
                    >
                      {copied ? "Copied" : "Copy"}
                    </button>
                  </div>
                </div>

                {/* code */}
                <div className="max-h-[70vh] overflow-auto text-[13px]">
                  <SyntaxHighlighter
                    language={active.lang}
                    style={vscDarkPlus}
                    showLineNumbers
                    wrapLongLines={false}
                    customStyle={{
                      margin: 0,
                      background: "transparent",
                      padding: "1.25rem 1rem",
                      fontSize: "13px",
                    }}
                    lineNumberStyle={{ color: "rgba(217,164,65,0.3)", minWidth: "2.6em" }}
                  >
                    {active.source}
                  </SyntaxHighlighter>
                </div>
              </div>

              <p className="mt-5 text-center font-serif text-sm text-parchment/50">
                Clone the repository and run{" "}
                <code className="text-gold-soft">python scenarios/match.py seek</code> to run it locally.
              </p>
              <div className="mt-6 text-center">
                <Link to="/fund" className="btn-gold">Support this work</Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
