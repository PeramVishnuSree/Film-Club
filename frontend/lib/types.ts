export interface User {
  id: number;
  username: string;
  email: string;
  display_name: string | null;
  bio: string | null;
  avatar_url: string | null;
  region: string;
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
}
