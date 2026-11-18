import type {
  Conversation,
  ConversationDetail,
  Me,
  Message,
  Ticket,
  TokenResponse,
} from "./types";

export const API_URL = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"
).replace(/\/$/, "");

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

export const tokenStore = {
  get access(): string | null {
    return typeof window === "undefined" ? null : localStorage.getItem(ACCESS_KEY);
  },
  get refresh(): string | null {
    return typeof window === "undefined" ? null : localStorage.getItem(REFRESH_KEY);
  },
  set(tokens: { access_token: string; refresh_token?: string }) {
    localStorage.setItem(ACCESS_KEY, tokens.access_token);
    if (tokens.refresh_token) localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function extractDetail(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const d = (body as { detail: unknown }).detail;
    if (typeof d === "string") return d;
    if (Array.isArray(d)) {
      return d
        .map((e) => (e && typeof e === "object" && "msg" in e ? String((e as { msg: unknown }).msg) : ""))
        .filter(Boolean)
        .join("; ") || fallback;
    }
  }
  return fallback;
}

let refreshing: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const refresh = tokenStore.refresh;
  if (!refresh) return false;
  if (!refreshing) {
    refreshing = (async () => {
      try {
        const res = await fetch(`${API_URL}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refresh }),
        });
        if (!res.ok) return false;
        tokenStore.set((await res.json()) as TokenResponse);
        return true;
      } catch {
        return false;
      } finally {
        setTimeout(() => (refreshing = null), 0);
      }
    })();
  }
  return refreshing;
}

async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  const token = tokenStore.access;
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "Server bilan aloqa yo'q. Backend ishlayotganini tekshiring.");
  }

  if (res.status === 401 && retry && path !== "/auth/login") {
    if (await tryRefresh()) return request<T>(path, init, false);
    tokenStore.clear();
    if (typeof window !== "undefined" && window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  }

  if (!res.ok) {
    let body: unknown = null;
    try {
      body = await res.json();
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, extractDetail(body, `So'rov xatosi (${res.status})`));
  }
  return (await res.json()) as T;
}

export const api = {
  login: (email: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<Me>("/auth/me"),
  conversations: (limit = 100) => request<Conversation[]>(`/conversations?limit=${limit}`),
  conversation: (id: string) => request<ConversationDetail>(`/conversations/${id}`),
  reply: (id: string, text: string) =>
    request<Message>(`/conversations/${id}/reply`, {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  setAi: (id: string, ai_enabled: boolean) =>
    request<Conversation>(`/conversations/${id}/ai`, {
      method: "POST",
      body: JSON.stringify({ ai_enabled }),
    }),
  tickets: (limit = 100) => request<Ticket[]>(`/tickets?limit=${limit}`),
};
