/**
 * Streaming client for the AI copilot (`POST /api/v1/chat`).
 *
 * The backend answers with Server-Sent Events; this parses that stream and
 * yields typed events as they arrive so the UI can render tokens live. Like the
 * REST client (`lib/api.ts`), it uses a *relative* base so requests are
 * same-origin and get proxied to the backend by Next rewrites (no CORS).
 */

const BASE = "/api/v1";

export type ChatStreamEvent =
  | { type: "sources"; sources: string[] }
  | { type: "token"; text: string }
  | { type: "done"; sources: string[] }
  | { type: "error"; message: string };

export interface ChatHistoryMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
}

/** Parse one SSE frame ("event: X\ndata: {...}") into a typed event. */
function parseFrame(frame: string): ChatStreamEvent | null {
  const lines = frame.split("\n");
  const dataLine = lines.find((l) => l.startsWith("data:"));
  if (!dataLine) return null;
  try {
    return JSON.parse(dataLine.slice(5).trim()) as ChatStreamEvent;
  } catch {
    return null;
  }
}

/** Stream a grounded answer, yielding sources, then tokens, then done/error. */
export async function* streamChat(params: {
  sessionId: string;
  message: string;
  signal?: AbortSignal;
}): AsyncGenerator<ChatStreamEvent> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({
      session_id: params.sessionId,
      message: params.message,
    }),
    signal: params.signal,
  });

  if (!res.ok || !res.body) {
    let message = `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { error?: { message?: string } };
      if (body?.error?.message) message = body.error.message;
    } catch {
      /* keep default */
    }
    yield { type: "error", message };
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by a blank line.
    let boundary: number;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const event = parseFrame(frame);
      if (event) yield event;
    }
  }
}

/** Load a conversation's persisted turns so a reload restores the chat. */
export async function getChatHistory(
  sessionId: string,
): Promise<ChatHistoryMessage[]> {
  try {
    const res = await fetch(`${BASE}/chat/history/${sessionId}`, {
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return [];
    return (await res.json()) as ChatHistoryMessage[];
  } catch {
    return [];
  }
}
