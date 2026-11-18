"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Conversation, Ticket } from "@/lib/types";
import { useAuth } from "@/lib/auth";
import { timeAgo } from "@/lib/format";
import { Badge, Empty, ErrorBox, PageHeader, Spinner, statusTone } from "@/components/ui";

const CLOSED_TICKET = ["RESOLVED", "CLOSED", "CANCELLED"];

function Stat({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: string | number;
  hint: string;
  accent?: boolean;
}) {
  return (
    <div className="card p-5">
      <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">{label}</div>
      <div
        className={`mt-2 text-3xl font-semibold tabular-nums tracking-tight ${
          accent ? "text-brand-700" : "text-slate-900"
        }`}
      >
        {value}
      </div>
      <div className="mt-1 text-sm text-slate-500">{hint}</div>
    </div>
  );
}

export default function DashboardPage() {
  const { me } = useAuth();
  const [convs, setConvs] = useState<Conversation[] | null>(null);
  const [tickets, setTickets] = useState<Ticket[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.conversations(200), api.tickets(200)])
      .then(([c, t]) => {
        setConvs(c);
        setTickets(t);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <ErrorBox message={error} />;
  if (!convs || !tickets) return <Spinner />;

  const open = convs.filter((c) => c.status.toUpperCase() === "OPEN");
  const aiOn = convs.filter((c) => c.ai_enabled).length;
  const aiOff = convs.length - aiOn;
  const openTickets = tickets.filter((t) => !CLOSED_TICKET.includes(t.status.toUpperCase()));
  const recent = [...convs]
    .sort(
      (a, b) =>
        new Date(b.last_message_at ?? b.created_at).getTime() -
        new Date(a.last_message_at ?? a.created_at).getTime(),
    )
    .slice(0, 6);

  return (
    <>
      <PageHeader
        title={`Xush kelibsiz, ${me?.full_name ?? ""}`}
        subtitle="Filiallardagi murojaatlar holati — umumiy ko'rinish"
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="Ochiq suhbatlar"
          value={open.length}
          hint={`Jami ${convs.length} ta suhbatdan`}
          accent
        />
        <Stat
          label="Tiketlar"
          value={tickets.length}
          hint={`${openTickets.length} tasi hal qilinmagan`}
        />
        <Stat label="AI yoqilgan" value={aiOn} hint="Avtomatik javob beriladigan suhbatlar" />
        <Stat label="AI to'xtatilgan" value={aiOff} hint="Operator boshqarmoqda" />
      </div>

      <div className="mt-4 rounded-lg border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-900">
        {aiOff === 0
          ? "Barcha suhbatlarda AI yordamchi faol."
          : `${aiOff} ta suhbatda AI to'xtatilgan — javoblar operator tomonidan beriladi. Operator javob yozganda AI avtomatik to'xtaydi.`}
      </div>

      <div className="card mt-8 overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3">
          <h2 className="text-sm font-semibold text-slate-900">So'nggi suhbatlar</h2>
          <Link href="/conversations" className="text-sm font-medium text-brand-700 hover:underline">
            Barchasi →
          </Link>
        </div>
        {recent.length === 0 ? (
          <Empty>Hozircha suhbatlar yo'q.</Empty>
        ) : (
          <ul className="divide-y divide-slate-100">
            {recent.map((c) => (
              <li key={c.id}>
                <Link
                  href={`/conversations/${c.id}`}
                  className="flex items-center justify-between gap-4 px-5 py-3 hover:bg-slate-50"
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-slate-900">
                      {c.subject || "Mavzusiz suhbat"}
                    </div>
                    <div className="text-xs text-slate-500">{timeAgo(c.last_message_at ?? c.created_at)}</div>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <Badge tone={c.ai_enabled ? "teal" : "amber"}>
                      AI {c.ai_enabled ? "yoqilgan" : "o'chiq"}
                    </Badge>
                    <Badge tone={statusTone(c.status)}>{c.status}</Badge>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </>
  );
}
