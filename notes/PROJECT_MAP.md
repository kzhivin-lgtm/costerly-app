# Costerly Project Map

This file explains where code belongs so the project stays understandable.

## Entry Point

- `app.py` sets Streamlit page config, applies global CSS, initializes state, and routes to screens.
- It should stay small. Business logic does not belong here.

## UI Layer

- `screens/` contains one Streamlit screen per file.
- `ui/` contains shared rendering helpers used by multiple screens.
- `ui/browser_session.py` owns the tab-scoped Auth storage bridge. Its component
  must remain inside the hidden Sidebar and outside the main screen layout. It
  reads only during session bootstrap; browser store/clear commands must remain
  callback-free so they cannot consume the next user interaction.
- `styles/` contains CSS grouped by responsibility.
- `styles/base.py` owns global design tokens and base Streamlit overrides.

## Application Layer

- `use_cases/` contains product flows such as processing an uploaded RFQ.
- `use_cases/rfq_processing.py` runs detection, writes the result to Supabase, and loads File Review data.
- `use_cases/estimation.py` starts object estimation by creating pending estimate records from detected objects.
- `use_cases/machinery.py` owns the 26-code storage catalog, the 16-capability
  Company Profile subset, outsourceable-operation boundary, company/supplier
  validation, Supabase persistence, and the bounded production-context snapshot
  used by future routing.
- A screen calls a use case. It should not call Claude, Supabase, or file parsing directly.

## Domain / Data Layer

- `models/` will define data contracts used by UI, services, validation, and database code.
- `validation/` will validate and normalize external responses before UI uses them.

## External Integrations

- `agents/` contains LLM detection orchestration, prompt loading, and detection schema validation.
- `db/` contains Supabase client and repositories.
- `db/sql/2026_09_24_machinery_foundation.sql` is the additive Machinery schema
  and catalog seed. It does not modify the prototype `company_machines` table.
- `engine/` will contain estimating/routing logic when we bring that part back.

## Project Notes

- `notes/` stores architecture notes, migration decisions, and project memory.
- `notes/WORK_RULES.md` stores working rules for debugging and project changes.
- `notes/AUTH_PASSWORD_RECOVERY_HANDOFF.md` stores the current 3.8.2 Auth and
- `notes/AUTH_PASSWORD_RECOVERY_HANDOFF.md` stores the closed 3.8.2 historical
  Auth and password-recovery contract.
- `notes/MACHINERY_FOUNDATION.md` stores the 3.9.1 scenario matrix, catalog
  boundary, routing priority, and verification state.
- Keep notes short and update them when structure changes.
