# citevault-ui

React 19 + TypeScript + Vite + Tailwind frontend for Citevault.

Served as a static SPA via nginx inside the Docker Compose stack. In development,
API requests are proxied to `citevault-api` at port 8000.

## Development

```bash
npm install
npm run dev            # dev server at http://localhost:5173
npm test               # Vitest unit tests
npx playwright test    # E2E tests (requires docker compose stack running)
```

See the root [README.md](../README.md) for the full project setup and Docker quick start.
