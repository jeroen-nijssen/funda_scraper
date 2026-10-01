# Contributing to Woningradar

Thanks for considering a contribution. Woningradar is a small, focused service:
it scrapes Dutch property listing sites and turns new listings into Kanboard
tasks. This document describes how to work on it.

**Everything in the development workflow is in English** — issues, pull
requests, commit messages, code, comments and docstrings. See
[Language conventions](#language-conventions) for the one important exception.

---

## Table of contents

- [Ethical scraping](#ethical-scraping)
- [Ways to contribute](#ways-to-contribute)
- [Local development setup](#local-development-setup)
- [Running the tests](#running-the-tests)
- [Running the full stack with Docker Compose](#running-the-full-stack-with-docker-compose)
- [The operator CLI](#the-operator-cli)
- [Code style](#code-style)
- [Language conventions](#language-conventions)
- [Adding a new scraper site](#adding-a-new-scraper-site)
- [Fixing a broken scraper](#fixing-a-broken-scraper)
- [Branch naming](#branch-naming)
- [Commit messages](#commit-messages)
- [Pull request process](#pull-request-process)
- [Reporting bugs and requesting features](#reporting-bugs-and-requesting-features)
- [Security issues](#security-issues)

---

## Ethical scraping

Read this before you write any code. It is not negotiable and it is the fastest
way to get a pull request rejected.

Woningradar is a personal house-hunting assistant, not a data harvesting tool.
It exists to check a handful of search pages a few times an hour — roughly what
a motivated human does with a browser tab.

**Rules for contributors:**

1. **Respect `robots.txt` and each site's Terms of Service.** If a change would
   put the project in conflict with either, it does not get merged.
2. **Never lower the default scrape intervals.** The current defaults in
   `app/config.py` are the floor, not a starting point:

   | Site      | Environment variable | Default |
   |-----------|----------------------|---------|
   | Funda     | `FUNDA_SLEEP`        | `3600` s (1 hour) |
   | Pararius  | `PARARIUS_SLEEP`     | `1800` s (30 minutes) |
   | Huispedia | `HUISPEDIA_SLEEP`    | `3600` s (1 hour) |

   Pull requests that reduce these defaults, or that add code paths which
   effectively increase request rate (parallel page fetching, pagination loops
   without delay, retry storms), will be rejected. Note that
   `docker-compose.yml` currently overrides these to very low values for local
   development convenience — that is a development artefact, not a licence to
   run it that way against live sites.
3. **No bot-detection evasion.** No captcha solving, no proxy rotation, no
   residential proxy support, no browser fingerprint spoofing, no headless
   browser added purely to defeat JavaScript challenges, no cookie or
   session-token replay obtained from a real browser session. The existing
   user-agent rotation in `app/config.py` is already at the limit of what this
   project is willing to ship; do not extend it.
4. **No rate-limit bypassing.** If a site returns `429` or `403`, the correct
   response is to back off further, not to try harder. The exponential backoff
   in `BaseScraper.make_request` is the intended behaviour.
5. **No scraping of personal data.** The scrapers collect street, city, price
   and URL. Do not add extraction of agent names, phone numbers, e-mail
   addresses, or anything else that identifies a person.
6. **Never paste scraped personal data into issues or PRs.**

Adding a capability from the list above is grounds for closing the pull request
without further review, even if the rest of the change is good.

See [DISCLAIMER.md](DISCLAIMER.md) for the project's position on the legal and
ethical framing of scraping, and on the user's own responsibility when running
this software.

---

## Ways to contribute

The most valuable contributions, in rough order of usefulness:

1. **Fixing broken selectors** when a site changes its HTML. This is the single
   most common failure mode — see
   [Fixing a broken scraper](#fixing-a-broken-scraper).
2. **Tests**, especially parser tests using fixture HTML.
3. **New scraper sites** — see
   [Adding a new scraper site](#adding-a-new-scraper-site).
4. **Documentation improvements** (Dutch for end users, English for developers).
5. **Bug reports** with enough detail to reproduce.

---

## Local development setup

Requires **Python 3.11+** and Git. Docker is needed only for running the full
stack.

```bash
git clone https://github.com/jeroen-nijssen/funda_scraper.git
cd funda_scraper

python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows (Git Bash)
source .venv/Scripts/activate
# Windows (PowerShell)
# .venv\Scripts\Activate.ps1

# Runtime dependencies (requests, beautifulsoup4, ...)
pip install -r app/requirements.txt

# Development dependencies (pytest, ruff, ...)
pip install -r requirements-dev.txt
```

Then create your local configuration:

```bash
cp .env.example .env
```

`.env` holds your search criteria and your Kanboard credentials. It is
git-ignored and **must never be committed**. If you add a new environment
variable in code, add it to `.env.example` too (with a safe placeholder value)
in the same pull request.

### A note on the import layout

The application uses **flat imports**: `app/main.py` does `from config import
Config`, not `from app.config import Config`. There is no `app/__init__.py` and
`app/` is not a package. This is deliberate — inside the container the
Dockerfile copies `app/` to the working directory `/app`, so those modules are
top-level there.

For local development this is handled by `pythonpath = ["app"]` in the
`[tool.pytest.ini_options]` section of `pyproject.toml`. The practical
consequences:

- Run `pytest` as a **bare command from the repository root**. Do not run
  `pytest app/`, do not `cd app` first, and do not use `python -m pytest` from
  inside `app/`.
- When adding a module under `app/`, import its siblings flatly
  (`from base_scraper import BaseScraper`), matching the existing files.

---

## Running the tests

From the repository root:

```bash
pytest
```

Useful variations:

```bash
pytest -v                                   # verbose
pytest app/test_scrapers.py::TestFundaScraper  # a single class
pytest -k pararius                          # by name
pytest --cov=app --cov-report=term-missing  # coverage, if pytest-cov is installed
```

Tests must not perform real network requests. Mock HTTP at the
`requests`/session boundary (see the existing `mock_response` fixture and the
`unittest.mock.patch` usage in `app/test_scrapers.py`). A test that hits a live
property site will be asked to change — it makes CI flaky and it hammers
someone else's server.

Parser tests are the most valuable kind: feed a small, anonymised HTML fixture
into `parse_listings` and assert on the resulting dictionaries.

---

## Running the full stack with Docker Compose

`docker-compose.yml` brings up two services: `kanboard` (the board, on port
`8080`) and `funda-scraper` (the scraper, health endpoint on port `8000`).

```bash
cp .env.example .env     # then edit it

docker compose build
docker compose up -d

docker compose logs -f funda-scraper
docker compose ps        # check health status of both services

docker compose down      # stop; add -v to also drop the Kanboard volumes
```

Notes:

- Logs are bind-mounted from the container's `/app/log` to `./logs` on the host.
  `logs/` is git-ignored.
- Kanboard ships with the default credentials `admin` / `admin`. Change them
  immediately and update `KANBAN_PASSWORD` in `.env`. Never expose port `8080`
  to the internet — see [SECURITY.md](SECURITY.md).
- `setup_kanboard.py` bootstraps the board/project so the scraper has somewhere
  to file tasks.
- The health endpoint is useful while developing:
  `curl http://localhost:8000/health`.
- **Before testing against live sites**, raise the `*_SLEEP` values in your
  `.env` back to the production defaults, or better, test your parser against a
  saved HTML fixture instead of the live site.

After rebuilding the image, remember that `docker compose up -d` does not
rebuild by default — use `docker compose up -d --build`.

---

## The operator CLI

`woningradar.sh` is the operator convenience wrapper for the common lifecycle
commands (building, starting, stopping, tailing logs, deploying the file set).
Prefer it over remembering raw `docker compose` invocations:

Run it without arguments to see every available command:

```bash
./woningradar.sh
```

If your change affects deployment or the set of files that need to be present on
a host, update `woningradar.sh` in the same pull request.

---

## Code style

- **Formatter and linter:** [ruff](https://docs.astral.sh/ruff/).
- **Line length: 120 characters.**
- Type hints on public functions and methods, matching the existing code.
- Docstrings on every module, class and public method (the existing code is
  consistent about this — keep it that way).
- Prefer explicit, readable code over clever code. This project is read far more
  often than it is written.

Before pushing:

```bash
ruff check .          # lint
ruff check --fix .    # autofix what it can
ruff format .         # format
```

CI runs ruff; a failing lint blocks the merge.

Logging conventions: use the module/worker logger that is passed in, not
`print`. Warnings for recoverable parse problems, errors for failures that abort
a run, info for normal progress.

---

## Language conventions

This project mixes two languages on purpose. Contributors get this wrong, so it
is spelled out:

| What | Language |
|------|----------|
| Code, identifiers, comments, docstrings | **English** |
| Log messages | **English** |
| Commit messages, branch names, PR titles and descriptions | **English** |
| Issues and discussions (development) | **English** |
| `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`, issue and PR templates | **English** |
| **End-user documentation** (installation and usage guides aimed at Dutch house hunters) | **Dutch** |

The reasoning: the software targets the Dutch housing market and its users are
Dutch, but development should be open to anyone. So the product speaks Dutch and
the codebase speaks English.

Do not translate code comments to Dutch, and do not translate the Dutch
end-user documentation to English unless you are explicitly adding a separate
English version.

---

## Adding a new scraper site

Concretely, to add a site called, say, `Huislijn.nl`:

**1. Create `app/huislijn.py`** and subclass `BaseScraper` from
`app/base_scraper.py`. You must implement exactly three abstract methods:

```python
"""Huislijn.nl property scraper."""
from typing import Dict, List

from bs4 import BeautifulSoup

from base_scraper import BaseScraper


class HuislijnScraper(BaseScraper):
    """Scraper for Huislijn.nl property listings."""

    def get_site_name(self) -> str:
        """Human-readable site name, used in log output."""
        return "Huislijn.nl"

    def build_url(self) -> str:
        """Build the search URL from self.config.scraper_config."""
        config = self.config.scraper_config
        return f"https://www.huislijn.nl/koop/{config.location}/0-{config.max_price}/"

    def parse_listings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Return one dict per listing with keys: street, city, price, url."""
        listings = []
        for item in soup.find_all("div", class_="listing-card"):
            try:
                ...
                listings.append({"street": street, "city": city, "price": price, "url": url})
            except Exception as e:  # never let one bad card kill the run
                self.logger.warning(f"Error parsing listing: {e}")
                continue
        return listings
```

Contract details that matter:

- `parse_listings` must return a list of dicts with **exactly** the keys
  `street`, `city`, `price`, `url`. `BaseScraper.process_listing` reads those
  four keys; anything else is ignored and a missing key raises.
- `url` must be **absolute**. Several sites emit relative hrefs — prefix the
  origin like `app/funda.py` does.
- Skip a card with `continue` rather than raising if a field is missing. A site
  layout change should degrade to "no listings found", not to a crash loop.
- Never bypass `self.make_request`; it carries the retry and backoff logic.
- Use `self.logger`, never `print`.
- `build_url` should honour as many of `location`, `distance`, `max_price`,
  `min_rooms` and `min_area` as the site actually supports. Document in the
  docstring which criteria the site ignores.

**2. Add a sleep interval in `app/config.py`**, in the `sleep_intervals` dict in
`Config.__init__`, with a default of **at least 1800 seconds**:

```python
self.sleep_intervals = {
    'funda': int(os.getenv('FUNDA_SLEEP', '3600')),
    'pararius': int(os.getenv('PARARIUS_SLEEP', '1800')),
    'huispedia': int(os.getenv('HUISPEDIA_SLEEP', '3600')),
    'huislijn': int(os.getenv('HUISLIJN_SLEEP', '3600')),  # 1 hour
}
```

**3. Register it in the `ScraperManager`** in `app/main.py`. Add the import at
the top and a worker in `ScraperManager.__init__`:

```python
from huislijn import HuislijnScraper
...
        self.workers['huislijn'] = ScraperWorker(
            HuislijnScraper, config, 'huislijn', config.sleep_intervals['huislijn']
        )
```

Each worker runs in its own daemon thread and is restarted automatically by
`monitor_workers` if it dies, so there is nothing else to wire up.

**4. Declare the new environment variable** in `.env.example`, in the `ENV`
block of the `Dockerfile`, and in the `environment:` list of the scraper service
in `docker-compose.yml`.

**5. Add tests** in `app/test_scrapers.py` (or a new `app/test_huislijn.py`)
covering `get_site_name`, `build_url`, and `parse_listings` against a small
saved HTML fixture — including the empty-page case.

**6. Update the documentation:** the Dutch end-user docs (site list, new env
var) and a `CHANGELOG.md` entry under `## [Unreleased]`.

Before starting, check the site's `robots.txt` and Terms of Service. If scraping
it is disallowed, do not open the pull request.

---

## Fixing a broken scraper

When a site changes its markup, `parse_listings` silently returns an empty list
and the log shows `No listings found`. To fix it:

1. Reproduce: run the scraper, note the `Requesting data from: ...` URL from the
   log, and open that URL in a browser.
2. Save the page once to a local file and work from that file. Do **not** loop
   requests against the live site while iterating on selectors.
3. Find the new listing-card container and field selectors in devtools.
4. Update the selectors in the relevant `app/<site>.py`.
5. **Add a regression test** with a trimmed, anonymised HTML fixture of the new
   markup. This is what stops the same break from going unnoticed next time.
6. Note the fix in `CHANGELOG.md`.

If you cannot fix it yourself, open an issue using the
*Scraper broken / site layout changed* template — capturing the search URL and
a single listing card's markup is most of the work.

---

## Branch naming

Branch off `main`. Use a type prefix and a short kebab-case description:

```
feat/add-huislijn-scraper
fix/funda-selectors-2026-09
fix/issue-42-duplicate-tasks
docs/dutch-install-guide
chore/bump-beautifulsoup
ci/cache-pip-in-release-workflow
refactor/extract-listing-model
test/pararius-parser-fixtures
```

Do not commit directly to `main`.

---

## Commit messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<optional scope>): <short imperative summary>

<optional body explaining what and why, wrapped at 72 characters>

<optional footer: Closes #123, BREAKING CHANGE: ...>
```

Types in use: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
`build`, `ci`, `chore`, `revert`.

Suggested scopes: `funda`, `huispedia`, `pararius`, `kanboard`, `config`, `docker`,
`compose`, `health`, `cli`, `deps`.

Examples:

```
fix(funda): update listing card selectors after site redesign
feat(config): add HUISLIJN_SLEEP interval
docs: add Dutch installation guide
chore(deps): bump beautifulsoup4 to 4.13.0
feat(config)!: rename KANBAN_URL to KANBOARD_URL

BREAKING CHANGE: KANBAN_URL is no longer read; update your .env.
```

Mark breaking changes with a `!` after the type/scope **and** a
`BREAKING CHANGE:` footer.

---

## Pull request process

1. Open an issue first for anything non-trivial, so the approach can be agreed
   before you write code. Small fixes and selector repairs can go straight to a
   pull request.
2. Fork, branch, and make your change.
3. Verify locally:
   - `pytest` (bare, from the repository root) passes.
   - `ruff check .` is clean.
   - `docker compose build` still succeeds if you touched dependencies,
     `Dockerfile` or `docker-compose.yml`.
4. Update `.env.example` if you added an environment variable, and add a
   `CHANGELOG.md` entry under `## [Unreleased]`.
5. Push and open a pull request against `main`. Fill in the pull request
   template honestly — the checklist is there to be used, not ticked blindly.
6. Keep pull requests focused. One logical change per pull request; unrelated
   reformatting makes review hard.
7. CI must be green. Address review comments with additional commits (do not
   force-push over a review in progress unless asked).
8. The maintainer (@jeroen-nijssen) reviews and merges. Squash merge is the
   default, so the pull request title should itself be a valid Conventional
   Commit subject.

By contributing you agree that your contribution is licensed under the
project's [Apache License 2.0](LICENSE).

---

## Reporting bugs and requesting features

Use the issue forms in
[.github/ISSUE_TEMPLATE](.github/ISSUE_TEMPLATE) — blank issues are disabled:

- **Bug report** — something does not work as documented.
- **Scraper broken / site layout changed** — a scraper returns no or wrong
  listings.
- **Feature request** — a new capability.

Usage and configuration questions belong in
[Discussions](https://github.com/jeroen-nijssen/funda_scraper/discussions),
not in issues.

Always redact credentials and personal data before pasting logs.

---

## Security issues

Do not open a public issue for a vulnerability. Follow the private reporting
process in [SECURITY.md](SECURITY.md).

---

## Code of Conduct

Participation in this project is governed by
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
