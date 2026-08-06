"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";

import { getChatHistory, streamChat } from "@/lib/aiClient";
import { cn } from "@/lib/utils";

/** A turn as rendered in the panel (assistant turns accrue tokens + sources). */
interface ChatTurn {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  streaming?: boolean;
  error?: boolean;
}

const SESSION_KEY = "ai-session-id";

const SUGGESTIONS = [
  "Why is Liverpool leading?",
  "Compare Arsenal and Chelsea.",
  "Who has the strongest attack?",
  "Summarize this season.",
  "What surprised you this year?",
];

/** Read (or create) the persistent conversation id from localStorage. */
function loadSessionId(): string {
  try {
    const existing = localStorage.getItem(SESSION_KEY);
    if (existing) return existing;
    const id = crypto.randomUUID();
    localStorage.setItem(SESSION_KEY, id);
    return id;
  } catch {
    return crypto.randomUUID();
  }
}

export function ChatPanel() {
  const [open, setOpen] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);

  // Establish the session id and restore any persisted history on mount.
  useEffect(() => {
    const id = loadSessionId();
    setSessionId(id);
    getChatHistory(id).then((history) => {
      if (history.length) {
        setTurns(history.map((m) => ({ role: m.role, content: m.content })));
      }
    });
  }, []);

  // Keep the newest turn in view as tokens stream in.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [turns, open]);

  const send = useCallback(
    async (text: string) => {
      const message = text.trim();
      if (!message || streaming || !sessionId) return;

      setInput("");
      setStreaming(true);
      setTurns((prev) => [
        ...prev,
        { role: "user", content: message },
        { role: "assistant", content: "", sources: [], streaming: true },
      ]);

      // Update the trailing (assistant) turn as events arrive. The functional
      // updater sees the current turn, so tokens can be appended incrementally.
      const updateLast = (fn: (turn: ChatTurn) => ChatTurn) =>
        setTurns((prev) => {
          const next = [...prev];
          next[next.length - 1] = fn(next[next.length - 1]);
          return next;
        });

      try {
        for await (const event of streamChat({ sessionId, message })) {
          if (event.type === "token") {
            updateLast((t) => ({ ...t, content: t.content + event.text }));
          } else if (event.type === "sources" || event.type === "done") {
            updateLast((t) => ({ ...t, sources: event.sources }));
          } else if (event.type === "error") {
            updateLast((t) => ({
              ...t,
              content: (t.content ? t.content + "\n\n" : "") + event.message,
              error: true,
            }));
          }
        }
      } catch {
        updateLast((t) => ({
          ...t,
          content:
            t.content ||
            "Something went wrong reaching the analyst. Please try again.",
          error: true,
        }));
      } finally {
        updateLast((t) => ({ ...t, streaming: false }));
        setStreaming(false);
      }
    },
    [sessionId, streaming],
  );

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void send(input);
  };

  return (
    <>
      {/* Floating launcher */}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close AI analyst" : "Open AI analyst"}
        className="fixed bottom-5 right-5 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-accent text-accent-foreground shadow-lg transition hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-background"
      >
        {open ? <IconClose /> : <IconSparkle />}
      </button>

      {/* Mobile scrim */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
          onClick={() => setOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Panel — right sidebar on desktop, bottom drawer on mobile */}
      <aside
        className={cn(
          "fixed z-50 flex flex-col border-border bg-surface shadow-2xl transition-transform duration-300",
          // Mobile: bottom drawer
          "inset-x-0 bottom-0 h-[85vh] rounded-t-2xl border-t",
          // Desktop: right sidebar
          "lg:inset-y-0 lg:left-auto lg:right-0 lg:h-full lg:w-[400px] lg:rounded-none lg:border-l lg:border-t-0",
          open
            ? "translate-y-0 lg:translate-x-0"
            : "translate-y-full lg:translate-y-0 lg:translate-x-full",
        )}
        aria-hidden={!open}
      >
        <header className="flex items-center justify-between border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent/15 text-accent">
              <IconSparkle />
            </span>
            <div>
              <p className="text-sm font-semibold leading-tight">
                Football Analyst
              </p>
              <p className="text-xs text-muted">Grounded in the data · never invents stats</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Close"
            className="rounded-md p-1.5 text-muted hover:bg-border/50 hover:text-foreground"
          >
            <IconClose />
          </button>
        </header>

        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
          {turns.length === 0 ? (
            <Welcome onPick={(s) => void send(s)} disabled={streaming} />
          ) : (
            turns.map((turn, i) => <Bubble key={i} turn={turn} />)
          )}
        </div>

        <form
          onSubmit={onSubmit}
          className="border-t border-border p-3"
        >
          <div className="flex items-end gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void send(input);
                }
              }}
              rows={1}
              placeholder="Ask about standings, form, or a team…"
              disabled={streaming}
              className="max-h-32 flex-1 resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-accent disabled:opacity-60"
            />
            <button
              type="submit"
              disabled={streaming || !input.trim()}
              aria-label="Send"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-foreground transition hover:brightness-110 disabled:opacity-40"
            >
              <IconSend />
            </button>
          </div>
        </form>
      </aside>
    </>
  );
}

function Welcome({
  onPick,
  disabled,
}: {
  onPick: (s: string) => void;
  disabled: boolean;
}) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted">
        I answer only from the data in this platform — standings, team stats, and
        results — and cite the source for every answer. Try one:
      </p>
      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            disabled={disabled}
            onClick={() => onPick(s)}
            className="rounded-full border border-border bg-background px-3 py-1.5 text-xs text-foreground transition hover:border-accent hover:text-accent disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

function Bubble({ turn }: { turn: ChatTurn }) {
  const isUser = turn.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm",
          isUser
            ? "bg-accent text-accent-foreground"
            : turn.error
              ? "bg-red-500/10 text-red-600 dark:text-red-400"
              : "bg-background border border-border text-foreground",
        )}
      >
        <p className="whitespace-pre-wrap break-words leading-relaxed">
          {turn.content}
          {turn.streaming && !turn.content && (
            <span className="text-muted">Thinking…</span>
          )}
        </p>
        {!isUser && turn.sources && turn.sources.length > 0 && (
          <div className="mt-2 border-t border-border pt-2">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">
              Source
            </p>
            <ul className="mt-1 space-y-0.5">
              {turn.sources.map((s) => (
                <li key={s} className="text-[11px] text-muted">
                  • {s}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

// --- icons (inline, no dependency) ---
function IconSparkle() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5" aria-hidden="true">
      <path d="M12 2l1.9 5.1L19 9l-5.1 1.9L12 16l-1.9-5.1L5 9l5.1-1.9L12 2zM19 14l.9 2.4L22 17l-2.1.6L19 20l-.9-2.4L16 17l2.1-.6L19 14z" />
    </svg>
  );
}
function IconClose() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-5 w-5" aria-hidden="true">
      <path d="M18 6 6 18M6 6l12 12" strokeLinecap="round" />
    </svg>
  );
}
function IconSend() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4" aria-hidden="true">
      <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
