import type {
  DiaryEntry,
  FilmDetail,
  FilmMeState,
  FilmSummary,
  Provider,
  RankedFilm,
  Review,
  Token,
  User,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "filmclub_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      if (data?.detail) {
        detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

// ---- auth
export const api = {
  signup: (body: {
    username: string;
    email: string;
    password: string;
    display_name?: string;
  }) => request<Token>("/auth/signup", { method: "POST", body: JSON.stringify(body) }),

  login: (identifier: string, password: string) =>
    request<Token>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ identifier, password }),
    }),

  me: () => request<User>("/auth/me"),

  // ---- discover
  trending: (window: "day" | "week" = "week") =>
    request<FilmSummary[]>(`/discover/trending?window=${window}`),

  top500: (limit = 100, offset = 0) =>
    request<RankedFilm[]>(`/discover/top500?limit=${limit}&offset=${offset}`),

  // ---- films
  search: (q: string) =>
    request<FilmSummary[]>(`/films/search?q=${encodeURIComponent(q)}`),

  film: (tmdbId: number) => request<FilmDetail>(`/films/${tmdbId}`),

  filmState: (tmdbId: number) => request<FilmMeState>(`/films/${tmdbId}/me`),

  filmProviders: (tmdbId: number, region = "US") =>
    request<Provider[]>(`/films/${tmdbId}/providers?region=${region}`),

  // ---- library
  setRating: (tmdbId: number, value: number) =>
    request(`/films/${tmdbId}/rating`, {
      method: "PUT",
      body: JSON.stringify({ value }),
    }),

  deleteRating: (tmdbId: number) =>
    request(`/films/${tmdbId}/rating`, { method: "DELETE" }),

  addWatchlist: (tmdbId: number) =>
    request(`/films/${tmdbId}/watchlist`, { method: "POST" }),

  removeWatchlist: (tmdbId: number) =>
    request(`/films/${tmdbId}/watchlist`, { method: "DELETE" }),

  addDiary: (
    tmdbId: number,
    body: {
      watched_on: string;
      rating_value?: number | null;
      liked?: boolean;
      rewatch?: boolean;
      note?: string | null;
    },
  ) =>
    request<DiaryEntry>(`/films/${tmdbId}/diary`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  myDiary: () => request<DiaryEntry[]>("/me/diary"),

  myWatchlist: () => request<FilmSummary[]>("/me/watchlist"),

  addReview: (
    tmdbId: number,
    body: { body: string; contains_spoilers?: boolean },
  ) =>
    request<Review>(`/films/${tmdbId}/reviews`, {
      method: "POST",
      body: JSON.stringify(body),
    }),

  reviews: (tmdbId: number) => request<Review[]>(`/films/${tmdbId}/reviews`),
};

// ---- TMDB images
const IMG_BASE = "https://image.tmdb.org/t/p";
export function posterUrl(path: string | null, size = "w342"): string | null {
  return path ? `${IMG_BASE}/${size}${path}` : null;
}
export function logoUrl(path: string | null, size = "w92"): string | null {
  return path ? `${IMG_BASE}/${size}${path}` : null;
}
