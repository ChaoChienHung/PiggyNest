# Technology stack

This list reflects the checked-in application manifests and imports. Versions are defined in `backend/requirements.txt` and `frontend/package.json`.

| Area | Technology | Use |
| --- | --- | --- |
| API | Python, FastAPI, Uvicorn | Versioned HTTP API and ASGI server |
| Validation and settings | Pydantic, pydantic-settings | Request/response schemas and environment configuration |
| Persistence | SQLAlchemy, SQLite | ORM models, sessions, and local database |
| Authentication | python-jose, passlib, bcrypt | JWT bearer tokens and password hashes |
| Recovery email | Python `smtplib`, `ssl`, `email` | TLS SMTP delivery for username reminders and password reset codes |
| Excel backup | openpyxl | `.xlsx` export and import |
| API tests | pytest, HTTPX/FastAPI TestClient | Isolated endpoint tests |
| Web app | React, TypeScript, React Router | UI, typing, and client-side routing |
| Build | Vite, `@vitejs/plugin-react`, npm | Development server and production bundle |
| Requests | Axios | Shared API client |
| Charts and icons | Recharts, lucide-react | Interactive charts and icons |
| Styling | Custom CSS and inline SVG | Theme, responsive layout, animations, illustrations |
| Frontend checks | TypeScript compiler, ESLint | Build-time type and lint checks |

`backend/requirements.txt` also lists `aiosqlite` and `matplotlib`; the active API uses synchronous SQLAlchemy sessions and Recharts for charts. The older CSV bookkeeping modules use pandas, but pandas is absent from the backend requirements. Review these dependencies with the legacy-code decision before removing or documenting them as supported features.

Configuration comes primarily from environment variables via `Settings` in `backend/app/core/config.py`. Its YAML loader supplies selected defaults and path settings from `config/config.yaml` if present; `backend/app/core/config.yaml` is not that default path. Prefer one documented configuration source when this is cleaned up.

Set `SECRET_KEY` to a stable, high-entropy value in the API environment for deployments. Without it, the API generates a random key at startup; existing login tokens then expire whenever the server restarts. The algorithm name is never a signing key.
