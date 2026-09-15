import { useEffect, useRef } from "react";

export type OrbState = "idle" | "listening" | "thinking" | "speaking";

const STATES: Record<OrbState, { color: string; energy: number }> = {
  idle: { color: "#7e93b4", energy: 0.18 },
  listening: { color: "#3ae0ff", energy: 0.85 },
  thinking: { color: "#a78bfa", energy: 0.55 },
  speaking: { color: "#3fdfa8", energy: 1 },
};

const TAU = Math.PI * 2;

function hexA(hex: string, a: number): string {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${Math.min(1, Math.max(0, a))})`;
}

/** Dot-blob voice orb (UI_SPEC.md §3). One canvas, ~150 lines, no deps. */
export function StatusOrb({ state, size = 300 }: { state: OrbState; size?: number }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.scale(dpr, dpr);

    const R = size * 0.42;
    const count = Math.max(90, Math.round(size * size * 0.0062));
    const dots = Array.from({ length: count }, (_, i) => ({
      r: Math.sqrt((i + 0.5) / count),
      a: i * 2.39996,
      s: Math.random() * TAU,
    }));

    const draw = (t: number) => {
      const { color: c, energy: e } = STATES[state];
      const cx = size / 2;
      const cy = size / 2;
      ctx.clearRect(0, 0, size, size);

      const g = ctx.createRadialGradient(cx, cy, R * 0.1, cx, cy, R * 1.7);
      g.addColorStop(0, hexA(c, 0.1 + 0.26 * e));
      g.addColorStop(1, hexA(c, 0));
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, size, size);

      const breathe = 1 + 0.018 * Math.sin(t * 0.8);
      const dotR = Math.max(1.1, size * 0.0068);

      for (const d of dots) {
        let ang = d.a;
        let wob = 0;
        let alpha = 0;
        const base = R * (0.16 + 0.84 * d.r) * breathe;
        const env = 0.3 + 0.7 * d.r;

        if (state === "idle") {
          wob = 3.2 * Math.sin(t * 0.8 + d.r * 4.5 + d.s) * Math.sin(t * 0.45 + ang * 2 + d.s * 0.7);
          alpha = 0.16 + 0.38 * d.r;
        } else if (state === "listening") {
          const beat = 0.5 + 0.5 * Math.sin(t * 3.3 + d.s);
          const w1 = Math.sin(ang * 3 + t * 4.4 + d.r * 5.5);
          wob = (2.5 + 9 * beat) * w1 * env;
          alpha = 0.2 + 0.5 * d.r + 0.2 * beat * Math.abs(w1);
        } else if (state === "thinking") {
          ang += t * 1.7 * (0.35 + 0.85 * d.r);
          wob = 3.6 * Math.sin(t * 3.1 + d.r * 8 + d.s) * env;
          alpha = 0.18 + 0.5 * d.r;
        } else {
          const rp = Math.sin(9 * d.r - t * 6.2 + ang * 2 + d.s * 0.4);
          wob = 7.5 * rp * env;
          alpha = 0.22 + 0.5 * d.r + 0.18 * Math.abs(rp);
        }

        const rr = base + wob;
        const x = cx + Math.cos(ang) * rr;
        const y = cy + Math.sin(ang) * rr;
        ctx.beginPath();
        ctx.arc(x, y, dotR * (0.8 + 0.4 * d.r), 0, TAU);
        ctx.fillStyle = hexA(c, alpha);
        ctx.fill();
      }
    };

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      draw(0);
      return;
    }
    let raf = 0;
    const loop = () => {
      draw(performance.now() / 1000);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [state, size]);

  return <canvas ref={ref} aria-hidden="true" />;
}
