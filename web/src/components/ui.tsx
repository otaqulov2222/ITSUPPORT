import type { ReactNode } from "react";

type Tone = "teal" | "slate" | "amber" | "red" | "green" | "blue";

const tones: Record<Tone, string> = {
  teal: "bg-brand-50 text-brand-800 ring-brand-600/20",
  slate: "bg-slate-100 text-slate-700 ring-slate-500/20",
  amber: "bg-amber-50 text-amber-800 ring-amber-600/25",
  red: "bg-red-50 text-red-700 ring-red-600/20",
  green: "bg-emerald-50 text-emerald-800 ring-emerald-600/20",
  blue: "bg-sky-50 text-sky-800 ring-sky-600/20",
};

export function Badge({ tone = "slate", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${tones[tone]}`}
    >
      {children}
    </span>
  );
}

export function statusTone(status: string): Tone {
  switch (status.toUpperCase()) {
    case "OPEN":
    case "NEW":
      return "blue";
    case "IN_PROGRESS":
    case "ASSIGNED":
    case "WAITING":
      return "amber";
    case "ESCALATED":
      return "red";
    case "RESOLVED":
    case "CLOSED":
      return "green";
    default:
      return "slate";
  }
}

export function priorityTone(priority: string): Tone {
  switch (priority.toUpperCase()) {
    case "CRITICAL":
    case "URGENT":
      return "red";
    case "HIGH":
      return "amber";
    case "LOW":
      return "slate";
    default:
      return "teal";
  }
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex items-end justify-between gap-4">
      <div>
        <h1 className="text-xl font-semibold tracking-tight text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions}
    </div>
  );
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {message}
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="px-4 py-12 text-center text-sm text-slate-500">{children}</div>;
}

export function Spinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-brand-700" />
    </div>
  );
}
