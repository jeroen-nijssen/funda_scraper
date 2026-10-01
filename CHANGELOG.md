# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Pushing a `v*.*.*` tag triggers the release workflow, which builds and publishes
the container image to GHCR. Plain pushes to `main` build and test but publish
nothing, so cutting a release is a deliberate act:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## [Unreleased]

### Added

- Branding: logo, wordmark and README banner under `assets/`.
- `kanboard-init` one-shot Compose service that bootstraps the Kanboard project
  and board columns automatically before the scraper starts.
- `KANBAN_BASE_URL`, `KANBAN_PROJECT_NAME` and `KANBAN_PROJECT_ID_FILE`
  environment variables for the Kanboard bootstrap.
- `app/huispedia.py`: a new scraper for Huispedia.nl, replacing the Jaap.nl
  scraper after Jaap.nl was shut down by its owner Mediahuis in January 2024.
  Huispedia absorbed Jaap's listings; data is read from the JSON payload the
  site embeds in its page markup, so no CSS selectors are involved.
- `BaseScraper.render_with_browser`, used by the Funda scraper to render pages
  with headless Chromium (Playwright) instead of a bare HTTP request, since
  Funda serves a static bot-check page to plain HTTP clients. This is
  best-effort and unconfirmed: testing still hit the same bot-check page,
  which looks like an IP-reputation block rather than a solvable challenge.
- GitHub Actions: CI (ruff, pytest on 3.11/3.12, bandit, image build with a
  health smoke test, Compose validation), tag-triggered GHCR release with build
  provenance, dependency review, and Dependabot.
- Repository collaboration setup: issue forms, PR template, CODEOWNERS,
  contributing guide, code of conduct, security policy.
- Dutch end-user documentation and a scraping disclaimer.
- Root `pyproject.toml` (pytest + ruff config) and `requirements-dev.txt`.
- Test coverage for configuration handling, HTML parsing and duplicate
  suppression.

### Changed

- Documentation for end users is now in Dutch; code and contributor docs stay
  in English.
- `copy_funda_scraper_files.sh` is renamed to `woningradar.sh`.
- `setup_kanboard.py` is fully environment-driven instead of hardcoding
  `localhost:8080`.
- `app/requirements.txt` holds runtime dependencies only; test and lint tools
  moved to `requirements-dev.txt`.

### Fixed

- Pararius scraper: requests without a full browser-like header set (not just
  a `User-Agent`) were rejected with a 403; `BaseScraper.get_headers` now sends
  `Accept-Language`, `Sec-Fetch-Mode` and `Sec-Fetch-Dest`.
- Pararius scraper: the city/location CSS class was renamed by the site from
  `listing-search-item__location` to `listing-search-item__sub-title`.
- Kanboard bootstrap no longer deletes all board columns — and with them every
  task in those columns — when the column layout does not match. Boards holding
  tasks now only get missing columns added.
- Compose no longer defaults the scrape intervals to 5 seconds, which hammered
  the target sites. Defaults are 3600/1800/3600 seconds.
- Test suite no longer asserts a location that contradicts the configured
  default, so it passes and can gate CI.
- Removed committed `__pycache__` bytecode and the dead `app/funda_scraper.sh`.
