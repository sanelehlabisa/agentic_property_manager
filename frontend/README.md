# Frontend

The frontend is a React + TypeScript application built with Material UI (MUI). It provides role-specific screens, submits user input to FastAPI, and renders server responses.

Business rules stay in the backend. The frontend must not calculate prediction dates/costs, decide permissions, match providers, or invent status transitions.

## Suggested module layout

```text
frontend/
|-- src/
|   |-- api/                  # Typed HTTP client and endpoint functions
|   |-- app/                  # Router, providers, and MUI theme
|   |-- components/           # Shared presentational components
|   |-- features/
|   |   |-- auth/
|   |   |-- properties/
|   |   |-- reports/
|   |   |-- predictions/
|   |   |-- jobs/
|   |   `-- provider-profile/
|   |-- pages/                # Route-level composition
|   |-- types/                # API response types
|   `-- main.tsx
|-- Dockerfile
|-- package.json
`-- vite.config.ts
```

## UI foundation

Use MUI components and a small custom theme. Prefer `Box`, `Stack`, `Grid`, `Card`, `Typography`, `TextField`, `Select`, `Button`, `Chip`, `Alert`, `Dialog`, `DataGrid`/`Table`, and `Skeleton` before creating custom primitives.

### Color palette

| Token | Value | Use |
| --- | --- | --- |
| Primary blue | `#2563EB` | Main actions, active navigation, links |
| Dark blue | `#1D4ED8` | Hover/pressed primary state |
| Black | `#111827` | Main text and dark navigation |
| Gray 700 | `#374151` | Secondary text |
| Gray 500 | `#6B7280` | Labels and muted text |
| Gray 200 | `#E5E7EB` | Borders and dividers |
| Gray 100 | `#F3F4F6` | Page background and subtle panels |
| White | `#FFFFFF` | Cards, dialogs, and input surfaces |

Use semantic MUI success, warning, and error colors only for actual statuses. Keep the visual style clean: white cards, light-gray page background, black/gray typography, restrained blue accents, consistent 8px spacing, and accessible contrast.

## Pages by role

### Shared

- `/sign-in` - email entry.
- `/onboarding` - name and one role for a new user.
- Shared app shell - role label, navigation, current account, and demo account switcher.

### Tenant

- `/tenant/home` - assigned property and recent report statuses.
- `/tenant/reports/new` - category, optional component, title, description, urgency, and optional photo placeholder.
- `/tenant/reports/:id` - approval/rejection reason and safe job progress.

The tenant never sees bids, provider contact data before award, owner controls, predictions, or property editing.

### Homeowner/property manager

- `/portfolio` - accessible properties and pending-report counts.
- `/properties/:id` - overview, components, history, predictions, reports, and jobs.
- `/properties/:id/reports` - approval queue with approve/reject dialogs.
- `/properties/:id/predictions` - backend-generated due date, estimate, urgency, and explanation.
- `/jobs/:id` - job status and bid comparison with accept action.

### Service provider

- `/provider/profile` - business name, description, contact, coverage area/radius, and active service categories.
- `/provider/jobs` - matched open jobs returned by the API.
- `/provider/jobs/:id` - safe job details and bid create/update/withdraw actions.
- `/provider/awards` - awarded and active work.

## Core interface states

### Report approval card

Show reporter role, property, component/category, urgency, description, and submitted time. The approve action opens a confirmation form where the manager may edit the public job description and budget. Rejection requires a reason.

### Prediction card

Show component, due date, urgency chip, estimated cost, and the backend explanation. Clearly label it as a rule-based estimate. The UI only submits `approve` or `dismiss`; it does not recalculate the prediction.

### Provider job card

Show service category, suburb/city, description, budget range, desired date, and bid status. Do not show tenant identity or exact street address before award.

### Bid comparison

Show provider/business name, amount, availability, message, service match, and rating if seeded. Acceptance must use a confirmation dialog and then refresh from the API so competing-bid state comes from the backend.

## API consumption rules

- Keep one configured API base URL from `VITE_API_URL`.
- Put all requests in the `api/` layer; page components should not call `fetch` directly.
- Use request/response types matching the OpenAPI contract.
- Treat HTTP 401, 403, 404, 409, and 422 as distinct user-facing cases.
- Disable mutations while a request is pending and prevent accidental double submission.
- Refetch/invalidate API data after mutations instead of manually reproducing backend transitions.
- Route guards improve UX only; backend authorization remains mandatory.
- Store only the minimal demo session locally and never store database credentials in browser variables.

## Configuration

Vite receives public client configuration from environment variables supplied by `dev.docker-compose.yaml`. Only variables prefixed with `VITE_` can reach browser code. Secrets and PostgreSQL credentials must never use that prefix.

## Tickets

### FE-01 - Bootstrap React and MUI

- [x] Create React + TypeScript with Vite.
- [x] Add MUI, icons, routing, the shared theme, and typed API client.
- [x] Add role-aware app shell and route guards.

**Done when:** the app hot reloads, uses the documented palette, and displays backend health.

### FE-02 - Sign-in and onboarding

- [x] Build email sign-in and first-time name/role onboarding.
- [x] Redirect each role to the correct landing page.
- [x] Add an obvious demo account switcher.

**Done when:** each seeded user can enter its role-specific flow.

### FE-03 - Properties and tenant reporting

- [x] Build portfolio/property detail for owners and managers.
- [x] Build component and maintenance-history forms.
- [x] Build tenant assigned-property view and report form/status page.

**Done when:** a tenant submits a valid report and sees `pending_approval` from the API.

### FE-04 - Approval queue and predictions

- [x] List pending reports with approve/reject dialogs.
- [x] Show predictions with server-provided explanations.
- [x] Confirm job fields when approving a report or prediction.

**Done when:** an authorized user can publish one job from either source.

### FE-05 - Provider profile and matched jobs

- [x] Build editable provider identity, coverage, description, and service-category controls.
- [x] Display matched jobs and bid create/update/withdraw forms.

**Done when:** changing active services changes the feed after an API refresh.

### FE-06 - Bid review

- [x] Build owner/manager job and bid comparison screens.
- [x] Confirm bid acceptance and show the awarded state from the API.

**Done when:** the manager completes the core loop without client-side state hacks.

### FE-07 - Demo polish

- [x] Add MUI skeleton, empty, validation, error, snackbar, and confirmation states.
- [x] Verify keyboard use, labels, contrast, and responsive layout.
- [x] Test role boundaries and the full presentation flow.

**Done when:** the happy path is understandable without narration and common failures are recoverable.

## Out of scope

Payments, chat, maps, real-time updates, complex charts, multi-role settings, and a custom design system are intentionally excluded from the first build.
