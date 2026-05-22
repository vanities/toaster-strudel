import { useCallback, useEffect, useRef, useState } from 'react';

// React port of the vanilla chat client. Same /api/chat SSE protocol; the
// assistant message is modeled as ordered blocks (text | tool) so markdown
// text and tool-call chips render in the order they streamed.

const newId = () => Math.random().toString(36).slice(2);

export interface TextBlock {
  type: 'text';
  text: string;
}
export interface ToolBlock {
  type: 'tool';
  id?: string;
  toolName: string;
  group: 'read' | 'write' | 'remove' | 'other';
  input: unknown;
  result?: unknown;
  ok?: boolean;
  done: boolean;
}
export type Block = TextBlock | ToolBlock;

export interface UserMessage {
  id: string;
  role: 'user';
  content: string;
}
export interface AssistantMessage {
  id: string;
  role: 'assistant';
  blocks: Block[];
  error?: string;
}
export type ChatMessage = UserMessage | AssistantMessage;

export interface AuthStatus {
  hasAuthToken: boolean;
  hasApiKey: boolean;
  authSource: string | null;
  apiKeySource: string | null;
  hint: string | null;
  model: string | null;
  binaryFound: boolean;
}

interface WireEvent {
  type: string;
  text?: string;
  id?: string;
  toolName?: string;
  group?: ToolBlock['group'];
  input?: unknown;
  toolUseId?: string;
  result?: unknown;
  isError?: boolean;
  sessionId?: string;
  message?: string;
  error?: unknown;
}

function appendText(m: AssistantMessage, t: string): AssistantMessage {
  const blocks = [...m.blocks];
  const last = blocks[blocks.length - 1];
  if (last && last.type === 'text') {
    blocks[blocks.length - 1] = { type: 'text', text: last.text + t };
  } else {
    blocks.push({ type: 'text', text: t });
  }
  return { ...m, blocks };
}

function toApi(m: ChatMessage): { role: 'user' | 'assistant'; content: string } {
  if (m.role === 'user') return { role: 'user', content: m.content };
  const text = m.blocks
    .filter((b): b is TextBlock => b.type === 'text')
    .map((b) => b.text)
    .join('');
  return { role: 'assistant', content: text };
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [pending, setPending] = useState(false);
  const [auth, setAuth] = useState<AuthStatus | null>(null);
  const resumeRef = useRef<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const refreshAuth = useCallback(async () => {
    try {
      setAuth((await (await fetch('/api/chat/auth')).json()) as AuthStatus);
    } catch {
      setAuth(null);
    }
  }, []);

  useEffect(() => {
    refreshAuth();
  }, [refreshAuth]);

  const saveToken = useCallback(
    async (token: string) => {
      if (!token.trim()) return;
      await fetch('/api/chat/auth', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ authToken: token.trim() }),
      });
      await refreshAuth();
    },
    [refreshAuth]
  );

  const stop = useCallback(() => abortRef.current?.abort(), []);

  const resetSession = useCallback(() => {
    abortRef.current?.abort();
    resumeRef.current = null;
    setMessages([]);
  }, []);

  const send = useCallback(
    async (text: string, viewingTrack?: string | null) => {
      if (pending || !text.trim()) return;

      const userMsg: UserMessage = { id: newId(), role: 'user', content: text };
      const assistantId = newId();
      const assistantMsg: AssistantMessage = { id: assistantId, role: 'assistant', blocks: [] };

      let apiMessages: { role: 'user' | 'assistant'; content: string }[] = [];
      setMessages((prev) => {
        apiMessages = [...prev.map(toApi), { role: 'user', content: text }];
        return [...prev, userMsg, assistantMsg];
      });
      setPending(true);

      const updateAssistant = (fn: (m: AssistantMessage) => AssistantMessage) =>
        setMessages((prev) =>
          prev.map((m) => (m.id === assistantId ? fn(m as AssistantMessage) : m))
        );

      const ac = new AbortController();
      abortRef.current = ac;

      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          signal: ac.signal,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: apiMessages,
            ...(resumeRef.current ? { resumeSessionId: resumeRef.current } : {}),
            context: { viewingTrack: viewingTrack || undefined },
          }),
        });
        if (!res.ok || !res.body) {
          let msg = `request failed (${res.status})`;
          try {
            const j = (await res.json()) as { error?: string };
            if (j?.error) msg = j.error;
          } catch {
            /* non-JSON error body */
          }
          updateAssistant((m) => ({ ...m, error: msg }));
          return;
        }
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        for (;;) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          let idx: number;
          while ((idx = buffer.indexOf('\n\n')) !== -1) {
            const chunk = buffer.slice(0, idx);
            buffer = buffer.slice(idx + 2);
            const payload = chunk
              .split('\n')
              .filter((l) => l.startsWith('data:'))
              .map((l) => l.slice(5).trimStart())
              .join('\n');
            if (!payload) continue;
            let ev: WireEvent;
            try {
              ev = JSON.parse(payload) as WireEvent;
            } catch {
              continue;
            }
            switch (ev.type) {
              case 'session':
                if (ev.sessionId) resumeRef.current = ev.sessionId;
                break;
              case 'text':
                if (typeof ev.text === 'string') {
                  const t = ev.text;
                  updateAssistant((m) => appendText(m, t));
                }
                break;
              case 'tool_call':
                updateAssistant((m) => ({
                  ...m,
                  blocks: [
                    ...m.blocks,
                    {
                      type: 'tool',
                      id: ev.id,
                      toolName: ev.toolName ?? 'tool',
                      group: ev.group ?? 'other',
                      input: ev.input,
                      done: false,
                    },
                  ],
                }));
                break;
              case 'tool_result':
                updateAssistant((m) => ({
                  ...m,
                  blocks: m.blocks.map((b) =>
                    b.type === 'tool' && b.id === ev.toolUseId
                      ? { ...b, result: ev.result, ok: !ev.isError, done: true }
                      : b
                  ),
                }));
                break;
              case 'assistant_error':
                updateAssistant((m) => ({
                  ...m,
                  error: typeof ev.error === 'string' ? ev.error : JSON.stringify(ev.error),
                }));
                break;
              case 'error':
                updateAssistant((m) => ({ ...m, error: ev.message ?? 'stream error' }));
                break;
            }
          }
        }
      } catch (err) {
        const msg =
          err instanceof Error
            ? err.name === 'AbortError'
              ? 'stopped'
              : err.message
            : 'request failed';
        updateAssistant((m) => ({ ...m, error: msg }));
      } finally {
        setPending(false);
        abortRef.current = null;
      }
    },
    [pending]
  );

  return { messages, pending, auth, send, stop, saveToken, refreshAuth, resetSession };
}
