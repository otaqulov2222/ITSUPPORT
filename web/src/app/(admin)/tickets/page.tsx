"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Ticket } from "@/lib/types";
import { formatDateTime } from "@/lib/format";
import {
  Badge,
  Empty,
  ErrorBox,
  PageHeader,
  Spinner,
  priorityTone,
  statusTone,
} from "@/components/ui";

export default function TicketsPage() {
  const [items, setItems] = useState<Ticket[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .tickets(100)
      .then(setItems)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <>
      <PageHeader title="Tiketlar" subtitle="Filiallardan kelgan texnik va operatsion murojaatlar" />
      {error && <ErrorBox message={error} />}
      {!items && !error && <Spinner />}
      {items && (
        <div className="card overflow-x-auto">
          {items.length === 0 ? (
            <Empty>Hozircha tiketlar yo'q.</Empty>
          ) : (
            <table className="w-full">
              <thead className="border-b border-slate-200 bg-slate-50">
                <tr>
                  <th className="th">Kod</th>
                  <th className="th">Sarlavha</th>
                  <th className="th">Kategoriya</th>
                  <th className="th">Muhimlik</th>
                  <th className="th">Holat</th>
                  <th className="th">Yaratilgan</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50">
                    <td className="td whitespace-nowrap font-mono text-xs font-medium text-slate-900">
                      {t.public_code}
                    </td>
                    <td className="td max-w-sm">
                      <div className="truncate font-medium text-slate-900">{t.title}</div>
                      {t.conversation_id && (
                        <Link
                          href={`/conversations/${t.conversation_id}`}
                          className="text-xs text-brand-700 hover:underline"
                        >
                          Suhbatni ochish
                        </Link>
                      )}
                    </td>
                    <td className="td">
                      <Badge>{t.category}</Badge>
                    </td>
                    <td className="td">
                      <Badge tone={priorityTone(t.priority)}>{t.priority}</Badge>
                    </td>
                    <td className="td">
                      <Badge tone={statusTone(t.status)}>{t.status}</Badge>
                    </td>
                    <td className="td whitespace-nowrap">{formatDateTime(t.created_at)}</td>
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
