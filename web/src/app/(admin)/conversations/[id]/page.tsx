"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { ConversationDetail, Message } from "@/lib/types";
import { formatDateTime } from "@/lib/format";
import { Badge, ErrorBox, Spinner, statusTone } from "@/components/ui";

const SENDER_LABEL: Record<string, string> = {
  EMPLOYEE: "Xodim",
  USER: "Xodim",
  AI: "AI yordamchi",
  BOT: "AI yordamchi",
  ADMIN: "Operator",
  SYSTEM: "Tizim",
};

function Bubble({ m }: { m: Message }) {
  const type = m.sender_type.toUpperCase();
  const isStaff = type === "EMPLOYEE" || type === "USER";
  const isAi = type === "AI" || type === "BOT";
  const isSystem = type === "SYSTEM";

  if (isSystem) {
    return (
      <div className="my-2 text-center text-xs text-slate-400">
        {m.content_text} · {formatDateTime(m.created_at)}
      </div>
    );
  }

  const style = isStaff
    ? "bg-white border border-slate-200 text-slate-800"
    : isAi
      ? "bg-slate-800 text-slate-50"
      : "bg-brand-700 text-white";

  return (
    <div className={`flex ${isStaff ? "justify-start" : "justify-end"}`}>
      <div className="max-w-[75%]">
        <div className={`mb-1 text-xs text-slate-500 ${isStaff ? "" : "text-right"}`}>
          {SENDER_LABEL[type] ?? m.sender_type} · {formatDateTime(m.created_at)}
        </div>
        <div className={`whitespace-pre-wrap break-words rounded-lg px-3.5 py-2.5 text-sm leading-relaxed ${style}`}>
          {m.content_text || <em className="opacity-70">[{m.content_type}]</em>}
          {m.attachments.length > 0 && (
            <div className="mt-2 space-y-1 border-t border-white/20 pt-2 text-xs opacity-80">
              {m.attachments.map((a) => (
                <div key={a.id}>
                  📎 {a.original_name || a.kind}
                  {a.is_quarantined && " (karantinda)"}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ConversationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [conv, setConv] = useState<ConversationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [toggling, setToggling] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const lastCount = useRef(0);

  const load = useCallback(async () => {
    try {
      const data = await api.conversation(id);
      setConv(data);
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, [id]);

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [load]);

  useEffect(() => {
    const n = conv?.messages.length ?? 0;
    if (n !== lastCount.current) {
      lastCount.current = n;
      endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [conv]);

  async function send(e: React.FormEvent) {
    e.preventDefault();
    const body = text.trim();
    if (!body || sending) return;
    setSending(true);
    setActionError(null);
    try {
      await api.reply(id, body);
      setText("");
      await load();
    } catch (err) {
      setActionError((err as Error).message);
    } finally {
      setSending(false);
    }
  }

  async function toggleAi() {
    if (!conv) return;
    setToggling(true);
    setActionError(null);
    try {
      const updated = await api.setAi(id, !conv.ai_enabled);
      setConv({ ...conv, ...updated });
    } catch (err) {
      setActionError((err as Error).message);
    } finally {
      setToggling(false);
    }
  }

  if (error && !conv) {
    return (
      <div className="space-y-4">
        <Link href="/conversations" className="text-sm text-brand-700 hover:underline">
          ← Suhbatlar
        </Link>
        <ErrorBox message={error} />
      </div>
    );
  }
  if (!conv) return <Spinner />;

  const messages = [...conv.messages].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  );

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col">
      <Link href="/conversations" className="mb-3 text-sm text-brand-700 hover:underline">
        ← Suhbatlar
      </Link>

      <div className="card mb-4 flex flex-wrap items-center justify-between gap-4 px-5 py-4">
        <div className="min-w-0">
          <h1 className="truncate text-lg font-semibold tracking-tight text-slate-900">
            {conv.subject || "Mavzusiz suhbat"}
          </h1>
          <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <Badge tone={statusTone(conv.status)}>{conv.status}</Badge>
            <span>Boshlangan: {formatDateTime(conv.created_at)}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right text-sm">
            <div className="font-medium text-slate-900">
              AI yordamchi: {conv.ai_enabled ? "yoqilgan" : "to'xtatilgan"}
            </div>
            <div className="text-xs text-slate-500">
              {conv.ai_enabled ? "Xodimlarga avtomatik javob beradi" : "Operator javob bermoqda"}
            </div>
          </div>
          <button
            onClick={toggleAi}
            disabled={toggling}
            className={conv.ai_enabled ? "btn-secondary" : "btn-primary"}
          >
            {toggling ? "…" : conv.ai_enabled ? "AI ni to'xtatish" : "AI ni davom ettirish"}
          </button>
        </div>
      </div>

      <div className="card flex min-h-0 flex-1 flex-col overflow-hidden">
        <div className="flex-1 space-y-4 overflow-y-auto bg-slate-50 px-5 py-5">
          {messages.length === 0 ? (
            <div className="py-12 text-center text-sm text-slate-500">Xabarlar yo'q.</div>
          ) : (
            messages.map((m) => <Bubble key={m.id} m={m} />)
          )}
          <div ref={endRef} />
        </div>

        <form onSubmit={send} className="border-t border-slate-200 bg-white p-4">
          {actionError && (
            <div className="mb-3">
              <ErrorBox message={actionError} />
            </div>
          )}
          <div className="flex items-end gap-3">
            <textarea
              rows={2}
              className="input resize-none"
              placeholder="Javob yozing… (Ctrl+Enter — yuborish)"
              value={text}
              maxLength={4000}
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) send(e);
              }}
            />
            <button type="submit" disabled={sending || !text.trim()} className="btn-primary h-10">
              {sending ? "Yuborilmoqda…" : "Yuborish"}
            </button>
          </div>
          {conv.ai_enabled && (
            <p className="mt-2 text-xs text-slate-500">
              Eslatma: operator javob yuborganda AI avtomatik to'xtatiladi.
            </p>
          )}
        </form>
      </div>
    </div>
  );
}
