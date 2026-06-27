import { useEffect, useRef } from "react";

type P = { x: number; y: number; r: number; vy: number; vx: number; a: number; tw: number };

/** Ambient drifting gold embers on a fixed full-screen canvas. */
export default function Embers({ density = 70 }: { density?: number }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current!;
    const ctx = canvas.getContext("2d")!;
    let raf = 0;
    let w = 0;
    let h = 0;
    let parts: P[] = [];
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const seed = () => {
      parts = Array.from({ length: density }, () => ({
        x: Math.random() * w,
        y: Math.random() * h,
        r: Math.random() * 1.8 + 0.4,
        vy: -(Math.random() * 0.25 + 0.05),
        vx: (Math.random() - 0.5) * 0.18,
        a: Math.random() * 0.6 + 0.15,
        tw: Math.random() * Math.PI * 2,
      }));
    };

    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
      seed();
    };

    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      for (const p of parts) {
        p.y += p.vy;
        p.x += p.vx;
        p.tw += 0.03;
        if (p.y < -10) {
          p.y = h + 10;
          p.x = Math.random() * w;
        }
        const flick = 0.6 + Math.sin(p.tw) * 0.4;
        const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 6);
        g.addColorStop(0, `rgba(255,196,92,${p.a * flick})`);
        g.addColorStop(1, "rgba(255,140,61,0)");
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * 6, 0, Math.PI * 2);
        ctx.fill();
      }
      raf = requestAnimationFrame(draw);
    };

    resize();
    window.addEventListener("resize", resize);
    if (!reduce) draw();
    else {
      // single static frame for reduced-motion users
      for (const p of parts) {
        ctx.fillStyle = `rgba(255,196,92,${p.a})`;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
    };
  }, [density]);

  return (
    <canvas
      ref={ref}
      aria-hidden
      className="pointer-events-none fixed inset-0 z-0 h-full w-full opacity-70"
    />
  );
}
