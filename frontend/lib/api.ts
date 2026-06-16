import type {
  DiaryEntry,
  FeedItem,
  FilmDetail,
  FilmMeState,
  FilmSummary,
  ImportResult,
  ListDetail,
  ListItem,
  ListSummary,
  Notification,
  Profile,
  Provider,
  RankedFilm,
  RecommendedFilm,
  Review,
  Stats,
  Token,
  User,
  UserCard,
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
  // Don't set a JSON content-type for FormData — the browser must supply the
  // multipart boundary itself.
  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
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

  updateProfile: (body: {
    display_name?: string | null;
    bio?: string | null;
    avatar_url?: string | null;
    region?: string;
  }) => request<User>("/auth/me", { method: "PATCH", body: JSON.stringify(body) }),

  // ---- discover
  trending: (window: "day" | "week" = "week") =>
    request<FilmSummary[]>(`/discover/trending?window=${window}`),

  top500: (limit = 100, offset = 0) =>
    request<RankedFilm[]>(`/discover/top500?limit=${limit}&offset=${offset}`),

  recommendations: (limit = 20) =>
    request<RecommendedFilm[]>(`/discover/recommendations?limit=${limit}`),

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

  likeReview: (reviewId: number) =>
    request<{ liked: boolean; like_count: number }>(
      `/reviews/${reviewId}/like`,
      { method: "POST" },
    ),

  unlikeReview: (reviewId: number) =>
    request<{ liked: boolean; like_count: number }>(
      `/reviews/${reviewId}/like`,
      { method: "DELETE" },
    ),

  // ---- social
  searchUsers: (q: string) =>
    request<UserCard[]>(`/users/search?q=${encodeURIComponent(q)}`),

  profile: (username: string) => request<Profile>(`/users/${username}`),

  userActivity: (username: string, limit = 30, offset = 0) =>
    request<FeedItem[]>(
      `/users/${username}/activity?limit=${limit}&offset=${offset}`,
    ),

  followers: (username: string, limit = 50, offset = 0) =>
    request<UserCard[]>(
      `/users/${username}/followers?limit=${limit}&offset=${offset}`,
    ),

  following: (username: string, limit = 50, offset = 0) =>
    request<UserCard[]>(
      `/users/${username}/following?limit=${limit}&offset=${offset}`,
    ),

  follow: (username: string) =>
    request<{ following: boolean }>(`/users/${username}/follow`, {
      method: "POST",
    }),

  unfollow: (username: string) =>
    request(`/users/${username}/follow`, { method: "DELETE" }),

  myFeed: (limit = 30, offset = 0) =>
    request<FeedItem[]>(`/me/feed?limit=${limit}&offset=${offset}`),

  stats: (year?: number) =>
    request<Stats>(`/me/stats${year ? `?year=${year}` : ""}`),

  // ---- import
  importLetterboxd: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<ImportResult>("/me/import/letterboxd", {
      method: "POST",
      body: form,
    });
  },

  // ---- notifications
  notifications: (limit = 30, offset = 0) =>
    request<Notification[]>(
      `/me/notifications?limit=${limit}&offset=${offset}`,
    ),

  unreadCount: () =>
    request<{ unread: number }>("/me/notifications/unread_count"),

  markNotificationsRead: () =>
    request("/me/notifications/read", { method: "POST" }),

  markNotificationRead: (id: number) =>
    request<Notification>(`/me/notifications/${id}/read`, { method: "POST" }),

  // ---- lists
  myLists: () => request<ListSummary[]>("/me/lists"),

  userLists: (username: string) =>
    request<ListSummary[]>(`/users/${username}/lists`),

  list: (listId: number) => request<ListDetail>(`/lists/${listId}`),

  createList: (body: {
    title: string;
    description?: string | null;
    is_ranked?: boolean;
    is_public?: boolean;
  }) => request<ListDetail>("/lists", { method: "POST", body: JSON.stringify(body) }),

  updateList: (
    listId: number,
    body: {
      title?: string;
      description?: string | null;
      is_ranked?: boolean;
      is_public?: boolean;
    },
  ) =>
    request<ListDetail>(`/lists/${listId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  deleteList: (listId: number) =>
    request(`/lists/${listId}`, { method: "DELETE" }),

  addListItem: (listId: number, tmdbId: number, note?: string | null) =>
    request<ListItem>(`/lists/${listId}/items`, {
      method: "POST",
      body: JSON.stringify({ tmdb_id: tmdbId, note: note ?? null }),
    }),

  removeListItem: (listId: number, tmdbId: number) =>
    request(`/lists/${listId}/items/${tmdbId}`, { method: "DELETE" }),

  reorderList: (listId: number, tmdbIds: number[]) =>
    request<ListDetail>(`/lists/${listId}/order`, {
      method: "PUT",
      body: JSON.stringify({ tmdb_ids: tmdbIds }),
    }),

  likeList: (listId: number) =>
    request<{ liked: boolean; like_count: number }>(`/lists/${listId}/like`, {
      method: "POST",
    }),

  unlikeList: (listId: number) =>
    request<{ liked: boolean; like_count: number }>(`/lists/${listId}/like`, {
      method: "DELETE",
    }),
};

// ---- TMDB images
const IMG_BASE = "https://image.tmdb.org/t/p";
export function posterUrl(path: string | null, size = "w342"): string | null {
  return path ? `${IMG_BASE}/${size}${path}` : null;
}
export function logoUrl(path: string | null, size = "w92"): string | null {
  return path ? `${IMG_BASE}/${size}${path}` : null;
}
