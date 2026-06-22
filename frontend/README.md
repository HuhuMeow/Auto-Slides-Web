# Auto-Slides Frontend

This Vite application is the browser client for the FastAPI backend.

## Development

```bash
npm ci
npm run dev
```

The default uses same-origin `/api`; Vite proxies it to the local backend during development. Set a base URL only when the API is deployed on another origin:

```env
VITE_API_BASE_URL=
VITE_USE_MOCK_API=false
```

Set `VITE_USE_MOCK_API=true` only for isolated UI work. Components must access backend behavior through `src/api/client.ts`; do not add direct `fetch()` calls outside the API adapters.

## Validation and Build

```bash
npm run lint
npm run build
```

The production bundle is written to `dist/`. FastAPI serves this directory automatically, including SPA route fallback.

Shared request and response types are in `src/api/types.ts`, the real adapter is `src/api/httpApi.ts`, and optional mock behavior is implemented by `src/api/mockApi.ts` and `src/api/mockData.ts`.
