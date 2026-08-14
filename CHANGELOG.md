# Changelog

All notable changes to Flokus Academy will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-08-13
### Added
- Created a separated modern architecture: **Vue 3 frontend** and **FastAPI backend**.
- **Vue 3 Frontend**: Implemented using Vite, Pinia, and Vue Router for a dynamic SPA experience.
- **FastAPI Backend**: Asynchronous endpoints, SQLAlchemy models, and structured routing (`/auth`, `/courses`, `/tasks`, `/schedule`, `/ai_tutor`, etc.).
- Robust async PostgreSQL database integration using `asyncpg`.

### Changed
- Migrated away from the monolithic Streamlit application structure (v1).
- Overhauled UI architecture per `lms-architecture` guidelines for better security, readability, and state management.
- Updated documentation (README, Changelog) to reflect the new architecture.

### Deprecated
- The legacy v1 Streamlit codebase (app.py, old UI components) is being archived.
