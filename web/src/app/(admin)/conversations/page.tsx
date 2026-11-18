"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Conversation } from "@/lib/types";
import { formatDateTime, shortId, timeAgo } from "@/lib/format";
import { Badge, Empty, ErrorBox, PageHeader, Spinner, statusTone } from "@/components/ui";

export default function ConversationsPage() {
  const [items, setItems] = useState<Conversation[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = () =>
      api
        .conversations(100)
        .then((c) => {
          setItems(c);
          setError(null);
        })
        .catch((e: Error) => setError(e.message));
    load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, []);

  return (
    <>
      <PageHeader title="Suhbatlar" subtitle="Dorixona xodimlari bilan Telegram orqali yozishmalar" />
      {error && <ErrorBox message={error} />}
      {!items && !error && <Spinner />}
      {items && (
        <div className="card overflow-hidden">
          {items.length === 0 ? (
            <Empty>Hozircha suhbatlar yo'q.</Empty>
          ) : (
            <table className="w-full">
              <thead className="border-b border-slate-200 bg-slate-50">
                <tr>
                  <th className="th">Mavzu</th>
                  <th className="th">Xodim</th>
                  <th className="th">Holat</th>
                  <th className="th">AI</th>
                  <th className="th">Oxirgi xabar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50">
                    <td className="td">
                      <Link
                        href={`/conversations/${c.id}`}
                        className="font-medium text-slate-900 hover:text-brand-700"
                      >
                        {c.subject || "Mavzusiz suhbat"}
                      </Link>
                    </td>
                    <td className="td font-mono text-xs text-slate-500">{shortId(c.employee_id)}</td>
                    <td className="td">
                      <Badge tone={statusTone(c.status)}>{c.status}</Badge>
                    </td>
                    <td className="td">
                      <Badge tone={c.ai_enabled ? "teal" : "amber"}>{c.ai_enabled ? "Yoqilgan" : "To'xtatilgan"}</Badge>
                    </td>
                    <td className="td whitespace-nowrap" title={formatDateTime(c.last_message_at)}>
                      {timeAgo(c.last_message_at ?? c.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </>
  );
}
