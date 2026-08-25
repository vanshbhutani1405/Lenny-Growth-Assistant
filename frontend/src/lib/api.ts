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

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function askAgent(query: string, sessionId?: string): Promise<AgentResponse> {
  const response = await fetch(`${API_BASE}/api/v1/agent/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, session_id: sessionId || undefined }),
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = body?.detail?.message ?? body?.detail ?? "The backend is unavailable.";
    throw new Error(typeof message === "string" ? message : "The backend is unavailable.");
  }
  return body as AgentResponse;
}

export async function clearSession(sessionId: string): Promise<void> {
  await fetch(`${API_BASE}/api/v1/agent/sessions/${sessionId}`, { method: "DELETE" });
}
