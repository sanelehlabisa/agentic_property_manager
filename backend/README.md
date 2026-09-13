# Backend

The FastAPI backend is the system's source of truth. It owns access control, validation, report approval, maintenance rules, job matching, bid transitions, and persistence. PostgreSQL is the system of record.

The React frontend must not duplicate these rules. It calls the API and renders the permitted actions and state returned by the server.

## Suggested module layout

```text
backend/
|-- app/
|   |-- api/                  # Thin route handlers
|   |-- core/                 # Settings, database, auth, and errors
|   |-- models/               # SQLAlchemy models
|   |-- schemas/              # Pydantic request/response types
|   |-- repositories/         # Database queries
|   |-- services/             # Use-case orchestration
|   |-- rules/                # Deterministic maintenance rules
|   |-- seed/                 # Categories, rules, and demo accounts
|   `-- main.py
|-- migrations/
|-- tests/
|-- Dockerfile
`-- requirements.txt
```

## Backend-owned use cases

### Tenant

- Return only properties assigned to the signed-in tenant.
- Create an issue report with category, title, description, urgency, and optional component.
- View their own reports and the safe subset of linked job status.
- Prevent tenants from approving reports, creating public jobs, or seeing bids.

### Homeowner and property manager

- Create/update a report for an accessible property.
- Review pending tenant reports and approve or reject them with a reason.
- Convert an approved report or prediction into one job.
- Manage properties, access assignments, components, and service history where authorized.
- View job bids and accept exactly one valid bid.

A homeowner-created or manager-created report may be approved as part of the create-job confirmation. Tenant reports always require explicit approval.

### Service provider

- Create/update a provider profile, coverage location/radius, service description, and contact information.
- Add, activate, or deactivate predefined service categories.
- View only open jobs matching an active category and coverage area.
- Submit one active bid per job, update it while the job is open, or withdraw it.
- View jobs awarded to their profile.

## Data model

| Table | Key fields and constraints |
| --- | --- |
| `users` | UUID `id`; unique normalized `email`; `name`; one `role` enum |
| `properties` | UUID `id`; display name; address; suburb; city; timestamps |
| `property_access` | Property/user foreign keys; `access_role`; unique property/user pair |
| `service_categories` | Stable code and display name, such as plumbing or electrical |
| `components` | Property FK; category FK/code; name; installation date; condition |
| `maintenance_rules` | Component category; interval months; warning days; default cost; active flag |
| `maintenance_records` | Component FK; completion date; amount; description; optional provider |
| `predictions` | Component/rule FKs; due date; estimate; urgency; explanation; status |
| `issue_reports` | Property/reporter FKs; optional component; category; details; urgency; review data; status |
| `jobs` | Property/category FKs; nullable source report/prediction; budget; private/public location; status; approval audit |
| `provider_profiles` | Unique user FK; business details; base location; radius; rating |
| `provider_services` | Provider/category FKs; description; active flag; unique pair |
| `bids` | Job/provider FKs; amount; message; availability; status; unique pair |

Use database constraints as well as service validation. A job must have one approved source (`issue_report_id` or `prediction_id`), never both. Each source can create at most one job.

## State transitions

Only service-layer methods may perform these transitions:

```text
Issue report: pending_approval -> approved -> converted_to_job
                                `-> rejected

Prediction:   active -> approved -> converted_to_job
                    `-> dismissed

Job:          open -> awarded -> in_progress -> completed
                `-> cancelled

Bid:          submitted -> accepted
                       `-> withdrawn
                       `-> rejected
```

Accepting a bid must run in one database transaction: lock the job, confirm it is open, accept the chosen bid, reject competing bids, and mark the job awarded.

## Predefined maintenance rules

No LLM is needed for the PoC. Seed a small rule set such as:

| Component category | Interval | Warning window | Demo default cost |
| --- | ---: | ---: | ---: |
| Plumbing inspection | 12 months | 30 days | Configured seed value |
| Geyser/water heater service | 12 months | 45 days | Configured seed value |
| Electrical inspection | 24 months | 60 days | Configured seed value |
| HVAC service | 6 months | 30 days | Configured seed value |
| Roof/gutter inspection | 12 months | 45 days | Configured seed value |

The service calculates:

```text
baseline_date = latest_completed_service_date OR component.installed_on
due_date = baseline_date + rule.interval_months
urgency = overdue | due_soon | upcoming
estimated_cost = median(recent_matching_costs) OR rule.default_cost
```

Every prediction response includes a plain-language explanation, for example: `Annual geyser service is due 15 days from now; estimate uses the last two completed services.`

Users select categories from the seeded list. CSV import uses required columns, fixed mappings, and predefined keyword aliases. Unknown categories are returned as validation errors for manual correction rather than guessed.

## Authorization rules

| Action | Tenant | Homeowner | Manager | Provider |
| --- | :---: | :---: | :---: | :---: |
| View assigned property | Yes | Yes | Yes | No |
| Report issue | Yes | Yes | Yes | No |
| Approve/reject report | No | Yes | Yes | No |
| Manage property/components | No | Yes | Yes | No |
| View predictions | No | Yes | Yes | No |
| Create job | No | Yes | Yes | No |
| View job bids | No | Yes | Yes | Own only |
| Manage provider profile | No | No | No | Yes |
| Bid on matched job | No | No | No | Yes |

`Yes` is still property-scoped. A manager needs a manager access record, a homeowner needs owner access, and a tenant needs tenant access.

## Initial REST API

```text
GET    /health
POST   /auth/email
GET    /me

GET    /properties
POST   /properties
GET    /properties/{property_id}
PATCH  /properties/{property_id}
DELETE /properties/{property_id}
POST   /properties/{property_id}/access

GET    /properties/{property_id}/components
POST   /properties/{property_id}/components
GET    /components/{component_id}/maintenance-records
POST   /components/{component_id}/maintenance-records
POST   /properties/{property_id}/maintenance-imports/preview
POST   /properties/{property_id}/maintenance-imports/confirm

GET    /properties/{property_id}/reports
POST   /properties/{property_id}/reports
POST   /reports/{report_id}/approve
POST   /reports/{report_id}/reject

GET    /properties/{property_id}/predictions
POST   /predictions/{prediction_id}/approve
POST   /predictions/{prediction_id}/dismiss
POST   /jobs/from-report/{report_id}
POST   /jobs/from-prediction/{prediction_id}

GET    /provider/profile
PUT    /provider/profile
PUT    /provider/services
GET    /provider/matched-jobs
POST   /jobs/{job_id}/bids
PATCH  /bids/{bid_id}
DELETE /bids/{bid_id}
GET    /jobs/{job_id}/bids
POST   /bids/{bid_id}/accept
```

The exact endpoint shapes can change during implementation, but the authorization and state-transition behavior should remain in services, not route handlers.

## Configuration

Settings come from environment variables loaded from the repository root `.env` during development. Credentials must not be hard-coded in Python or committed to Git. See the root `.env.example` for required names.

## Tickets

### BE-01 - Bootstrap API and database

- [x] Create FastAPI, `GET /health`, settings, CORS, SQLAlchemy, and migrations.
- [x] Read all configuration from environment variables.
- [x] Add consistent error responses and request logging.

**Done when:** the container hot reloads and the API/database health checks pass.

### BE-02 - Schema and seed data

- [x] Create the tables and constraints documented above.
- [x] Seed service categories, maintenance rules, and demo users/property.

**Done when:** a clean database can be migrated and seeded repeatedly.

### BE-03 - Demo identity and access

- [ ] Find/create users by normalized email and finish first-time onboarding.
- [ ] Enforce role and property membership in reusable dependencies/services.

**Done when:** cross-property and cross-role access tests fail with HTTP 403/404.

### BE-04 - Property maintenance data

- [ ] Implement property, access, component, and maintenance-record endpoints.
- [ ] Add CSV preview/confirm using fixed mappings and aliases.

**Done when:** an owner can prepare complete input for the rule engine.

### BE-05 - Issue reports and approval

- [ ] Implement tenant/owner/manager report creation.
- [ ] Implement owner/manager approve and reject actions with audit fields.
- [ ] Expose only safe status information to tenants.

**Done when:** a tenant report cannot become a job until an authorized user approves it.

### BE-06 - Rule engine

- [ ] Generate stable predictions from component history and seeded rules.
- [ ] Return due date, urgency, estimated cost, and explanation.

**Done when:** fixed test data always generates the expected predictions without external AI calls.

### BE-07 - Job creation

- [ ] Convert an approved report or prediction into exactly one open job.
- [ ] Store approval audit data and hide exact/private location data from unmatched providers.

**Done when:** duplicate and unapproved job creation is rejected.

### BE-08 - Provider profiles, matching, and bidding

- [ ] Implement provider profile and service-category updates.
- [ ] Match by active service category and simple city/suburb coverage.
- [ ] Implement bid submission, update, withdrawal, listing, and atomic acceptance.

**Done when:** a matching provider can bid and an authorized manager can award one bid.

### BE-09 - Demo reliability

- [ ] Test both tenant-report and prediction-to-job happy paths.
- [ ] Add resettable seed data and document shortcuts.

**Done when:** the entire demo can be replayed predictably.

## Out of scope

Production authentication, payments, chat, notifications, background ML training, LLM integration, complex auctions, maps, and production-grade distance calculations are deferred.
