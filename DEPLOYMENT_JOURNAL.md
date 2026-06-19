# Film Club — Deployment Journal

A plain-language record of how Film Club went from "runs on my laptop" to a
live, free-to-run product on the public internet. Written so a non-technical
reader can follow the story and a technical reader can reuse the decisions.

---

## 1. What we were trying to do

Film Club is a small web app: browse trending movies, search films, sign up,
and rate what you've watched. Before this work it ran only on a developer
machine. The goal was simple to state and fiddly to achieve:

> **Put it on the internet, for real, using only free services — no credit
> card, no payments, now or scheduled for later.**

"For real" mattered. A lot of free hosting looks fine in a demo but quietly
falls over: the server falls asleep, the database gets deleted after a month,
the first visitor each hour waits a minute for a page to load. We wanted to
avoid those traps, not just hide them.

---

## 2. The shape of the app (the three pieces)

Every web app of this kind has three moving parts. It helps to picture them
as three separate machines that talk to each other:

| Piece | What it is | Plain English |
| --- | --- | --- |
| **Frontend** | Next.js (React) | The pages you see and click in your browser. |
| **Backend** | FastAPI (Python) | The "brain" — it answers questions like "log this person in" or "give me trending films." |
| **Database** | PostgreSQL | The filing cabinet where accounts and ratings are stored permanently. |

The movie data itself (posters, titles, descriptions) comes from **TMDB**, a
free public movie database we call out to. Our backend holds a TMDB key and
relays the results, so the key never sits in the browser where anyone could
copy it.

---

## 3. The big decision: where each piece lives

The most consequential choice was **not** putting all three pieces on one
platform. Early on, everything ran together on a single host (Render). It
worked, but it inherited that host's free-tier weaknesses for *every* piece.
We split them up so each part lives on the platform that serves it best:

| Piece | Platform we chose | Why this one |
| --- | --- | --- |
| Frontend | **Vercel** | Never sleeps, served from a global CDN, and it's the company that builds Next.js — so the app it's designed for. |
| Database | **Neon** | Free **and permanent**. Most free databases get deleted after ~30 days; Neon's doesn't. |
| Backend | **Render** | Free Docker hosting. It *does* sleep when idle, so we added a trick (below) to keep it awake. |

None of these required a payment method.

### Why split it up — the trade-off in one sentence

A single platform is simpler to set up but forces one compromise on all three
pieces; splitting them adds a little wiring but lets us dodge the *specific*
weakness of each free tier — a sleeping server, a disappearing database, a
slow frontend — all at once.

### A small decision with a big effect: put the backend next to the database

Splitting the pieces across platforms created one subtle trap of its own:
**distance.** The backend (Render) and the database (Neon) can each be hosted
in different parts of the country. Every page the app serves asks the database
several questions, and each question is a round trip — so if the two live on
opposite coasts, every one of those trips pays ~60–80 milliseconds just
traveling the wire. Stack a handful of them up per request and you've added
real, visible lag for no good reason.

The fix is almost embarrassingly simple, and that's the point: **host the
backend in the same region as the database.** Neon's database lives in AWS's
Northern Virginia region (US East), so we pinned the Render backend to its
**Virginia** region too. Same-region round trips are roughly *one* millisecond
instead of sixty-plus — so the same code, unchanged, answers the database
dozens of times faster.

This is the kind of decision that doesn't show up in the feature list but
separates "it works" from "it's quick." It costs nothing on the free tier, and
it reflects a basic truth about distributed systems: **the speed of light is a
real budget.** Computers are fast; the wire between them is not. When two
services talk constantly, the first question to ask is "how far apart are
they?"

One operational wrinkle worth recording: Render fixes a service's region *when
the service is created* and won't move it afterward. Applying this meant
deleting and recreating the backend service in Virginia — which is safe here
precisely because of an earlier decision: the database lives on Neon, not on
the server, so tearing down and rebuilding the server loses nothing. The
accounts and ratings sit untouched in Neon the whole time. (The backend is
"stateless" — it remembers nothing between requests — which is exactly what
makes it disposable and, as a bonus, easy to scale later.)

---

## 4. The two free-tier traps, and how we beat them

### Trap 1: The sleeping backend ("cold starts")

Render's free servers **go to sleep after ~15 minutes of no traffic**. The
next visitor then waits ~50 seconds while it wakes up — long enough that our
app gave up and showed an error. This was the single most visible problem.

**The fix: a "keep-warm" heartbeat.** We added a tiny automated job
(`.github/workflows/keep-warm.yml`) that runs on GitHub's free automation and
pings the backend's `/health` address **every ~10 minutes, around the clock**.
The server never sits idle long enough to fall asleep, so real visitors always
hit a server that's already awake.

Why this is safe on the free budget: Render gives 750 server-hours per month,
and a single always-awake server uses about 744 — it fits, with room to spare,
*as long as we only keep one server awake.* (This is exactly why we moved the
frontend off Render and onto Vercel — it freed up that budget for the one
server that needs it.)

### Trap 2: The disappearing database

Render's free database is deleted after ~30 days. For a real product that's a
non-starter — you'd lose every account and rating. **Neon's free database is
persistent**, so we moved the filing cabinet there and sidestepped the whole
problem.

---

## 5. The technical problems we hit (and exactly how we fixed them)

This is the honest part of the journal — the things that broke. Each one
taught us something, and each fix is now baked into the code so it won't bite
the next person who deploys.

### Problem A — "The server won't start at all" (port binding)

**Symptom:** Both services failed to deploy on the first try.
**Cause:** Cloud hosts don't let your app pick its own door number (network
port); they assign one and expect your app to listen on *that* one. Our app
was hard-coded to a fixed port, so the host couldn't find it.
**Fix:** We changed both apps to read the port the platform hands them
(`$PORT`). Now they listen wherever they're told.
*(Commit `fd4a178`.)*

### Problem B — "UID 1000 is not unique" (the frontend image)

**Symptom:** The frontend's Docker image failed to build.
**Cause:** For security, apps shouldn't run as the all-powerful "root" user. We
tried to create a dedicated non-root user, but the base image already *ships*
one at the same internal ID, so the system rejected the duplicate.
**Fix:** Instead of creating a new user, we reuse the one already there
(`USER node`). Simpler and avoids the clash.
*(Commit `8d621ac`.)*

### Problem C — The database connection string the app couldn't read

**Symptom:** Risk that the backend couldn't connect to Neon.
**Cause:** Neon hands out a connection string in a dialect built for one
Postgres driver, decorated with options (`sslmode`, `channel_binding`) that
**our** driver (asyncpg) doesn't understand and outright rejects.
**Fix:** We taught the app to **translate the string automatically** the moment
it reads it — rewriting the prefix to the form our driver expects, converting
the encryption option to the right name, and dropping the one option our
driver can't parse. The practical payoff: **you can paste Neon's string in
exactly as given** and it just works — no manual editing, no foot-guns.
*(In `backend/app/config.py`; shipped in `e2f64f3`.)*

### Problem D — The "list of allowed websites" setting wouldn't load

**Symptom:** Configuring which website is allowed to talk to the backend (a
security setting called CORS) caused the app to crash on startup.
**Cause:** The settings library insisted on reading that value as strict
computer-formatted data (JSON). A human typing a plain URL into a dashboard
would get an error.
**Fix:** We made the app accept that setting in **whatever form is easiest to
type** — a single URL, a comma-separated list, or JSON — and sort it out
internally. Friendlier for whoever deploys it.
*(In `backend/app/config.py`; shipped in `e2f64f3`.)*

### Problem E — "Could not load trending films" (the one that looked scariest)

**Symptom:** The site loaded, but the movie grid showed a red error. It *felt*
like the whole backend was down.

**How we diagnosed it — by elimination:**
1. Asked the backend directly (bypassing the browser). It answered perfectly:
   health check OK, trending films returned, and a login attempt correctly
   said "wrong password" — which *proved the database was connected and the
   accounts table existed.* So the server and database were 100% fine.
2. Checked the security setting (CORS). The backend was correctly allowing the
   Vercel site. Not the cause.
3. That left only one suspect: **how the browser itself was building the
   request.** We read the actual code shipped to the browser and found it was
   calling `https://filmclub-api.onrender.com.` — **with a stray period on the
   end of the address.**

**Cause:** The backend's web address had been pasted into Vercel's settings
with a trailing `.` (an easy thing to grab when copying a URL from the end of
a sentence). A web address ending in a dot is technically a *different* host
to a browser, and its security certificate doesn't match — so the browser
quietly refused every request. The page loaded (that's served by Vercel) but
its calls to the backend all failed.

**Fix:** Delete the trailing period from the setting and rebuild the frontend.
One character. Everything lit up immediately.

**The lesson:** When something "doesn't work," resist assuming the worst. We
proved the expensive parts (server, database) were healthy *first*, which
narrowed a scary-looking outage down to a one-character typo in a settings
field.

### Problem F — The "Top 500" page was empty

**Symptom:** The Top 500 page said "hasn't been generated yet."
**Cause:** The Top 500 isn't a live query — it's an expensive ranked list
(pulling ~1,000 candidate films from the movie database and re-ranking them
with an IMDb-style weighted average). It was only ever built when someone
manually triggered a "refresh." On the brand-new database, nobody had.
**Fix:** We made the app **build the Top 500 by itself the first time it starts
with an empty list**, quietly in the background so it never delays startup. It
does this once, then leaves it alone on every future restart. A fresh
deployment now serves a populated Top 500 with zero manual steps.

### Problem G — Hovering a poster took 13+ seconds to show "where to watch"

**Symptom:** Hovering a movie poster to see its streaming services spun for a
very long time — over a minute on a cold server.
**Cause:** Two things stacked up. First, a cold server (the ~50s nap from
Problem E's family). Second — and the real bug — the "lightweight" hover
lookup wasn't lightweight at all: to answer "where can I watch this," it was
quietly fetching and saving the film's *entire* dossier (full cast, crew,
keywords) — roughly seventy separate writes to the database, one slow trip at a
time. We measured it: **~13 seconds even on a warm server.**
**Fix:** We gave the hover its own **fast lane** — it now asks the movie
database for *only* the streaming info in a single request, and saves it in one
batched write instead of seventy. The full dossier is still fetched, but only
when you actually open a film's page, where it belongs. The hover lookup
dropped from ~13 seconds to a couple of seconds.

**A related note on geography:** part of the remaining couple-of-seconds was
simple distance — the backend and the database were living in different regions
of the country, so every database question made a cross-country round trip. We
then closed that gap by moving the backend into the same region as the database
— see *"put the backend next to the database"* in Section 3.

---

## 6. Things that went well

- **The "fail loudly" safety net paid off.** The backend is built to *refuse
  to start* in production if a critical secret (its login-signing key) is
  missing or weak, or if the movie-data key is absent. During deployment this
  did exactly its job: it stopped a misconfigured server from running instead
  of silently shipping something insecure. A deliberate "better to break now
  than leak later" choice.
- **Diagnosing without the browser.** Being able to question the backend
  directly turned vague "it's broken" reports into precise answers within
  minutes — and repeatedly proved the server was fine when the real fault was
  elsewhere.
- **Every fix became permanent.** None of the problems above were patched by
  hand on the server. Each fix went into the code and configuration files, so
  the project can be torn down and redeployed from scratch and still work.
- **A safety gate on changes.** The project already runs an automated test
  suite (60 backend tests) and build checks on every change via GitHub
  Actions, so a broken change is caught before it can reach the live site.

---

## 7. Security and privacy choices worth noting

- **The TMDB key stays server-side.** The browser never sees it; it only ever
  talks to our backend, which holds the key. A leaked key can't be copied from
  something the public can't see.
- **Login tokens are signed with a strong secret**, generated automatically by
  the host and never written into the code or shared.
- **Only our own frontend is allowed to call the backend** (the CORS setting),
  so a random third-party site can't drive our API from a user's browser.
- **Secrets live in each platform's secure store, never in the code.** The
  database password, signing key, and movie-data key are all set as protected
  environment variables.
- **Connection encrypted end to end.** The database link uses SSL; the public
  sites are HTTPS-only.
- A footnote we flagged in passing: a database password was shown in plain
  text during setup, so we noted it can be rotated with one click later — a
  good habit, not an emergency.

---

## 8. The final architecture (how a single click flows)

When you open **film-club-sigma.vercel.app** and the trending grid appears,
here's the journey behind it:

```
   You (browser)
        │  1. load the page
        ▼
   Vercel ──────────────► serves the Next.js frontend (never asleep)
        │
        │  2. the page asks for trending films
        ▼
   Render ──────────────► FastAPI backend (kept awake by the 10-min heartbeat)
        │   │
        │   └── 3a. calls TMDB for movie data ──► TMDB
        │
        │  3b. for accounts & ratings
        ▼
   Neon ────────────────► PostgreSQL database (free, permanent)
```

- **Frontend:** https://film-club-sigma.vercel.app
- **Backend:** https://filmclub-api.onrender.com
- **Keep-warm heartbeat:** a GitHub Action, every ~10 minutes
- **Cost:** $0 / month, no card on file.

---

## 9. Commit trail (for the technical reader)

The deployment work, in order:

| Commit | What it did |
| --- | --- |
| `9780670` | Hardened the backend for production (the "fail loudly" guard, security headers). |
| `8f41048` | First end-to-end deploy prep (sessions, query batching, initial free-tier setup). |
| `fd4a178` | Made both apps listen on the platform-assigned port (**Problem A**). |
| `8d621ac` | Reused the existing non-root user in the frontend image (**Problem B**). |
| `8a9c9cf` | Pinned the frontend's port so the old host routed to it correctly. |
| `e2f64f3` | The big migration: Vercel + Neon + Render, the keep-warm heartbeat, the Neon connection-string translator (**Problem C**) and the friendlier CORS setting (**Problem D**). |
| `1dfa408` | Auto-seed the Top 500 on first boot (**Problem F**) and give the poster-hover provider lookup a fast lane (**Problem G**). |
| `(region)` | Pin the Render backend to the **Virginia** region to colocate it with the Neon database — see "put the backend next to the database" above. |

(**Problem E**, the trailing-period typo, was fixed entirely in a hosting
dashboard setting — no code change needed.)

---

## 10. What's left / nice-to-haves

Done since the first cut:

- **Branch protection** on the code repository is now switched on — changes
  must pass the automated checks before reaching the live site.

Planned next (the backlog as it stands):

- **More ways to filter the catalogue** — by genre, by decade, by cast member,
  and by streaming service. The data we already cache (genres, credits, watch
  providers) makes these natural next steps rather than new plumbing.
- **Smooth out the remaining cold-start** — even with the keep-warm ping, the
  very first visit after an idle stretch is still slow to paint posters and
  artwork. Worth profiling image loading and the first-request path so a new
  visitor never waits.
- **Exercise the accounts/login path under real use** — sign-up, sign-in, and
  watching how the database behaves as real users and their libraries accumulate
  (connection limits on the free database, query performance as rows grow).
- **Cleanup:** delete the now-unused old Render frontend and database services
  so they don't count against the free budget.
- **Optional polish:** a custom domain, and analytics — both available free,
  neither required.

---

*In short: three free platforms, each picked to dodge a specific free-tier
trap; a handful of real bugs found and fixed at the source; and one
one-character typo that masqueraded as a total outage until we proved,
piece by piece, that everything else was healthy.*
