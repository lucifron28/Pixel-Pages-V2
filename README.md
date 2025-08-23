# Pixel Pages Web

A modern web reader for EPUB books built with Next.js + TypeScript and EPUB.js. Integrates with the Pixel Pages FastAPI backend for authentication, uploads, ingestion status, and reading progress.

## Stack

- Next.js (App Router) + TypeScript
- Tailwind CSS + Headless UI/Radix UI
- TanStack Query (React Query) for data fetching
- EPUB.js for rendering, pagination, themes
- Deployed on Vercel (Hobby plan)
- FastAPI backend (Heroku)

## Features

- Authentication (login/register)
- Upload EPUB via presigned URL to object storage
- Library: list user books, covers, metadata
- Reader: pagination, themes, font size/line-height, TOC navigation
- Progress sync: save CFI/chapter progress to backend
- Basic search (Postgres FTS on backend)
- Responsive UI and basic offline support (cache last-read chapter locally)

## Project Structure

```
pixel-pages/
├── README.md
├── .env.example
├── .gitignore
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── deploy-web.yml
│       ├── deploy-api.yml
│       └── generate-clients.yml
│
├── apps/
│   ├── api/
│   │   ├── README.md
│   │   ├── Procfile
│   │   ├── pyproject.toml
│   │   ├── alembic.ini
│   │   ├── storage/              # Local file storage (gitignored)
│   │   │   ├── uploads/          # Temporary uploads before ingestion
│   │   │   │   └── users/
│   │   │   │       └── {user_id}/
│   │   │   │           └── {upload_id}.epub
│   │   │   ├── books/            # Processed books
│   │   │   │   └── {book_id}/
│   │   │   │       ├── manifest.json
│   │   │   │       ├── cover.jpg
│   │   │   │       ├── chapters/
│   │   │   │       ├── images/
│   │   │   │       ├── fonts/
│   │   │   │       └── css/
│   │   │   └── temp/             # Temporary processing files
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── db.py
│   │   │   ├── deps.py
│   │   │   ├── auth/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py
│   │   │   │   ├── service.py
│   │   │   │   └── schemas.py
│   │   │   ├── files/            # File upload/download endpoints
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py     # File upload/download endpoints
│   │   │   │   └── service.py    # Local storage operations
│   │   │   ├── users/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py
│   │   │   │   ├── routes.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── service.py
│   │   │   ├── books/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py
│   │   │   │   ├── routes.py
│   │   │   │   ├── schemas.py
│   │   │   │   └── service.py
│   │   │   ├── ingestion/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py
│   │   │   │   └── service.py
│   │   │   ├── progress/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── models.py
│   │   │   │   ├── routes.py
│   │   │   │   └── schemas.py
│   │   │   ├── search/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py
│   │   │   │   └── service.py
│   │   │   └── utils/
│   │   │       ├── __init__.py
│   │   │       ├── sanitizer.py
│   │   │       ├── storage.py    # Local file storage utilities
│   │   │       ├── security.py
│   │   │       └── pagination.py
│   │   ├── migrations/
│   │   │   ├── env.py
│   │   │   ├── script.py.mako
│   │   │   └── versions/
│   │   └── tests/
│   │       ├── unit/
│   │       └── integration/
│   │
│   ├── worker/
│   │   ├── README.md
│   │   ├── Procfile
│   │   ├── pyproject.toml
│   │   ├── worker/
│   │   │   ├── __init__.py
│   │   │   ├── worker.py
│   │   │   ├── tasks.py
│   │   │   ├── epub/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── parser.py
│   │   │   │   ├── normalizer.py
│   │   │   │   ├── manifest.py
│   │   │   │   └── images.py
│   │   │   └── storage.py
│   │   └── tests/
│   │
│   ├── web/
│   │   ├── README.md
│   │   ├── package.json
│   │   ├── next.config.js
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   ├── .env.local.example
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── globals.css
│   │   │   │   ├── auth/
│   │   │   │   │   ├── login/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   └── register/
│   │   │   │   │       └── page.tsx
│   │   │   │   ├── books/
│   │   │   │   │   ├── upload/
│   │   │   │   │   │   └── page.tsx
│   │   │   │   │   └── [bookId]/
│   │   │   │   │       └── page.tsx
│   │   │   │   └── read/
│   │   │   │       └── [bookId]/
│   │   │   │           └── page.tsx
│   │   │   ├── components/
│   │   │   │   ├── reader/
│   │   │   │   │   ├── EpubReader.tsx
│   │   │   │   │   ├── TocSidebar.tsx
│   │   │   │   │   └── ReaderControls.tsx
│   │   │   │   ├── library/
│   │   │   │   │   ├── BookCard.tsx
│   │   │   │   │   └── BookGrid.tsx
│   │   │   │   └── forms/
│   │   │   │       └── UploadForm.tsx
│   │   │   ├── lib/
│   │   │   │   ├── api.ts
│   │   │   │   ├── auth.ts
│   │   │   │   ├── config.ts
│   │   │   │   └── storage.ts
│   │   │   └── styles/
│   │   │       └── globals.css
│   │   ├── public/
│   │   │   └── epub-reader/
│   │   └── tests/
│   │
│   └── mobile/
│       ├── README.md
│       ├── pubspec.yaml
│       ├── android/
│       ├── ios/
│       ├── lib/
│       │   ├── main.dart
│       │   ├── screens/
│       │   │   ├── login_screen.dart
│       │   │   ├── register_screen.dart
│       │   │   ├── library_screen.dart
│       │   │   ├── book_details_screen.dart
│       │   │   └── reader_screen.dart
│       │   ├── services/
│       │   │   ├── api_client.dart
│       │   │   ├── auth_service.dart
│       │   │   └── storage_service.dart
│       │   ├── widgets/
│       │   │   ├── book_tile.dart
│       │   │   └── reader_controls.dart
│       │   └── utils/
│       │       ├── env.dart
│       │       └── routes.dart
│       └── assets/
│           ├── web-reader/
│           └── fonts/
│
├── packages/
│   └── shared/
│       ├── README.md
│       ├── openapi/
│       │   ├── schema.yaml
│       │   └── clients/
│       │       ├── typescript/
│       │       └── dart/
│       ├── python/
│       │   ├── models/
│       │   └── constants.py
│       └── ts/
│           ├── types/
│           └── constants.ts
│
├── infra/
│   ├── heroku/
│   │   ├── README.md
│   │   ├── Procfile.api
│   │   ├── Procfile.worker
│   │   ├── app.json
│   │   └── release.sh
│   ├── vercel/
│   │   ├── README.md
│   │   └── project.json
│   └── scripts/
│       ├── dev_bootstrap.sh
│       ├── gen_openapi.sh
│       └── seed_dev.py
│
└── docker/
    ├── api.Dockerfile
    ├── worker.Dockerfile
    ├── docker-compose.dev.yml
    └── .dockerignore
```

## Environment Variables

Create a `.env.local` file with values like:

```env
NEXT_PUBLIC_API_BASE_URL=https://<heroku-app>.herokuapp.com
NEXT_PUBLIC_ASSET_CDN_URL=https://<r2-or-s3-domain>
NEXT_PUBLIC_APP_NAME=Pixel Pages
```

If using cookie-based auth on a subdomain, coordinate CORS and cookie settings with the backend.

## Development

- Node 18+
- pnpm (recommended) or npm/yarn

Run locally:

```bash
pnpm install
pnpm dev
# build and start
pnpm build && pnpm start
# lint and tests
pnpm lint
pnpm test # if configured
```

Local backend defaults:

- API at `http://localhost:8000` — set `NEXT_PUBLIC_API_BASE_URL` accordingly.

## Deployment (Vercel)

1. Connect the repository to Vercel.
2. Set the environment variables in Project Settings.
3. Prefer static generation + client-side fetching to minimize serverless usage.
4. Optionally add 1–2 short cron jobs (cache warmers, housekeeping).

## Upload Flow

1. Request a presigned URL from the backend: `POST /books/presign`
2. PUT the `.epub` to object storage using the returned URL/headers.
3. Notify backend with the object key: `POST /ingestion/start`
4. Poll ingestion status or subscribe to updates.
5. Reader loads normalized assets via signed URLs from storage/CDN.

## Reader Implementation (EPUB.js)

- Load book via baseUrl + manifest (recommended) or the original `.epub`.
- Inject theme CSS for light/dark/sepia and font scaling.
- Track positions via EPUB CFI; debounce saves to backend.
- Isolate CSS in an iframe to avoid global style bleed.

## Security Notes

- Never trust book HTML: backend must sanitize before publishing assets.
- Use signed URLs for assets with short TTLs.
- Enforce CORS to the Vercel domain and use HTTPS end-to-end.
- Rate limit login and upload endpoints on the backend.

## Roadmap

- Highlights/annotations
- Meilisearch for richer search
- Collections/series and sharing
- Enhanced offline-first behavior (service worker, smarter caching)