import { useEffect, useRef, useState } from "react";
import { StatusOrb, type OrbState } from "./components/StatusOrb";
import { connectWs, type ConnStatus, type ServerEvent } from "./lib/ws";

const STATE_COLORS: Record<OrbState, string> = {
  idle: "var(--idle)",
  listening: "var(--listening)",
  thinking: "var(--thinking)",
  speaking: "var(--speaking)",
};

const HINTS: Record<OrbState, string> = {
  idle: "wake word armed · mic is local-only",
  listening: "streaming · realtime",
  thinking: "working on it",
  speaking: "playing response",
};

export default function App() {
  const [orbState, setOrbState] = useState<OrbState>("idle");
  const [status, setStatus] = useState<ConnStatus>("connecting");
  const [events, setEvents] = useState<string[]>([]);
  const clientRef = useRef<ReturnType<typeof connectWs> | null>(null);
  const idleTimer = useRef<number | null>(null);

  useEffect(() => {
    const client = connectWs(
      (event: ServerEvent) => {
        setEvents((prev) => [`${new Date().toLocaleTimeString()}  ${JSON.stringify(event)}`, ...prev].slice(0, 50));
        if (event.type === "wake") {
          setOrbState("listening");
          if (idleTimer.current) window.clearTimeout(idleTimer.current);
          idleTimer.current = window.setTimeout(() => setOrbState("idle"), 4000);
        }
      },
      setStatus,
    );
    clientRef.current = client;
    return client.close;
  }, []);

  const ping = () => clientRef.current?.send({ hello: "from ui", at: Date.now() });

  return (
    <div className="shell">
      <header className="topbar">
        <span className="conn">
          <span className="dot" data-status={status} />
          {status} · desktop
        </span>
        <span className="mono dim">M1 skeleton · no voice yet</span>
      </header>

      <main className="stage">
        <StatusOrb state={orbState} size={280} />
        <p className="status-label" style={{ color: STATE_COLORS[orbState] }} aria-live="polite">
          {orbState === "idle" ? "Say “Hey Aria”" : `${orbState[0].toUpperCase()}${orbState.slice(1)}…`}
        </p>
        <p className="status-hint mono">{HINTS[orbState]}</p>

        <div className="dev-row">
          {(Object.keys(STATE_COLORS) as OrbState[]).map((s) => (
            <button
              key={s}
              className="chip"
              aria-pressed={s === orbState}
              onClick={() => setOrbState(s)}
            >
              {s}
            </button>
          ))}
          <button className="chip ghost" onClick={ping}>
            send ping
          </button>
        </div>
      </main>

      <section className="log" aria-label="WebSocket events">
        {events.length === 0 ? (
          <p className="mono dim">no events yet — start the backend and they appear here</p>
        ) : (
          events.map((line, i) => (
            <p key={i} className="mono log-line">
              {line}
            </p>
          ))
        )}
      </section>
    </div>
  );
}
