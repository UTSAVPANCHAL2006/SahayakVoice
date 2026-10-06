# Sahayak Voice — frontend (Next.js)

## Run

```bash
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` in `.env.local` if API is not `http://localhost:8000`.

## Layout

```
src/
  app/
    page.tsx           Landing
    dashboard/         Customer queue (main demo entry)
    call/[id]/         Live voice session
    cases/[id]/        Resolution case view
  components/
    AppShell.tsx       Sidebar shell
    dashboard/         Customer queue row and controls
  lib/
    api.ts             Backend HTTP + types
    format.ts          INR, initials, last-4
    scenarios.ts       Filter + counts
    scenarioTheme.ts   Per-issue copy & colors
```

## Stack

Next.js App Router, CSS in `globals.css` + `dashboard/dashboard.css`. No extra UI library.
