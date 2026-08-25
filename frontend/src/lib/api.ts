export type Source = {
  chunk_id: string;
  episode_slug: string;
  guest: string | null;
  title: string | null;
  chunk_index: number;
  similarity_score: number;
  youtube_url: string | null;
  evidence: string | null;
};

export type AgentResponse = { session_id: string; answer: string; sources: Source[] };
export type SessionSummary = {
  session_id: string;
  created_at: string;
  updated_at: string;
  provider?: string | null;
  workflow?: string | null;
};
export type SessionMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  sequence: number;
  created_at: string;
};
export type SessionDetail = SessionSummary & { messages: SessionMessage[] };
export type AgentStreamEvent = {
  event: "session" | "workflow" | "token" | "sources" | "validation" | "done" | "error";
  data: Record<string, any>;
};

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/+$/, "");
const NGROK_HEADERS = { "ngrok-skip-browser-warning": "true" };

function apiError(body: any, fallback: string): Error {
  const message = body?.detail?.message ?? body?.detail ?? fallback;
  return new Error(typeof message === "string" ? message : fallback);
}

export async function askAgent(query: string, sessionId?: string): Promise<AgentResponse> {
  const response = await fetch(`${API_BASE}/api/v1/agent/ask`, {
    method: "POST",
    headers: { ...NGROK_HEADERS, "Content-Type": "application/json" },
    body: JSON.stringify({ query, session_id: sessionId || undefined }),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw apiError(body, "The backend is unavailable.");
  return body as AgentResponse;
}

export async function clearSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/agent/sessions/${sessionId}`, {
    method: "DELETE",
    headers: NGROK_HEADERS,
  });
  if (!response.ok && response.status !== 404) {
    throw new Error("Could not delete this conversation.");
  }
}

export async function listSessions(): Promise<SessionSummary[]> {
  const response = await fetch(`${API_BASE}/api/v1/agent/sessions`, { headers: NGROK_HEADERS });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw apiError(body, "Could not load saved conversations.");
  return body as SessionSummary[];
}

export async function getSession(sessionId: string): Promise<SessionDetail> {
  const response = await fetch(`${API_BASE}/api/v1/agent/sessions/${sessionId}`, { headers: NGROK_HEADERS });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw apiError(body, "Could not load this conversation.");
  return body as SessionDetail;
}

export async function* streamAgent(query: string, sessionId?: string): AsyncGenerator<AgentStreamEvent> {
  const response = await fetch(`${API_BASE}/api/v1/agent/ask/stream`, {
    method: "POST",
    headers: { ...NGROK_HEADERS, "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({ query, session_id: sessionId || undefined }),
  });
  if (!response.ok || !response.body) {
    const body = await response.json().catch(() => ({}));
    throw apiError(body, "The streaming connection failed.");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const event = frame.match(/^event:\s*(.+)$/m)?.[1]?.trim() as AgentStreamEvent["event"] | undefined;
      const dataLine = frame.match(/^data:\s*(.+)$/m)?.[1];
      if (!event || !dataLine) continue;
      yield { event, data: JSON.parse(dataLine) };
    }
    if (done) break;
  }
}
