export interface User {
  id: number;
  username: string;
  email: string;
  display_name: string | null;
  bio: string | null;
  avatar_url: string | null;
  region: string;
  email_verified: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  user: User;
}

export interface FilmSummary {
  tmdb_id: number;
  title: string;
  release_date: string | null;
  overview: string | null;
  poster_path: string | null;
  vote_average: number | null;
}

export interface RankedFilm extends FilmSummary {
  rank: number;
}

export interface Credit {
  person_id: number;
  name: string;
  credit_type: "cast" | "crew";
  job: string | null;
  character: string | null;
}

export interface Provider {
  provider_id: number;
  provider_name: string;
  logo_path: string | null;
  offer_type: "flatrate" | "rent" | "buy";
}

export interface NamedRef {
  id: number;
  name: string;
}

export interface FilmDetail {
  tmdb_id: number;
  media_type: string;
  title: string;
  original_title: string | null;
  overview: string | null;
  release_date: string | null;
  runtime: number | null;
  poster_path: string | null;
  backdrop_path: string | null;
  vote_average: number | null;
  vote_count: number | null;
  region: string;
  genres: NamedRef[];
  keywords: NamedRef[];
  cast: Credit[];
  crew: Credit[];
  watch_providers: Provider[];
}

export interface FilmMeState {
  rating: number | null;
  watchlisted: boolean;
  watched: boolean;
}

export interface DiaryEntry {
  id: number;
  film_tmdb_id: number;
  film_title: string;
  poster_path: string | null;
  watched_on: string;
  rating_value: number | null;
  liked: boolean;
  rewatch: boolean;
  note: string | null;
  created_at: string;
}

export interface ReviewAuthor {
  id: number;
  username: string;
  display_name: string | null;
}

export interface Review {
  id: number;
  film_tmdb_id: number;
  author: ReviewAuthor;
  body: string;
  contains_spoilers: boolean;
  created_at: string;
  like_count: number;
  liked: boolean;
}

// ---- social
export interface UserCard {
  id: number;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  bio: string | null;
}

export interface ProfileStats {
  films_logged: number;
  reviews: number;
  followers: number;
  following: number;
}

export interface Profile {
  id: number;
  username: string;
  display_name: string | null;
  bio: string | null;
  avatar_url: string | null;
  created_at: string;
  stats: ProfileStats;
  is_following: boolean;
  is_self: boolean;
}

export interface FeedFilm {
  tmdb_id: number;
  title: string;
  poster_path: string | null;
}

export interface FeedItem {
  id: number;
  actor: UserCard;
  type: string;
  value: number | null;
  film: FeedFilm;
  created_at: string;
}

export interface RecommendedFilm extends FilmSummary {
  reason: string;
}

// ---- stats
export interface RatingBucket {
  value: number;
  count: number;
}
export interface GenreCount {
  name: string;
  count: number;
}
export interface MonthCount {
  month: number;
  count: number;
}
export interface TopFilm {
  tmdb_id: number;
  title: string;
  poster_path: string | null;
  rating: number | null;
}
export interface YearStats {
  year: number;
  entries: number;
  distinct_films: number;
  hours: number;
  by_month: MonthCount[];
  top_genres: GenreCount[];
  top_films: TopFilm[];
}
export interface LifetimeStats {
  films_logged: number;
  entries: number;
  ratings: number;
  reviews: number;
  lists: number;
  average_rating: number | null;
  rating_distribution: RatingBucket[];
}
export interface Stats {
  lifetime: LifetimeStats;
  year: YearStats;
  available_years: number[];
}

// ---- import
export interface ImportResult {
  kind: string;
  rows: number;
  imported: number;
  skipped: number;
  unmatched: string[];
}

// ---- notifications
export interface Notification {
  id: number;
  type: "follow" | "review_like" | "list_like" | string;
  actor: UserCard | null;
  read: boolean;
  data: {
    review_id?: number;
    film_tmdb_id?: number;
    film_title?: string;
    list_id?: number;
    list_title?: string;
  } | null;
  created_at: string;
}

// ---- lists
export interface ListFilm {
  tmdb_id: number;
  title: string;
  release_date: string | null;
  poster_path: string | null;
  vote_average: number | null;
}

export interface ListItem {
  film: ListFilm;
  rank: number | null;
  note: string | null;
}

export interface ListSummary {
  id: number;
  title: string;
  description: string | null;
  is_ranked: boolean;
  is_public: boolean;
  is_system: boolean;
  item_count: number;
  owner: UserCard | null;
  created_at: string;
  preview_posters: string[];
  like_count: number;
  liked: boolean;
}

export interface ListDetail extends ListSummary {
  items: ListItem[];
  is_owner: boolean;
}
