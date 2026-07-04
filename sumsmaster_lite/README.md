# Sumsmaster Lite

The static, browser-only edition of Sumsmaster. It mirrors the Tkinter app's plan-based practice, strategy feedback,
mastery tracking, resumable sessions, trick library, and coverage report. One learner profile is stored in the browser
with `localStorage`; no backend or account is required.

## Development

```bash
npm ci
npm start
npm test -- --watch=false
npm run build
```

The GitHub Pages workflow builds with `/sumsmaster/` as the base path. For another repository name, update
`--base-href` in `.github/workflows/deploy-lite.yml`.
