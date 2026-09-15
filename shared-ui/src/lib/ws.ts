export type ServerEvent = { type: string; [key: string]: unknown };

export type ConnStatus = "connecting" | "connected" | "disconnected";

export type WsClient = {
  close: () => void;
  send: (data: unknown) => void;
};

export function connectWs(
  onEvent: (event: ServerEvent) => void,
  onStatus: (status: ConnStatus) => void,
): WsClient {
  let closed = false;
  let retryMs = 1000;
  let sock: WebSocket | null = null;

  const open = () => {
    if (closed) return;
    onStatus("connecting");
    const proto = location.protocol === "https:" ? "wss" : "ws";
    sock = new WebSocket(`${proto}://${location.host}/ws`);
    sock.onopen = () => {
      retryMs = 1000;
      onStatus("connected");
    };
    sock.onmessage = (msg) => {
      try {
        onEvent(JSON.parse(msg.data) as ServerEvent);
      } catch {
        onEvent({ type: "unparseable", raw: String(msg.data) });
      }
    };
    sock.onclose = () => {
      if (closed) return;
      onStatus("disconnected");
      setTimeout(open, retryMs);
      retryMs = Math.min(retryMs * 2, 15000);
    };
  };

  open();
  return {
    close: () => {
      closed = true;
      sock?.close();
    },
    send: (data: unknown) => {
      if (sock && sock.readyState === WebSocket.OPEN) sock.send(JSON.stringify(data));
    },
  };
}
