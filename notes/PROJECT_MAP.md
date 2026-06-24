# Costerly Project Map

This file explains where code belongs so the project stays understandable.

## Entry Point

- `app.py` sets Streamlit page config, applies global CSS, initializes state, and routes to screens.
- It should stay small. Business logic does not belong here.

## UI Layer

- `screens/` contains one Streamlit screen per file.
- `ui/` contains shared rendering helpers used by multiple screens.
- `styles/` contains CSS grouped by responsibility.
- `styles/base.py` owns global design tokens and base Streamlit overrides.

## Application Layer

- `use_cases/` contains product flows such as processing an uploaded RFQ.
- `use_cases/rfq_processing.py` runs detection, writes the result to Supabase, and loads File Review data.
- A screen calls a use case. It should not call Claude, Supabase, or file parsing directly.

## Domain / Data Layer

- `models/` will define data contracts used by UI, services, validation, and database code.
- `validation/` will validate and normalize external responses before UI uses them.

## External Integrations

- `agents/` contains LLM detection orchestration, prompt loading, and detection schema validation.
- `db/` contains Supabase client and repositories.
- `engine/` will contain estimating/routing logic when we bring that part back.

## Project Notes

- `notes/` stores architecture notes, migration decisions, and project memory.
- Keep notes short and update them when structure changes.
