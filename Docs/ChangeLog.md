# Changelog

All notable changes to this project will be documented in this file.

The format is based on "Keep a Changelog" and this project follows Semantic Versioning.

## [Unreleased]

### Added
- `POST /network/scan_range` endpoint: scan a CIDR or IP range and return open/closed/filtered ports per host. (2026-01-14)
- UI: new operation "Analisis de redes (rango)" in the FastAPI operations panel; renders a card per IP with port results and per-card internal scrolling. (2026-01-14)
- Tests: `tests/controllers/test_network_api_scan_range.py` covering CIDR fallback and large-range rejection. (2026-01-14)
- Docs: `Docs/Network_Scan_Range.md` describing API, UI usage and examples. (2026-01-14)

### Changed
- Network scanning service (`app.services.network_analysis.network_analysis`) now includes explicit `state` field for parsed nmap results (e.g., `open`, `closed`, `filtered`) to allow correct UI rendering of filtered ports. (2026-01-14)
- UI (`src/app/ui/static/ui.js`, `styles.css`) shows `FILTERED` badge (orange) for `state === 'filtered'`; sorts hosts and ports to surface open/filtered results first; cards include collapse/expand and limited port-list height with internal scrolling. (2026-01-14)

### Fixed
- Validation improvements: `RangeScanRequest` normalizes empty strings and accepts `start`/`end` when `cidr` is empty; improved handling of form payloads to avoid 422 errors from the UI. (2026-01-14)

### Security
- Scan requests are limited to a maximum of 1024 hosts per request to prevent accidental mass-scans. (2026-01-14)


## [0.0.0] - 2026-01-14
- Initial release notes entry (internal development)
