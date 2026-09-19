# Changelog

All notable changes to this project will be documented in this file.

## v0.10.3

Date: 2026-09-19

### Added
- **Self-hosting on a machine you own** -- `scripts/deploy.py` moves a deployment to a different revision of the repository in one command: it exports the revision, installs its dependencies, builds its interface, snapshots the database, checks the new revision against that snapshot, repoints a `current` symlink and restarts the service. Deployment was the step that made every other improvement hard to use, because the cost of redeploying accumulates until you stop bothering to update.
- **`/api/health` reports the running revision** -- The response gained a `revision` field, supplied through `OPENVOCA_REVISION` by whatever started the process. After a deployment, "is it up?" and "is the new code live?" are the same question, and answering them with two calls invites checking only the first.
- **`deploy/openvoca.service`** -- A systemd unit that runs the service from a symlink, so switching revisions never touches it. Restarts are bounded: a revision that refuses to start enters the `failed` state after a few attempts rather than looping and burying the reason. `ProtectSystem=strict` makes the code tree read-only for the service, so an accidental write fails immediately instead of surviving until the next deployment replaces it.
- **`backend/src/preflight.py`** -- Runs a revision's own startup checks without starting it, so a revision that would refuse to serve is never switched to.
- **`docs/DEPLOY.md`** -- The full procedure, written for whoever is on the deployment machine. Includes why the commands pass `PATH` through `sudo` explicitly.
- **`docs/specs/private-deployment.md`** -- 27 acceptance criteria covering the distribution contract, startup checks, deployment atomicity, process supervision, and the boundary between requesting and executing an update.

### Fixed
- **The portable bundle overrode the caller's data directory** -- The launcher built its child environment with the bundle's own `data/` last, so `OPENVOCA_DATA_DIR` set from outside was silently discarded. Because an update replaces the bundle directory, this made every update destructive: it would take the database with it. The data directory is now a default rather than an assignment, and the directory that actually gets used is the one created. This was the single obstacle that made any update path unsafe.
- **A database older than the models silently served broken queries** -- `create_all()` creates missing tables but never alters existing ones, so a model that gained a column kept running against a table that never received it. The application started, the health check answered `200`, static pages loaded, and the first query touching that column raised `no such column`. Every automated probe reported the service as healthy. Startup now compares the model's declared columns against the database and refuses to start, naming the table and the missing columns. The check is deliberately one-directional: a surplus column is what a rollback looks like, and refusing to start then would block the recovery path an operator reaches for precisely when a deployment has gone wrong.
- **The interface path was only reported when it existed** -- Startup printed the frontend directory only when a build was present, and otherwise mentioned it inside a warning on stderr. The output therefore differed by environment and omitted the one line an operator reads when the interface is blank. All three paths are now always printed.
- **`deploy.py` failed with a traceback when a tool was unreachable** -- A missing executable surfaces from `subprocess` as `FileNotFoundError`, which escaped the deployment's error handler. The operator got a stack trace instead of being told which revision was still serving and how to return to it — the one thing a failed deployment must say. The toolchain is now checked before any work begins, and the message names the `PATH` that was searched, because the usual cause is not an absent tool: `sudo` replaces `PATH` with its own `secure_path`, which contains `/usr/bin` but not where user-installed tools live. `git` is found and `uv` is not, which is why a deployment gets past the export and fails at the dependency install.
- **The SPA fallback test asserted nothing in CI** -- The static routes were defined inside a module-level `if dist exists` block, so in an environment without a frontend build they did not exist as attributes, and the test's `hasattr` guard meant it reported success without executing an assertion. `AC-SHELL-001-02` was green and untested. Registration moved into `register_spa(app, dist)`, and the test now drives real requests through a `TestClient`.

### Changed
- **Startup now refuses to serve a database it cannot query** -- See Fixed above. This is a behaviour change rather than a cosmetic one: a revision will decline to start where it previously started and failed later. A revision that is deployed and refuses to start leaves the previous one serving.
- **The VPS deployment specification was removed** -- `docs/specs/deployment.md` described a public deployment with a reverse proxy, TLS termination, an image registry and session-cookie authentication. It assumed a target that may never exist. Specifications should describe the path actually being taken, so it is gone rather than shelved, and three criteria from it that were environment-independent (static resources resolved from the application file, version injection, and skipping the update check when the version is unset) were carried into the private deployment specification.

### Changed Files
- `scripts/deploy.py` -- New; one-command deployment with an atomic symlink switch.
- `scripts/bundle.py` -- `OPENVOCA_DATA_DIR` is a default; the directory used is the one created.
- `deploy/openvoca.service`, `deploy/openvoca.conf.example` -- New; systemd unit and optional overrides.
- `docs/DEPLOY.md` -- New; the deployment procedure.
- `docs/specs/private-deployment.md` -- New; 27 criteria. `docs/specs/deployment.md` removed.
- `backend/src/preflight.py`, `backend/src/services/schema_guard.py` -- New; startup checks.
- `backend/src/main.py` -- Startup path reporting, schema check, `register_spa()`, revision in health.
- `backend/src/services/word_store.py` -- `database_path()`.
- `backend/tests/` -- `test_private_deployment.py`, `test_deployment_atomicity.py`, `test_process_supervision.py` added; `test_static.py` rewritten to exercise the routes; `test_main.py` updated for the health response.
- `README.md` -- Self-hosting section.
- `VERSION`, `frontend/package.json`, `backend/pyproject.toml` -- Version bumped.

## v0.10.2

Date: 2026-09-17

### Added
- **A capability layer for touch and pointer input** -- The interface was designed for a mouse with a keyboard nearby, which made several controls unusable on a phone. `main.css` now defines the shared pieces once instead of leaving each component to reinvent them: `.tap-target` for controls that need a finger-sized box at every width, `.tap-finger` for controls that only need it under `@media (hover: none)` so pointer layouts keep their compact density, `.pointer-only` for affordances that have no meaning without a cursor, `.sheet-rise` for the bottom sheet animation, and `.dock-divide` to drop a dock's top border once the layout is wide enough that the dock no longer floats over content.
- **Bottom docks on the reading, settings and stats views** -- Primary navigation and page actions now live in a fixed bottom bar rather than a header. On a phone the top of the screen is the hardest place to reach and a header scrolls away, so every page keeps its controls under the thumb and within reach at all times.

### Fixed
- **Controls that were invisible or untappable on touch** -- The settings and vocabulary buttons used `opacity: 0` with a `group-hover:opacity-100` reveal. Touch devices never hover, so those controls were present but permanently invisible. The capability layer forces them visible when no pointer is available. Alongside that, nineteen controls across the composer, reading dock and definition panel were below the 44px minimum touch target; the reading dock and definition panel sized themselves for a cursor and were tapped without aiming.
- **Vocabulary statistics were unreadable on narrow screens** -- The table depended on a lemma column that collapsed to zero width at 390px, taking the word itself with it. The table is now a card list: the lemma sits on its own row with its action beside it, and the familiarity and cooldown figures wrap underneath. Cards also removed the horizontal scrolling the table needed. `statsLemma` is gone from the string table because the column header it labelled no longer exists.
- **The model settings overflowed on narrow screens** -- Three rows exceeded the viewport (the API key row, the custom header rows, and the zoom selector) because flex items will not shrink below their intrinsic width unless explicitly allowed to. Grid tracks and flex children now use `minmax(0, 1fr)` and `min-w-0`, the API key and header rows stack below 640px, and the header row's remove action becomes an icon button rather than forcing the row wider than the screen.
- **Definition lines ran together into a single line** -- The previous release introduced a wrapper element around the definition lines whose `display: flex` and `flex-direction: column` were declared inside `@media (hover: none)`. On desktop the wrapper was therefore not a flex container at all, so its inline children flowed together: several senses rendered as one unbroken string with no separation between the Chinese and English text. The stacking rules are now unconditional and only the height cap and scrolling remain touch-specific.
- **The reading settings panel covered the text it configured** -- A top panel that pushed the sentence down was replaced by a bottom sheet, so changing the font size or spacing no longer moves the text being adjusted.

### Changed
- **The reading view was redesigned for touch** -- The header is gone and the brand moved into the normal content flow, which returns that vertical space to the sentence. Reading controls, previously a row of icons in the header, are now a dock with the primary action separated from the secondary ones.
- **The composer controls gathered around the primary button** -- Settings and stats sit on one side, about and GitHub on the other, with the generate button between them, instead of the actions appearing above the button and the metadata below it. On wide screens the arrangement is a single row; below 640px it becomes two rows with the primary action on top. `ComposerCard` exposes `actions-before` and `actions-after` slots so the view can place them without the component knowing which controls exist.
- **The reading settings bar became a bottom sheet** -- Its three rows (font size, line spacing, theme) keep the label-left, control-right arrangement, and its buttons use the shared touch target.

### Changed Files
- `frontend/src/main.css` -- Capability layer: touch targets, sheet animation, dock divider.
- `frontend/src/views/HomeView.vue` -- Header removed, reading dock, brand in flow, bottom sheet wiring.
- `frontend/src/views/SettingsView.vue` -- Bottom dock, narrow-screen overflow fixes, icon remove action.
- `frontend/src/views/StatsView.vue` -- Table replaced by a card list, bottom dock.
- `frontend/src/components/ComposerCard.vue` -- `actions-before` / `actions-after` slots, touch sizing.
- `frontend/src/components/DefinitionToast.vue` -- Unconditional line stacking, touch sizing for its controls.
- `frontend/src/components/ReadingSettingsBar.vue` -- Top panel converted to a bottom sheet.
- `frontend/src/composables/useI18n.ts` -- `statsLemma` removed with the column header.
- `frontend/tests/StatsView.spec.ts`, `frontend/tests/App.spec.ts` -- Updated for the card list and dock layout.
- `VERSION`, `frontend/package.json`, `backend/pyproject.toml` -- Version bumped.

## v0.10.1

Date: 2026-09-14

### Fixed
- **Repository links pointed at the old name** -- The repository moved to `Maribbit/openvoca`, so every reference to the previous casing went through a redirect. The update check paid that hop on each startup, and package metadata advertised the stale name. All references and the git remote now use the canonical lowercase form.
- **Changelog extraction is now a script** -- Replaced the inline shell extraction with `scripts/extract_changelog.py`. Passing a tag whose section is missing now fails the job instead of publishing empty notes; the previous guard was added in v0.10.0, but the extraction itself still relied on an `awk` range whose end pattern also matched its start line, and on `head -n -1`, which is GNU-only and errors on macOS. Published notes no longer carry surrounding blank lines.

### Added
- **Release tooling test coverage** -- The release scripts ran without any tests, which is how nine consecutive releases came to be published with empty notes while CI reported success. `backend/tests/test_release_process.py` now covers changelog extraction, the repair tool's decision rules, and version consistency across the three version sources.
- **`scripts/sync_release_notes.py`** -- Repairs releases already published with empty notes, filling only empty bodies unless `--all` is passed. Its decision rules are factored out so they can be tested without a network.
- **`docs/specs/release-process.md`** -- Version consistency, release note extraction, and the repair tool as acceptance criteria.

### Changed
- **Version consistency is enforced** -- `RELEASE.md` required the three version sources to stay in sync, but nothing checked it, so a bump that missed one file would ship silently mislabelled artifacts. A test now fails when they disagree.
- **CI imports the release scripts via `pythonpath`** -- `backend/pyproject.toml` adds `../scripts` so the suite can import tooling that operates on the repository as a whole.

### Changed Files
- `scripts/extract_changelog.py` -- New; section extraction with explicit failure semantics.
- `scripts/sync_release_notes.py` -- New; `plan_updates()` factored out of `main()` for testability.
- `backend/tests/test_release_process.py` -- New; 25 tests covering both scripts and version consistency.
- `backend/pyproject.toml` -- `pythonpath` includes `../scripts`; version bumped.
- `docs/specs/release-process.md`, `docs/specs/README.md` -- New spec and index entry.
- `.github/workflows/ci.yml` -- Release job calls the extraction script.
- `VERSION`, `frontend/package.json` -- Version bumped.
- `backend/src/main.py`, `frontend/src/views/HomeView.vue`, `frontend/package.json`, `scripts/templates/`, `SECURITY.md` -- Canonical repository URL.

## v0.10.0

Date: 2026-09-13

### Breaking Changes
- **Provider API reshaped around key independence.** The API key is no longer part of the endpoint/model payload, because a single field carrying both a masked read value and a writable secret caused real data loss (see Fixed below). Clients must migrate:
  - `PUT /api/provider` now accepts `{endpoint, model, headers}` only.
  - `PUT /api/provider/key` sets the key; empty values are rejected with 422.
  - `DELETE /api/provider/key` clears it. This is the only way to unset.
  - `GET /api/provider` returns `apiKeySet` and `apiKeyHint` instead of `apiKey`.
  - `PUT /api/settings/provider` and `PUT /api/settings/provider/{key}` now return 403: provider configuration has a single write path that also rebuilds the active client.
  - `GET /api/settings` and `GET /api/settings/{namespace}` exclude `apiKey` and `headers` entirely.
  - `DELETE /api/settings` no longer clears the provider namespace, so resetting preferences cannot discard the model configuration.

### Added
- **Custom request headers for the model provider** -- Some OpenAI-compatible endpoints require extra headers to route requests. OpenCode Zen, for example, returns `400 MissingSessionID` without `x-opencode-session`, which reads like a credential or model problem rather than a missing header. Headers are configurable in a collapsible "Advanced" section, merged over the built-in ones so an explicitly configured header wins (enabling non-Bearer auth schemes), and applied to both streaming and non-streaming requests. Invalid names or values are rejected at write time: newline characters in a value would otherwise allow injecting additional headers.
- **Dedicated API key lifecycle** -- The key is now independent of the endpoint and model. When set, the field shows a read-only status with an irreversible hint; changing it requires clearing first. The hint is rendered as text rather than bound to an input, so a masked value can never be saved back as the real key.
- **`docs/specs/`** -- Specifications became the entry point for development, with stable acceptance criteria IDs and inline test traceability.
- **Deferred criteria tracking** -- `docs/specs/deferred.txt` records criteria that are specified but not yet implemented. The traceability gate distinguishes "planned, not built" from "built, but the test went missing", and rejects entries that already have tests so the list cannot rot.

### Fixed
- **Streaming generation silently truncated** -- `generate_completion_stream` indexed `choices[0]` without checking for an empty array. Providers that emit a usage-only tail chunk (`{"choices": [], ...}`) before `[DONE]` triggered an `IndexError` that was not caught, so the response ended with neither a `complete` nor an `error` event and the interface waited forever. The frontend showed a stalled word count with no error. Ollama never emitted such a chunk, which is why this went unnoticed.
- **Failed streams now always report** -- An unexpected exception mid-stream produced no terminal event at all. Any failure now yields an `error` event, so a stalled generation can no longer pass for a slow one.
- **API key lost when editing the model** -- Changing the endpoint or model wiped the in-memory key while the database kept it, so requests failed until a restart appeared to restore it. An empty value meant "do not change" to one code path and "set to empty" to another.
- **Database files were world-readable** -- The database stores the API key and custom headers, which may carry session credentials. The file was created with the default umask, leaving it readable by other users on the same machine, and its SQLite sidecars (`-journal`, `-wal`, `-shm`) shared the exposure. Files are now restricted to the owner, and databases created by earlier versions are tightened on startup.
- **Frontend caches could hold session headers** -- The settings cache, export and import skipped only the API key. Custom headers, which can carry session credentials, reached `localStorage` and exported JSON files. The sensitive-key list is now defined once and shared by all three paths.
- **Cross-platform launch configuration** -- The documented dev command (`fastapi dev src/main.py`) failed outside Windows with `ModuleNotFoundError: No module named 'src'`, and the VS Code launch configuration hard-coded a Windows interpreter path. The package now has explicit `__init__.py` files, the interpreter is resolved per platform, and development tasks are available for both servers.
- **Release notes were published empty** -- The release job extracted the changelog with an `awk` range pattern whose start and end both matched the version heading, so the range covered only that one line and the following `head -n -1` removed it, leaving a zero-byte file. Nine consecutive releases shipped with no release notes. The extraction now captures the section body explicitly and fails the job when a section is missing, instead of publishing empty notes.

### Changed
- **Specs-first workflow enforced** -- AI coding guidelines now require reading acceptance criteria before writing tests or code, and mandate inline `Covers:` annotations on new tests.
- **Traceability checker rewritten** -- Reports deferred criteria separately, validates that every deferred entry exists and is still unimplemented, and prints actionable guidance.
- **CI now runs the full local check set** -- `ruff format --check`, `ruff check` and the traceability gate previously ran only on developer machines, so lint drift and untraced work could reach `main` unflagged. Both are now enforced in CI, and the bundle job depends on the traceability result.

### Changed Files
- `backend/src/integrations/openai_compat.py` -- `extra_headers` support, header merge order, empty-`choices` tolerance.
- `backend/src/main.py` -- Provider write paths, `_reload_provider()`, header validation and persistence, stream error reporting.
- `backend/src/services/settings_store.py` -- `PROTECTED_NAMESPACES`, `delete_setting()`, protected-namespace-aware clear.
- `backend/src/services/word_store.py` -- Restrictive umask and `_restrict_db_permissions()`.
- `backend/tests/test_provider_config.py`, `backend/tests/test_openai_compat.py`, `backend/tests/test_main.py`, `backend/tests/test_word_store.py` -- Coverage for the above.
- `frontend/src/api/settings.ts`, `frontend/src/views/SettingsView.vue`, `frontend/src/composables/useI18n.ts` -- Key lifecycle, header editing.
- `frontend/src/composables/useSettings.ts` -- Shared sensitive-key list.
- `frontend/tests/SettingsView.spec.ts`, `frontend/tests/useSettings.spec.ts` -- Coverage for the above.
- `docs/specs/` -- New specs, deferred list, and index corrections.
- `scripts/check_traceability.py` -- Deferred-aware rewrite.
- `.vscode/`, `backend/README.md` -- Cross-platform interpreter, launch and task configuration.

## v0.9.9

Date: 2026-05-09

### Fixed
- **Reading route persistence** -- Navigating from Reading to Settings or Stats and back now preserves the current generated sentence instead of resetting to the Composer.
- **Live language/settings refresh** -- Cached Reading state now refreshes visible copy and reading display settings when returning from Settings, without accidentally saving route-activation defaults.
- **Stats editing clarity** -- The destructive delete action has moved out of the active edit action cluster and into the expanded row details as a labeled danger action.
- **Stats numeric alignment** -- Familiarity and cooldown columns now use fixed centered columns and text-mode numeric inputs so values stay aligned with headers and do not shift during editing.

### Changed
- **Settings and Stats navigation** -- The top headers are now sticky, slimmer, and separated from scrolled content with a subtle divider so Back to Reading remains available on long pages.

### Changed Files
- `frontend/src/App.vue` -- Cached `HomeView` with Vue `KeepAlive`.
- `frontend/src/views/HomeView.vue` -- Paused route-specific global listeners while cached/inactive and refreshed reading UI state on activation.
- `frontend/src/composables/useI18n.ts` -- Made locale resolution reactive to the shared settings store.
- `frontend/src/composables/useSettings.ts` -- Preloaded the local settings cache before first render so cached views initialize from persisted settings.
- `frontend/src/views/SettingsView.vue` -- Added the compact sticky header treatment.
- `frontend/src/views/StatsView.vue` -- Added the compact sticky header, moved delete into expanded details, and aligned numeric columns/inputs.
- `frontend/tests/App.spec.ts` -- Added route persistence and language refresh coverage.
- `frontend/tests/StatsView.spec.ts` -- Added Stats editing and numeric alignment coverage.

## v0.9.8

Date: 2026-05-09

### Added
- **Current-sentence lemma correction fallback** -- Users can correct the lemma used for dictionary lookup and feedback before submitting progress. The correction is available from the Definition Toast and Progress Summary Modal, applies only to the current sentence, and is not persisted as a global alias.
- **Color system guidance** -- Added frontend color-token guidance to reduce light/dark and palette regressions.

### Changed
- **Definition Toast lemma display polished** -- The lemma label is localized (`lemma` / `词元`), hyphenated lemmas such as `state-of-the-art` are accepted, and duplicate word/lemma rows are avoided when both values match.
- **Progress Summary Modal theme colors fixed** -- Level-delta badges and modal borders now use theme-aware ink/surface tokens instead of hard-coded dark gray colors.
- **Review Progress button refined** -- The reading-page summary button now sits closer to the sentence, uses a subtler theme-tinted neutral fill, and only shows shadow on hover.

### Changed Files
- `frontend/src/composables/useLemmaOverrides.ts` -- Added the current-sentence lemma override mechanism.
- `frontend/src/views/HomeView.vue` -- Routed dictionary lookup, draft feedback, and final submit through corrected lemmas; refined Review Progress spacing and button styling.
- `frontend/src/components/DefinitionToast.vue` -- Added lemma editing, localized lemma display, and duplicate display suppression.
- `frontend/src/components/ProgressSummaryModal.vue` -- Added lemma editing and theme-aware level-delta styling.
- `frontend/src/composables/useI18n.ts` -- Added lemma correction labels in English and Chinese.
- `frontend/tests/` -- Added and expanded coverage for lemma overrides, toast editing, modal editing, and corrected feedback submission.
- `frontend/README.md` -- Documented frontend color-system usage rules.
- `design/Implementation.md`, `design/UI_Design.md`, `design/Algorithm.md` -- Documented the simplified non-persistent lemma correction fallback design.

## v0.9.7

Date: 2026-05-02

### Added
- **`POST /api/feedback/draft` endpoint** -- Simulates user feedback to calculate accurate vocabulary level changes without mutating the database.

### Changed
- **Replaced Hold-to-Submit with Progress Summary Modal** -- Reading interaction has been simplified. Instead of holding the "Continue" button, tapping "Continue" (or Spacebar) now opens a modal showing precise vocabulary transitions.
- **Feedback processing refactored** -- The backend `apply_feedback` logic now completely wraps around the simulation output of `draft_feedback`, ensuring mathematical consistency.
- **Empty state improved** -- If a sentence has no vocabulary updates during the feedback draft, the Progress Summary modal cleanly handles the empty state and asks for user confirmation.
- **Loading UI for Async Events** -- Every single asynchronous interaction on the frontend (Sentence generating, Target Word suggestion loading, definition fetching, Progress Summary calculating, and File parsing on the Stats View) now comes with responsive `animate-spin` Tailwind loaders to significantly improve perceived usability overhead during delays.
- **Stats View Edit Workflow Overhaul** -- Eliminated chaotic direct-input lists making numbers too easy to misclick. Added row-level specific toggle workflows with precise "Edit Row/Done Editing" and better icon layouts.
- **Deleted Icon overhaul** -- Replaced vague "X" interface delete marker across Stats View with a standard clear trash-can icon specifically bound to active edit rows. Visibiliy on dark mode updated to pass contrast limits.
- **Legacy copy removed** -- Renamed `nextSentenceHint` to `reviewProgressBtn` and updated translations for "Review Progress". Fixed 'new' word UI display state.

### Changed Files
- `backend/src/services/word_store.py` -- `draft_feedback` added; `apply_feedback` refactored to reuse it.
- `backend/src/main.py` -- Added `submit_feedback_draft` route.
- `backend/tests/test_word_store.py` -- Added explicit tests for untouched and manipulated word targets.
- `frontend/src/api/reading.ts` -- Upgraded to support `LevelDelta` payload fetching.
- `frontend/src/views/HomeView.vue` -- Refactored manual level-up prediction into strict backend draft mapping. Remove manual logic skip filters.
- `frontend/src/components/ProgressSummaryModal.vue` -- Exact transitions, robust `NEW` state, and added empty state.
- `frontend/src/composables/useI18n.ts` -- Added `progressEmpty` translation. Removed legacy `releaseHint`.
- `frontend/src/components/HoldButton.vue` -- Removed.

## v0.9.6

Date: 2026-04-19

### Breaking Changes
- **POS removed from word store** -- The `pos` field has been completely removed from `WordRecord`. The primary key is now the lemma alone. All API routes, request/response models, CSV export/import, and the frontend have been updated accordingly. Legacy CSV files with a `pos` column are still accepted on import (the column is silently ignored).

### Changed
- **API routes simplified** -- `PATCH /api/vocabulary/{lemma}/{pos}` → `PATCH /api/vocabulary/{lemma}`; `DELETE /api/vocabulary/{lemma}/{pos}` → `DELETE /api/vocabulary/{lemma}`.
- **Feedback payload simplified** -- `FeedbackRequest.targetWords` and `markedWords` changed from `WordPosEntry[]` objects (lemma + pos) to plain `string[]` of lemmas.
- **CSV export** -- The `pos` column is no longer exported. New column order: `lemma,level,cooldown,first_seen,last_seen,last_context,seen_count`.
- **CSV import** -- Only `lemma` is required. The `pos` column is accepted but ignored for backward compatibility with v0.9.5 exports.
- **Stats view** -- POS column removed from vocabulary table.
- **pick_target_words** -- With lemma as the sole PK, the deduplication loop is replaced by a direct `.limit()` query.

### Changed Files
- `backend/src/services/word_store.py` -- `WordRecord.pos` removed; `_find_record()` removed; `apply_feedback()`, `update_word_record()`, `delete_word_record()`, `import_vocabulary()` simplified to lemma-only.
- `backend/src/main.py` -- `WordPosEntry` model removed; `FeedbackRequest` uses `list[str]`; `WordRecordOut` drops `pos`; routes use `/{lemma}` instead of `/{lemma}/{pos}`; CSV export drops `pos` column.
- `frontend/src/api/reading.ts` -- `WordPosEntry` removed; `FeedbackRequest` and `WordRecordOut` simplified.
- `frontend/src/views/HomeView.vue` -- Feedback construction simplified to lemma strings.
- `frontend/src/views/StatsView.vue` -- POS column and `wordKey()` helper removed.
- `frontend/src/composables/useI18n.ts` -- `pos` removed from i18n type and all translation maps.
- `backend/tests/test_algorithm.py` -- All tests updated to use lemma strings instead of `(lemma, pos)` tuples. POS-specific tests removed.
- `backend/tests/test_word_store.py` -- All tests updated: `apply_feedback` calls use `list[str]`; `update_word_record`/`delete_word_record` drop `pos`; import tests use lemma-only rows with legacy pos backward-compat test.
- `backend/tests/test_main.py` -- API tests updated: feedback payloads use `string[]`; routes use `/{lemma}`; CSV assertions match new column layout; legacy pos CSV import test added.

---

## v0.9.5

Date: 2026-04-19

### Bug Fixes
- **Lazy-load spaCy model** -- The spaCy NLP model (`en_core_web_sm`) is now loaded on first sentence generation instead of at module import time. This allows the `/api/health` endpoint to respond immediately on startup, preventing the bundled launcher from timing out on cold first launches.
- **Favicon served in bundled mode** -- The SPA catch-all route now checks whether a requested file exists in the frontend dist directory before falling back to `index.html`. Fixes the missing favicon in bundled browser tabs.
- **Target words lemma mismatch safety net** -- When the LLM uses a derived form (e.g. "analysis" instead of the target "analyze"), the tokenizer may not match it back to the original DB record, causing the word to never advance and be picked indefinitely. Feedback now includes `originalTargets` (the raw lemmas from `pick_target_words`), and `apply_feedback` ensures every originally-picked word advances unless the user explicitly marked it unknown.

### Changed
- **Test file split** -- Extracted SRS algorithm tests (level progression, cooldown queue, POS matching, pick logic, full simulation, and original_targets safety net) from `test_word_store.py` into a dedicated `test_algorithm.py`.

### Changed Files
- `backend/src/services/tokenizer.py` -- `spacy.load()` moved from module scope to lazy `_get_nlp()` helper.
- `backend/src/main.py` -- SPA fallback checks for real files before serving `index.html`; `FeedbackRequest` model gains optional `originalTargets` field; `submit_feedback` passes it through.
- `backend/src/services/word_store.py` -- `apply_feedback()` accepts `original_targets: list[str]`; safety-net loop ensures unmatched picked words still advance.
- `frontend/src/api/reading.ts` -- `FeedbackRequest` interface gains optional `originalTargets` field.
- `frontend/src/views/HomeView.vue` -- Stores `response.words` and sends them as `originalTargets` in feedback.
- `backend/tests/test_algorithm.py` -- New file: 15 algorithm-focused tests extracted from `test_word_store.py` plus 3 new `original_targets` tests.
- `backend/tests/test_word_store.py` -- Trimmed to 33 CRUD / metadata / import tests.

---

## v0.9.4

Date: 2026-04-18

### New Features
- **OV monogram logo** -- New brand identity: a warm cream rounded-square containing a dark ink circle with the letter V cut through as negative space. Added as `logo.svg` and replaced the Vite-template favicon.
- **Bundle README files** -- Every distributable archive now ships a platform-specific `README.txt` and `README.zh-CN.txt` generated from templates in `scripts/templates/`. Covers quick start, first-time LLM setup, usage, data location, and support links.

### Changed
- **DefinitionToast repositioned** -- The word-definition panel now slides up from the bottom of the screen (`bottom-4`) instead of dropping from the top, reducing overlap with reading text.
- **About modal: How It Works section** -- The About modal (click "OpenVoca" in the header) now includes a "How It Works" walkthrough. The separate first-run onboarding modal idea was merged here so users can revisit the guide at any time.
- **README headers** -- Both `README.md` and `README.zh-CN.md` redesigned: centred logo (140 px), centred title and tagline.
- **Bundle script improvements** -- `edge_tts` added to the import-verification list so a missing TTS dependency is caught at package time.

### Changed Files
- `logo.svg` -- New OV monogram logo (new file).
- `demo.gif` -- Demo recording for README (new file).
- `frontend/public/favicon.svg` -- Replaced with OV monogram.
- `frontend/src/components/DefinitionToast.vue` -- `top-4` → `bottom-4`; transition direction reversed.
- `frontend/src/views/HomeView.vue` -- About modal expanded with How It Works steps; OnboardingModal removed.
- `frontend/src/composables/useI18n.ts` -- Added `howItWorks` and `onboardingStep*` keys (EN + ZH).
- `README.md`, `README.zh-CN.md` -- New centred header; Download and Building from Source sections.
- `scripts/bundle.py` -- README template loading; `edge_tts` added to import check.
- `scripts/templates/` -- Four new README template files (EN + ZH × Windows + Unix).

---

## v0.9.3

Date: 2026-04-15

### Changed
- **Level-based SRS model** -- Replaced raw interval values with a level exponent (1--6). Actual cooldown = 2^level generations. Simplifies the data model and makes the algorithm easier to reason about.
- **Stats display overhaul** -- Familiarity column now shows a plain integer input (1--6) instead of a progress bar with +/- buttons. Matches the cooldown column's editable-number style.
- **Algorithm hint in Stats** -- Sort toolbar shows a brief explanation: "Each level doubles the cooldown: 2, 4, 8, 16, 32, 64".

### Changed Files
- `backend/src/services/word_store.py` -- `interval` field renamed to `level`; constants `INTERVAL_BASE`/`INTERVAL_MAX` replaced with `LEVEL_MIN`/`LEVEL_MAX`/`LEVEL_BASE`; algorithm functions updated.
- `backend/src/main.py` -- Pydantic response/update models use `level` instead of `interval`.
- `backend/tests/test_main.py`, `backend/tests/test_word_store.py` -- Tests updated for level-based model.
- `frontend/src/api/reading.ts` -- TypeScript `WordRecordOut.interval` renamed to `.level`.
- `frontend/src/views/StatsView.vue` -- Integer input for familiarity; removed progress bar, +/- buttons, and helper functions. Added algorithm hint in sort bar.
- `frontend/src/composables/useI18n.ts` -- Added `statsIntervalTip` key; removed dead `intervalHalve`/`intervalDouble` keys.

---

## v0.9.2

Date: 2026-04-14

### New Features
- **Edge TTS read-aloud** -- Sentence read-aloud now uses Microsoft Edge TTS (`edge-tts`) for natural, neural-quality speech. Falls back to browser `SpeechSynthesis` when Edge TTS is unavailable. Three-state button (idle / loading / playing) with progressive streaming playback.
- **Word pronunciation** -- Speaker button in the definition toast lets users hear individual words via Edge TTS (with browser fallback). Available for both found and not-found dictionary entries.
- **TTS voice listing endpoint** -- `GET /api/tts/voices?locale=en` returns available Edge TTS voices filtered by locale.

### Changed Files
- `backend/pyproject.toml` -- Added `edge-tts>=6.1.26` dependency.
- `backend/src/main.py` -- New `GET /api/tts` and `GET /api/tts/voices` endpoints.
- `frontend/src/views/HomeView.vue` -- Sentence read-aloud with Edge TTS, 3-state button, browser fallback.
- `frontend/src/components/DefinitionToast.vue` -- Added word pronunciation button with Edge TTS + browser fallback.
- `frontend/src/api/reading.ts` -- Added `fetchTtsAudio()` helper.
- `frontend/src/composables/useI18n.ts` -- Added `pronounceWord` i18n key.

---

## v0.9.1

Date: 2026-04-13

### New Features
- **Streaming sentence generation** -- New SSE endpoint `POST /api/reading-sentence/next/stream` streams progress events during LLM generation. The frontend now shows a live elapsed timer ("3s") while waiting for the model, then switches to a word counter ("12 words") as tokens arrive.
- **Update check** -- Background version check against GitHub Releases on startup; dismissible banner in the UI when a newer version is available.

### Bug Fixes
- **Double-s lemma correction** -- Fixed spaCy's statistical lemmatizer spuriously de-pluralizing words ending in double-s (e.g. "fiberglass" → "fiberglas", "compass" → "compas"). A lightweight heuristic in the tokenizer now preserves the correct form.

### Changed Files
- `backend/src/integrations/openai_compat.py` -- Added `generate_completion_stream()` async generator for SSE streaming.
- `backend/src/integrations/provider.py` -- `LLMProvider` protocol now includes `generate_completion_stream()`.
- `backend/src/main.py` -- New `POST /api/reading-sentence/next/stream` SSE endpoint.
- `backend/src/services/tokenizer.py` -- Double-s lemma heuristic fix.
- `frontend/src/api/reading.ts` -- Added `fetchNextReadingSentenceStream()` with progress callbacks.
- `frontend/src/components/SentenceDisplay.vue` -- New `loadingProgress` prop for live progress display.
- `frontend/src/views/HomeView.vue` -- Elapsed timer + streaming word count during generation.
- `frontend/src/composables/useI18n.ts` -- Added `wordSingular`, `wordPlural` i18n keys.

---

## v0.9.0

Date: 2026-04-12

### New Features
- **Cross-platform bundle script** -- `scripts/bundle.py` now auto-detects the host platform (Windows/macOS/Linux), produces `.zip` on Windows and `.tar.gz` on Unix, and uses platform-appropriate Python paths.
- **CI release pipeline** -- Pushing a `v*` tag triggers a 3-platform build matrix (Windows x64, macOS arm64, Linux x64) and creates a GitHub Release with all bundle artifacts attached.
- **macOS quarantine helper** -- macOS/Linux bundles include `run.sh`, which strips the Gatekeeper quarantine attribute before launching, so users don't need to run `xattr` manually.

### Improvements
- **Script-based launchers** -- `openvoca.bat` (Windows) and `run.sh` (macOS/Linux) as simple, signing-free entry points. `start.py` is cross-platform.
- **CI restructured** -- Tests (frontend, backend) run on every push/PR. Bundle + Release jobs run only on `v*` tags to conserve CI minutes.

### Changed Files
- `scripts/bundle.py` -- Rewritten as 7-step cross-platform pipeline with `.bat`/`.sh` entry points.
- `.github/workflows/ci.yml` -- 4 jobs: frontend, backend, bundle (3 platforms, tags only), release (creates GitHub Release).
- `.vscode/tasks.json` -- "Check All" depends on Backend and Frontend.
- `RELEASE.md` -- Updated with automated workflow documentation.

---

## v0.8.0

Date: 2026-04-12

### New Features
- **`first_seen` and `seen_count` fields** — Each word record now tracks when the word was first encountered as a target word (`first_seen`) and how many times it has appeared as a target word (`seen_count`). Both fields are shown in the Stats page expanded row and included in CSV export/import.
- **OpenVoca branding in Composer** — The app title "OpenVoca" now appears in the header center when the Composer is active. GitHub and About icons are shown below the Composer card.
- **About modal** — Clicking the info icon opens a compact overlay with the app tagline, description, version number, and GitHub link. Version is read from the `VERSION` file at build time.
- **Chinese README** — Added `README.zh-CN.md` with a language toggle link at the top of both READMEs.

### Bug Fixes
- **Theme sync across pages** — Fixed a bug where navigating directly to the Stats page would show light mode even when dark mode was set. The reading theme (`data-theme`) is now applied centrally in `App.vue` on mount, ensuring consistency regardless of entry route.
- **Settings gear hidden in Composer** — The reading display settings icon is now hidden when the Composer is open, since reading settings don't apply to the Composer state. The settings panel auto-closes when switching to Composer.

### Improvements
- **Renamed theme attributes** — `data-reading-theme` → `data-theme`, `data-color-theme` → `data-palette` for clarity.
- **README rewritten** — Added a "What is OpenVoca?" section with a plain-language explanation of the core workflow for first-time visitors. Moved bundling details into the script comments.
- **Package metadata** — Updated `pyproject.toml` and `package.json` with proper descriptions, license, and repository URLs. Fixed `index.html` title to "OpenVoca" and added a meta description tag.
- **Open-source readiness** — Added GitHub issue templates (bug report, feature request), pull request template, CODE_OF_CONDUCT.md, and SECURITY.md.
- **Gitee mirror instructions** — Added a Gitee Mirror section to CONTRIBUTING.md with setup steps.

### Changed Files
- `backend/src/services/word_store.py`: `WordRecord` gains `first_seen` and `seen_count`; `apply_feedback` and `import_vocabulary` updated.
- `backend/src/main.py`: `WordRecordOut` gains `firstSeen` and `seenCount`; export CSV is now 8 columns.
- `frontend/src/App.vue`: centralized `data-theme` application on mount.
- `frontend/src/views/HomeView.vue`: branding elements, About modal, settings gear hidden in Composer.
- `frontend/src/views/StatsView.vue`: expanded row shows `firstSeen` and `seenCount`.
- `frontend/src/composables/useI18n.ts`: new keys for `firstSeenLabel`, `seenCountLabel`, `aboutOpenVoca`, `aboutTagline`, `aboutDescription`.
- `frontend/src/main.css`: renamed `data-reading-theme` → `data-theme`, `data-color-theme` → `data-palette`.
- `frontend/vite.config.ts`, `frontend/vitest.config.ts`: inject `__APP_VERSION__` from VERSION file.
- `README.md`, `README.zh-CN.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`: new or updated.
- `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`: new.
- `backend/pyproject.toml`, `frontend/package.json`, `frontend/index.html`: metadata fixes.

---

## v0.7.7

Date: 2026-04-12

### New Features
- **`first_seen` timestamp** — Each word record now stores when the word was first encountered as a target word. Shown in the expanded row on the Stats page as "First seen: X days ago".
- **`seen_count` counter** — Each word record now tallies how many times the word has appeared as a target word (selected by the pick algorithm). Shown in the expanded row as "Seen: N×".

### Improvements
- **Stats page expanded row** — Clicking a word now reveals four details: Last seen, First seen, Seen count, and Last context.
- **Export/import roundtrip** — CSV export now includes `first_seen` and `seen_count` columns. Import treats both as optional (defaults: `first_seen=now`, `seen_count=0`).

### Changed Files
- `backend/src/services/word_store.py`: `WordRecord` gains `first_seen` (datetime) and `seen_count` (int ≥ 0); `apply_feedback` sets `first_seen` on creation only and always increments `seen_count`; `import_vocabulary` handles both new optional columns.
- `backend/src/main.py`: `WordRecordOut` gains `firstSeen` and `seenCount`; export CSV is now 8 columns.
- `frontend/src/api/reading.ts`: `WordRecordOut` interface adds `firstSeen?` and `seenCount?`.
- `frontend/src/views/StatsView.vue`: expanded row shows `firstSeen` and `seenCount`.
- `frontend/src/composables/useI18n.ts`: new keys `firstSeenLabel` and `seenCountLabel` (EN + ZH).
- `backend/tests/test_word_store.py`: 2 new tests (`test_apply_feedback_sets_first_seen_once`, `test_apply_feedback_increments_seen_count`).
- `backend/tests/test_main.py`: export header and roundtrip tests updated for 8-column CSV.

---

## v0.7.6

Date: 2026-04-12

### New Features
- **Import settings** — Restore settings from a previously exported JSON file on the Settings → Data page. API key is excluded from both export and import for security.
- **Import vocabulary link on Settings page** — A "Go to Vocabulary →" shortcut in the Data section links to the Stats page for CSV import.

### Security
- **API key excluded from localStorage** — `provider.apiKey` is no longer cached in `localStorage`; it only lives in the backend SQLite DB and in-memory at runtime.
- **API key excluded from settings export** — Exported JSON files never contain the raw API key.

### Bug Fixes
- **BOM-aware CSV import** — CSV files with a UTF-8 BOM (common from Excel on Windows) are now parsed correctly instead of failing with "missing columns".
- **Consistent import banner styling** — Overwrite re-import no longer shows a red error banner on partial success.

### Improvements
- **Danger zone backup hints** — Clear Vocabulary and Reset Settings confirmation dialogs now remind users to export a backup first.
- **Full roundtrip fidelity** — Export/import roundtrip now preserves `last_seen` timestamps (verified by test).

### Changed Files
- `backend/src/main.py`: BOM-safe UTF-8 decoding (`utf-8-sig`), export includes `last_seen`/`last_context`.
- `frontend/src/composables/useSettings.ts`: `importAll()`, `exportAll()` and `saveCache()` strip `provider.apiKey`.
- `frontend/src/views/SettingsView.vue`: import settings UI, import vocabulary link, `onSettingsFileSelected()` handler.
- `frontend/src/views/StatsView.vue`: consistent `importError` flag on reimport.
- `frontend/src/composables/useI18n.ts`: new keys for import settings, import vocabulary link, danger zone hints.
- `frontend/tests/useSettings.spec.ts`: 6 new tests for export/import settings.
- `backend/tests/test_main.py`: BOM test, `last_seen` roundtrip assertion, minimal CSV test.

---

## v0.7.5

Date: 2026-04-12

### Improvements
- **Export now includes `last_seen` and `last_context`** — CSV export outputs all 6 fields for complete backup and lossless roundtrip.
- **Import accepts minimal CSV** — Only `lemma` and `pos` columns are required. `interval`, `cooldown`, `last_seen`, and `last_context` are all optional with sensible defaults (interval=2, cooldown=0, last_seen=now, last_context=null).
- **Danger zone backup hint** — Clear Vocabulary and Reset Settings confirmation dialogs now remind users they can export a backup first.

### Changed Files
- `backend/src/main.py`: export endpoint outputs 6-column CSV.
- `backend/src/services/word_store.py`: import only requires `lemma`+`pos`; optional columns parsed with defaults.
- `frontend/src/composables/useI18n.ts`: updated confirmation messages; removed unused `importModeSkip` key.
- `backend/tests/`: 5 new import tests (minimal CSV, last_seen/last_context, bad date, overwrite context, endpoint minimal).

---

## v0.7.4

Date: 2026-04-12

### New Features
- **Vocabulary import** — Import vocabulary from a CSV file via the Stats page. The endpoint accepts the same four-column format (`lemma`, `pos`, `interval`, `cooldown`) used by export, with row-level validation, case normalization, value clamping, and a 5 000-row / 1 MB limit.
- **Import mode (skip / overwrite)** — By default, importing preserves existing learning progress (skip mode). When existing words are detected, a contextual "Overwrite" button appears in the result banner, letting users re-import with overwrite mode without selecting the file again.
- **External dictionary links** — DefinitionToast now shows quick links to Merriam-Webster, Cambridge, and Youdao below the definition for further lookup.

### Improvements
- **i18n for import messages** — All import result messages (success, partial, failure) are fully localized in English and Chinese.

### Changed Files
- `backend/src/main.py`: new `POST /api/vocabulary/import` endpoint (multipart CSV + `mode` form field).
- `backend/src/services/word_store.py`: `ImportResult` dataclass, `import_vocabulary()` with skip/overwrite mode.
- `frontend/src/api/reading.ts`: `importVocabulary(file, mode)` API helper.
- `frontend/src/views/StatsView.vue`: import button, file input, result banner with contextual overwrite action.
- `frontend/src/components/DefinitionToast.vue`: external dictionary links (MW, Cambridge, Youdao).
- `frontend/src/composables/useI18n.ts`: new i18n keys for import-related messages.
- `backend/tests/test_word_store.py`, `backend/tests/test_main.py`: 19 new import tests.

---

## v0.7.3

Date: 2026-04-11

### Bug Fixes
- **Firefox line-wrap fix** — Sentences no longer overflow horizontally in Firefox. Two root causes were addressed:
  1. Vue's template compiler (condensed whitespace mode) was stripping the space text node inside `<span> </span>`, leaving no line-break opportunities between word spans. The space is now rendered via `{{ ' ' }}` mustache interpolation inside a `<template>` element, which compiles to `createTextVNode(' ')` unconditionally.
  2. The `<article>` flex item had `min-width: auto` (the flex default), which resolved to the sentence's full one-line width because each word span carries `whitespace-nowrap`. Added `min-w-0` to allow the flex item to shrink and text to wrap.

### Other
- **`.gitignore`** — Added `build/` and `dist/` entries (bundle script output directories were previously untracked).
- **README** — New "Building a Release Package (Windows)" section documents prerequisites, the `uv run python scripts/bundle.py` command, the 8-step build process, and a note on automatic dependency management via `uv.lock`.

### Changed Files
- `frontend/src/components/SentenceDisplay.vue`: space span replaced with `<template>{{ ' ' }}</template>`; `min-w-0` added to `<article>`.
- `.gitignore`: added `build/` and `dist/`.
- `README.md`: added build instructions section.

---

## v0.7.2

Date: 2026-04-12

### Highlights
- **First-run experience** — Generation failures no longer strand the user on a blank reading view. The Composer stays visible and an inline error banner with a direct "Go to Settings →" link appears below the card.
- **Target Words redesign** — Suggestion chips (from vocabulary) are now toggleable (click to deselect/reselect) and never permanently destroyed. User-typed custom words are visually distinct (lighter fill + ×). A ↺ refresh button lets users fetch a fresh pool without reloading the page.
- **Word Picking settings split** — The single "Words Per Sentence" slider is now two linked sliders: **Suggestion Pool** (how many chips appear, 1–6) and **Auto-selected** (how many start pre-selected, 0–pool). Reducing the pool automatically clamps the auto-select value.
- **Language detection fixed** — A stale legacy `localStorage` key (`openvoca.ui.locale`) was shadowing `navigator.language` after clearing settings. The legacy key has been removed entirely; locale now persists exclusively through the settings store.
- **UI language order** — English moved to the left in the language picker (Settings → Interface). Dictionary display order changed to EN | Both | 中文.
- **Smart dictionary default** — First-run default for definition language is now browser-detection-aware: **EN** for non-Chinese browsers, **Both** for Chinese browsers (applies to Settings picker and the reading view).

### Frontend
- `HomeView.vue`: on generation error, `showComposer` is reverted to `true`; new `composerError` ref drives an inline error banner below `ComposerCard` with a `router-link` to `/settings`.
- `ComposerCard.vue`:
  - Data model split into `suggestedWords`, `activeSuggestions` (Set), and `customWords`. `effectiveTargetWords` computed combines active suggestions + custom words.
  - `loadTargetWords()` now reads `generation.suggestionPoolSize` (pool fetch count) and `generation.targetWordCount` (auto-select count separately) — first `autoSelect` fetched words are pre-activated.
  - Template: suggestion chips use new `.suggestion-chip.active/.inactive` styles (toggleable, no × button); custom chips use `.custom-chip` (lighter fill, × to remove); refresh button replaces the hint text in the header.
  - Scoped CSS updated: `.word-chip` removed, `.suggestion-chip` and `.custom-chip` added.
- `SettingsView.vue`:
  - Added `draftSuggestionPoolSize` ref (reads `generation.suggestionPoolSize`, default 3).
  - Word Picking section replaced with two sliders; auto-select slider `max` is bound to pool size; pool-change watch clamps auto-select.
  - Language picker: English button moved left.
  - Dictionary display order changed to EN | Both | 中文; default now inferred from `navigator.language`.
- `useI18n.ts`:
  - Removed legacy `STORAGE_KEY` constant and all `localStorage.setItem/getItem` calls for locale — persistence is now via settings store only.
  - `targetWordCount` label/hint updated to describe auto-select semantics.
  - Added `suggestionPoolSize` / `suggestionPoolSizeHint` keys.
  - Added `goToSettings` key ("Go to Settings →" / "前往设置 →").
  - Renamed `composerTargetWordsHint` → `composerRefreshSuggestions`.
- `HomeView.vue`: `dictionaryDisplayMode` default changed from hardcoded `"both"` to browser-language-aware detection.
- Tests: locale-persistence test updated to assert via `openvoca.settings.cache` instead of deleted `openvoca.ui.locale` key.

### Design
- `ui_guide_composer_light.html` and `ui_guide_composer_dark.html`: Target Words section updated to show two-zone chip design (toggleable suggestions + custom chips with ×, ↺ refresh button).

---

## v0.7.1

Date: 2026-04-11

### Highlights
- **Static file serving fix** — `GET /` now serves the Vue SPA (`index.html`) in production. The health check was renamed to `GET /api/health` so routing no longer conflicts.
- **Composer UI polish** — Section dividers removed (spacing-only rhythm), scenario card background unified, and the scenario supplement textarea replaced with a `+ Add details` expand button, preserving access while keeping the default view clean.
- **Fake News prompt revised** — Removed disaster-biased language (`crisis`, `breaking news`); now explicitly lists diverse beats (science, culture, sports, weather, economics) for varied output.

### Backend
- `main.py`: health endpoint moved from `GET /` to `GET /api/health`. Added `GET /` (`serve_root`) to the SPA section so the root URL serves the frontend.
- `test_main.py`: `test_read_root` renamed to `test_health_endpoint`, path updated to `/api/health`.

### Frontend
- `ComposerCard.vue`:
  - Section `border-t` dividers removed; card spacing increased to `space-y-6`.
  - Scenario cards background changed from `paper` to `surface` (matches option-cards in Difficulty/Length).
  - Supplement textarea replaced with `+ 添加细节` expand button for preset scenarios; textarea auto-shows for "自定义" or when the user has existing content. Scenario switching resets the open state when content is empty.
  - `absurd_headlines` prompt revised: removed `crisis` / `breaking news`; added explicit beat list (`local news, science, culture, sports, weather, economics`).
  - Poetry scenario emoji changed `✏️` → `📜`; "无预设" renamed to "自定义" / "No Preset" → "Custom".
- `useI18n.ts`: added `composerAddDetails` key (`"Add details"` / `"添加细节"`).

### Design
- `ui_guide_composer_dark.html` and `ui_guide_composer_light.html` updated to reflect all composer changes: scenario card backgrounds, expand-button pattern for supplement input, poetry emoji, "Custom" naming, divider removal, `space-y-6` spacing.

### Breaking Changes
- `GET /` no longer returns the JSON health response — use `GET /api/health` instead. (Only affects direct API consumers; the frontend was not using this endpoint.)

---

## v0.7.0

Date: 2026-04-10

### Highlights
- **Phase A — Portable distribution foundation** — The backend now serves the compiled frontend as static files, eliminating the need to run a separate Vite dev server for production use. Mount and SPA fallback are conditional (only active when `frontend/dist` exists), so the existing dev workflow is unaffected.
- **Data directory isolation** — A new `OPENVOCA_DATA_DIR` environment variable controls where `openvoca.db` is written. When set, the database is created at `$OPENVOCA_DATA_DIR/openvoca.db`; otherwise it defaults to `./openvoca.db` as before. This is the foundation for the v0.7.0 portable ZIP distribution.
- **Test file reorganization** — Backend test suite split into focused files: `test_main.py` (HTTP API), `test_word_store.py` (storage + engine), `test_tokenizer.py` (tokenizer), `test_static.py` (SPA serving), reducing `test_main.py` from 648 to ~560 lines and removing duplicate tokenizer tests.
- **Open-source license** — Project is now licensed under **AGPL-3.0**. `LICENSE` file, `README.md` license section, and `CONTRIBUTING.md` contributor notice added.

### Backend
- `word_store.py`: `_make_engine()` function added. Reads `OPENVOCA_DATA_DIR` env var for the DB path; `_engine` is initialized via this function (monkeypatchable).
- `main.py`: imports reorganized (alphabetical); `StaticFiles` mount + `spa_fallback` route added at end of file. Both are conditional on `frontend/dist` existing at startup.
- New test file `test_static.py`: verifies `spa_fallback()` returns `FileResponse` pointing at `index.html`.
- `test_word_store.py`: 2 new tests for `_make_engine()` (default path + `OPENVOCA_DATA_DIR`).
- 2 duplicate tokenizer tests removed from `test_main.py`. Total: **107 backend tests**.

### Frontend
- Version bump only (`0.7.0`). No functional changes.

### Design
- `design/Bundling.md` added — comprehensive portable distribution design (ZIP, Rust launcher, tray icon, update strategy, Phases A–D).

### Breaking Changes
- None. `OPENVOCA_DATA_DIR` is opt-in; defaults unchanged.

---

## v0.6.10

Date: 2026-04-09

### Highlights
- **Default zoom reset** — default UI zoom changed from 125% back to 100% for a more natural initial experience.
- **Dark mode button fix** — Tailwind `dark:` variant now scoped to `data-reading-theme="dark"` instead of OS `prefers-color-scheme`, fixing invisible button borders when the OS is in dark mode but the app is in light mode.
- **Three-way vocabulary sort** — Stats page now offers three sort modes: "Due for Review" (cooldown ASC), "By Familiarity" (interval ASC — least familiar first), and "By Recent" (last seen DESC). Previously "By Familiarity" was actually sorting by cooldown.
- **Familiarity progress bar** — replaced the color dot in the interval column with a horizontal progress bar using a logarithmic scale (2→64), making learning progress more intuitive at a glance.
- **Terminology cleanup** — column header and button titles renamed from "Interval"/"复习间隔" to "Familiarity"/"熟悉度" for consistency.

### Backend
- `list_all_words()` in `word_store.py`: default sort renamed from `"familiarity"` to `"due"` (cooldown ASC, interval ASC). New `"familiarity"` mode sorts by interval ASC, cooldown ASC.
- `GET /api/vocabulary`: query parameter `sort` now accepts `due|familiarity|recent` (was `familiarity|recent`), default changed to `due`.
- 1 new test (`test_vocabulary_sort_familiarity`), 1 renamed test (`test_vocabulary_sort_due`). Total: 106 backend tests.

### Frontend
- `main.css`: added `@variant dark` override to scope `dark:` utilities to `[data-reading-theme="dark"]`.
- `App.vue` / `SettingsView.vue`: default zoom changed from `"md"` (125%) to `"sm"` (100%).
- `SettingsView.vue`: button border opacity increased from `border-black/10` to `border-black/15`.
- `StatsView.vue`: three sort pills (Due for Review / By Familiarity / By Recent), default `"due"`. Interval column shows progress bar instead of number + label + dot. Removed `intervalLabel()` function.
- `reading.ts`: `fetchVocabulary()` accepts `"due" | "familiarity" | "recent"`, default `"due"`.
- `useI18n.ts`: added `sortByDue` key (EN: "Due for Review", ZH: "即将复习"). Renamed `statsInterval` to "Familiarity"/"熟悉度". Updated `intervalHalve`/`intervalDouble` titles. Removed 4 dead keys (`familiarityNeedsReview`, `familiarityLearning`, `familiarityFamiliar`, `familiarityMastered`).
- 11 frontend tests passing.

### Breaking Changes
- `GET /api/vocabulary` default sort changed from `familiarity` to `due`. The old `?sort=familiarity` still works but now sorts by interval ASC instead of cooldown ASC.

---

## v0.6.9

Date: 2026-04-06

### Highlights
- **Zoom viewport fix** — views at zoom levels above 100% no longer produce a scrollbar or break vertical centering. A new `--app-zoom` CSS custom property drives a `min-h-zoom-screen` utility that compensates `100vh` for the active zoom factor.
- **Dark mode button contrast** — "Test Connection", "Export CSV", and "Export JSON" buttons in Settings now have visible borders and hover states in dark mode (`dark:border-white/15`, `dark:hover:bg-white/8`).

### Frontend
- `App.vue` / `SettingsView.vue`: `applyZoom()` now sets `--app-zoom` CSS variable alongside `zoom` on `#app`.
- `main.css`: added `.min-h-zoom-screen { min-height: calc(100vh / var(--app-zoom, 1)); }` utility.
- `HomeView.vue`, `StatsView.vue`, `SettingsView.vue`: replaced `min-h-screen` with `min-h-zoom-screen`.
- `SettingsView.vue`: added `dark:border-white/15 dark:hover:bg-white/8` to three action buttons.

---

## v0.6.8

Date: 2026-04-06

### Highlights
- **Stats page: sortable vocabulary** — two sort modes via pill toggle: "By Familiarity" (cooldown ASC, interval ASC) and "By Recent" (last reviewed first). Sorting is performed server-side for future pagination readiness.
- **Stats page: expandable word details** — click any row to reveal the last review timestamp (relative, e.g. "3h ago") and the previous sentence context in which the word appeared.
- **Dark mode fix** — the "Know" button in the definition toast is now readable in dark mode (was white-on-white).
- **Timezone fix** — `lastSeen` timestamps are now always serialized with a UTC offset (`+00:00`), preventing local-time misinterpretation on the frontend.
- **Progress bar removed** — the non-functional decorative progress bar at the top of the reading view has been removed from both the Vue code and design mockups.

### Backend
- `WordRecordOut` response model now includes `lastSeen` (ISO 8601 with UTC offset).
- `GET /api/vocabulary` accepts `?sort=familiarity|recent` query parameter (validated, 422 on invalid values).
- `list_all_words()` in `word_store.py` accepts `sort` keyword argument for server-side ordering.
- New `_utc_iso()` helper in `main.py` to re-attach UTC timezone to naive datetimes from SQLite.
- 4 new tests: sort familiarity, sort recent, sort invalid, lastSeen presence. Total: 105 backend tests.

### Frontend
- `fetchVocabulary(sort)` in `reading.ts` passes sort mode to backend API.
- `StatsView.vue`: sort toggle pills re-fetch from backend; click any row to expand inline detail showing relative last-seen time and italic previous context. Interactive controls use `.stop` to avoid accidental row toggle.
- `DefinitionToast.vue`: "Know" active button uses `dark:text-black` instead of `dark:text-ink` for readability.
- `HomeView.vue`: removed decorative progress bar div.
- `useI18n.ts`: 4 new i18n keys (`sortByFamiliarity`, `sortByRecent`, `lastSeenLabel`, `lastContextLabel`).
- `WordRecordOut` interface updated with `lastSeen` field.
- Total: 11 frontend tests.

---

## v0.6.7

Date: 2026-04-06

### Highlights
- **Copy & read aloud**: two new action buttons below the sentence — copy to clipboard (with checkmark feedback) and browser TTS read-aloud (with stop toggle).
- **Editable vocabulary records**: interval can be halved (÷2) or doubled (×2) via buttons in the Stats table. Cooldown is now an inline editable number input. Both are clamped to valid ranges.
- **Delete individual words**: each row in the Stats table has a delete button (×) to remove a single word record.
- **Click-to-toggle mark**: clicking the same word again while its definition toast is showing toggles between "Know" and "Don't know" without needing to reach the toast buttons.
- **Stale record safety**: PATCH and DELETE endpoints return 404 when the target record has already been deleted (multi-tab scenario), with dedicated test coverage.

### Backend
- New `PATCH /api/vocabulary/{lemma}/{pos}` endpoint — update interval (clamped to [2, 64]) and/or cooldown (clamped to [0, interval]).
- New `DELETE /api/vocabulary/{lemma}/{pos}` endpoint — remove a single word record; returns 404 if already deleted.
- New `update_word_record()` and `delete_word_record()` functions in `word_store.py`.
- 14 new tests (5 update, 4 delete, 2 API PATCH, 3 API DELETE including stale-tab scenarios). Total: 101 backend tests.

### Frontend
- New `tokensToPlainText()` utility in `reading.ts` — pure function to reconstruct plain text from tokens (6 tests in `reading.spec.ts`).
- New `updateWordRecord()` and `deleteWordRecord()` API functions in `reading.ts`.
- `HomeView.vue`: copy button (clipboard → checkmark for 1.5s) and read-aloud button (speaker → stop square while playing). TTS auto-cancels on sentence advance. Clicking the same word again toggles know/don't-know.
- `StatsView.vue`: interval gets −/+ buttons (exponential ÷2/×2), cooldown is an inline editable `<input type="number">`, each row gets a delete (×) button. Color dot moved after the familiarity label.
- `useI18n.ts`: added 5 new i18n keys (`copySentence`, `readAloud`, `intervalHalve`, `intervalDouble`, `deleteWord`).
- Total: 11 frontend tests (6 reading + 5 HomeView).

---

## v0.6.6

Date: 2026-04-06

### Highlights
- **Hyphenated word merging**: compound words like "lo-fi", "well-known", and "state-of-the-art" are now treated as single clickable tokens instead of being split into separate parts by spaCy.
- **Dictionary default changed to bilingual**: the definition language setting now defaults to "Both" (Chinese + English) instead of Chinese only.

### Backend
- New `_merge_hyphenated()` post-processing pass in `tokenizer.py` — after spaCy tokenization, adjacent `word-hyphen-word` sequences with no intervening whitespace are merged back into a single `SentenceToken`.
- Target matching updated: hyphenated targets like `*lo-fi*` are stored as whole keys, matching merged tokens directly.
- 2 new tests: `test_hyphenated_non_target_word`, `test_hyphenated_chain`. Updated `test_hyphenated_target_word` for merged behavior. Total: 87 backend tests.

### Frontend
- `SettingsView.vue` / `HomeView.vue`: dictionary display default changed from `"zh"` to `"both"`.

---

## v0.6.5

Date: 2026-04-06

### Highlights
- **Built-in dictionary**: click any word in the reading view to see its definition in a top-center toast. Powered by a compact 7.7 MB dictionary extract (ECDICT, 36,896 words).
- **Know / Don't know toggle**: the definition toast includes a toggle — tap "Don't know" to highlight the word, or "Know" (default) to leave it unmarked.
- **Definition language setting**: new "Dictionary" section in Settings lets you choose Chinese only, English only, or both definitions.
- **Multi-line definitions**: long definitions are split by line breaks and capped at 4 lines per language for readability.
- **Word-not-found handling**: words not in the dictionary still show a toast with the word and a "No definition found" message.

### Backend
- New `GET /api/dictionary/{word}` endpoint — case-insensitive lookup returning word, phonetic, definition, translation, pos, tag, exchange. Returns 404 for unknown words.
- New `src/services/dictionary.py` with `lookup()` and `lookup_custom()` functions backed by SQLite.
- New `backend/data/dictionary.db` — compact dictionary extracted from ECDICT (BNC/COCA top 30k + exam-tagged words with Chinese translations).
- New `scripts/extract_dictionary.py` for regenerating the dictionary from `stardict.db`.
- 7 new tests in `test_dictionary.py`. Total: 85 backend tests.

### Frontend
- New `DefinitionToast.vue` component — fixed top-center toast with slide-down animation, definition display, and know/don't-know toggle.
- `SentenceDisplay.vue`: click events now emit `word-click` (replaced `toggle-mark`). Word marking is handled by the toast toggle instead of direct clicks.
- `HomeView.vue`: wired dictionary lookup on word click, document click to dismiss, definition state management. Dismisses toast on sentence advance and composer return.
- `SettingsView.vue`: new "Dictionary" section with definition language toggle (中文 / EN / Both), stored in `dictionary.display` setting.
- `reading.ts`: new `fetchDefinition(word)` API function and `DictionaryEntry` interface.
- `useI18n.ts`: added 8 new i18n keys (`definitionKnow`, `definitionDontKnow`, `definitionNotFound`, `dictionarySection`, `dictionaryDisplay`, `dictionaryDisplayZh`, `dictionaryDisplayEn`, `dictionaryDisplayBoth`).

### Design
- Updated `ui_guide_reading_light.html` and `ui_guide_reading_dark.html` with top-center definition toast mockup.

---

## v0.6.4

Date: 2026-04-06

### Highlights
- **Vocabulary CSV export**: new "Export Vocabulary" button in both the Stats page and the Settings Data section. Downloads all word records as a CSV file (`lemma, pos, interval, cooldown`).
- **Settings page restructured**: the "Data" section (export vocabulary + export settings) now sits above the "Danger Zone" for a more logical flow.
- **Danger Zone confirmation**: "Clear Database" and "Clear Settings" now require explicit confirmation via a browser dialog before executing, preventing accidental data loss.
- **Header UX polish**: removed hover backgrounds from Menu/Stats buttons; moved the settings gear icon next to the Menu link for consistency.
- **Test suite reorganized**: `test_main.py` split into `test_main.py` (API endpoints), `test_word_store.py` (algorithm logic), and `test_openai_compat.py` (LLM client). Shared helper in `conftest.py`. 78 backend tests, 5 frontend tests.

### Backend
- New `GET /api/vocabulary/export` endpoint — returns a streaming CSV response with `Content-Disposition: attachment`.
- 2 new tests: `test_export_vocabulary_csv`, `test_export_vocabulary_csv_empty`.

### Frontend
- `StatsView.vue`: replaced "Clear All" button with "Export" button (CSV download via blob).
- `SettingsView.vue`: added "Export Vocabulary" row to Data section; Data section moved above Danger Zone; both Danger Zone actions now use `window.confirm()`.
- `reading.ts`: new `exportVocabulary()` API function.
- `useI18n.ts`: added 7 new i18n keys (`exportVocabulary`, `exportVocabularySettings`, `exportVocabularySettingsDescription`, `exportVocabularySettingsButton`, `confirmClearVocabulary`, `confirmClearSettings`).

---

## v0.6.3

Date: 2026-04-06

### Highlights
- **Prompt assembly moved to frontend**: the frontend now builds the complete prompt (template interpolation + scenario/difficulty/length instructions + target words). The backend receives a single `prompt` string and only appends the internal markdown-marking directive. This eliminates duplication between preview and generation.
- **Simplified API**: `POST /api/reading-sentence/next` now accepts `{ prompt, targetWords }` instead of `{ promptTemplate, targetWords, composerInstructions }` — 2 fields instead of 3.
- **Backend sorting**: vocabulary list sorting moved from frontend to backend SQL (`ORDER BY cooldown ASC, interval ASC`), preparing for future pagination and filtering.

### Backend
- `prompt_builder.py`: simplified from 50 to 28 lines. No longer does template interpolation or composer instruction concatenation — only appends the IMPORTANT markdown-marking directive when target words are present.
- `ReadingSentenceRequest`: replaced `promptTemplate` + `composerInstructions` with a single `prompt` field. `targetWords` retained for tokenizer marking.
- `list_all_words()`: now sorts by `cooldown ASC, interval ASC` in SQL (was `interval ASC, last_seen ASC`).
- 76 backend tests passing (prompt_builder tests simplified from 9 to 6).

### Frontend
- `ComposerCard.vue`: new `buildPrompt()` function assembles the complete prompt (resolves `{{target_words}}`, appends composer instructions). Emits `(prompt, targetWords)` instead of `(composerInstructions, targetWords)`.
- `HomeView.vue`: removed `DEFAULT_READING_PREFERENCES` import (no longer needed). `loadSentence` sends `{ prompt, targetWords }`.
- `StatsView.vue`: removed client-side sort (backend handles it).

### Breaking Changes
- `POST /api/reading-sentence/next`: request body changed from `{ promptTemplate, targetWords, composerInstructions? }` to `{ prompt, targetWords }`. The `prompt` field must contain the fully assembled prompt.

---

## v0.6.2

Date: 2026-04-06

### Highlights
- **Target Word Preview & Edit**: users can now see, remove, and add target words in the Composer before generating a sentence. Words are auto-selected from the vocabulary and injected into the prompt template.
- **Cooldown tick fix**: `tick_cooldowns()` moved from the preview endpoint to `/api/reading-sentence/next`, preventing repeated page refreshes from draining cooldowns to zero.

### Backend
- New `GET /api/target-words?limit=K` endpoint — picks available words without ticking cooldowns.
- `POST /api/reading-sentence/next` now requires `targetWords: string[]` in the request body (replacing the old `targetWordCount`). Backend uses the frontend-chosen word list directly.
- `tick_cooldowns()` moved back to `/next` — called once per generation cycle, not on preview.
- 2 new tests: `test_target_words_endpoint_does_not_tick`, `test_next_endpoint_ticks_cooldowns`. 79 total backend tests.

### Frontend
- New `fetchTargetWords(limit)` API function.
- `ComposerCard.vue`: fetches target words on mount, displays word chips with `×` remove, `+` button reveals inline input for manual word entry. Target Words section placed at top of card.
- Prompt preview now resolves `{{target_words}}` with the actual selected words.
- `ComposerCard` emits both `composerInstructions` and `targetWords`.
- `StatsView.vue`: words sorted by review priority (cooldown ASC, interval ASC). Table split into 4 columns: Lemma, POS, Interval, Cooldown — matching the database schema.
- New i18n keys: `composerTargetWords`, `composerTargetWordsHint`, `composerAddWordPlaceholder`, `statsLemma`, `statsInterval`, `statsCooldown` (EN + ZH).

### Design Documents
- `ui_guide_composer_light.html` / `ui_guide_composer_dark.html`: fully rewritten with 5-card scenario grid, collapsible sections, Target Words module at top.

### Breaking Changes
- `POST /api/reading-sentence/next`: `targetWordCount` field replaced by `targetWords: string[]`. Clients must now supply an explicit word list.

---

## v0.6.1

Date: 2026-04-06

### Highlights
- **Persistent HTTP connections**: the LLM client now creates a single `httpx.AsyncClient` at init and reuses it across all requests, eliminating per-call connection overhead. Graceful shutdown via FastAPI `lifespan`.
- **SQL-optimized bulk operations**: `tick_cooldowns()` and `clear_all_words()` replaced ORM loops with single raw SQL statements for O(1) database round-trips.
- **Composer UI guide refresh**: both light and dark HTML mockups fully rewritten to match the current implementation — 5-card scenario grid, collapsible difficulty/length with custom, prompt preview, and new Target Words preview module.

### Backend
- `OpenAICompatibleClient`: refactored from per-call `async with httpx.AsyncClient(...)` to persistent client created in `__init__`. Added `aclose()` method.
- FastAPI app: added `lifespan` async context manager that calls `llm.aclose()` on shutdown.
- `set_provider()` is now `async` — closes the old client before creating a new one to prevent connection leaks.
- `word_store.py`: `tick_cooldowns()` now uses `UPDATE wordrecord SET cooldown = cooldown - 1 WHERE cooldown > 0` (single SQL). `clear_all_words()` uses `DELETE FROM wordrecord` with `result.rowcount`.
- Added `from sqlalchemy import text` import for raw SQL execution.
- 2 new tests: persistent connection reuse, graceful client shutdown. 78 total backend tests passing.

---

## v0.6.0

Date: 2026-04-01

### Highlights
- **Scenario-driven Composer**: replaced the Topic + Tone + Length slider with a card-based scenario selector. 4 creative presets (Slice of Life, Fun Facts, Absurd Headlines, Poetry) + a No Preset option, each with a full "persona prompt" injected into the LLM request.
- **Custom Difficulty & Length**: Difficulty and Length panels now collapse by default and each offer 3 presets + a "Custom" option with free-text input. Empty custom = no constraint.
- **Unified model configuration**: replaced the Ollama-specific provider with a generic OpenAI-compatible API client (`/v1/chat/completions`), supporting Ollama, OpenAI, DeepSeek, Groq, OpenRouter, SiliconFlow, and any compatible endpoint.
- **Prompt architecture overhaul**: prompt assembly (scenario + difficulty + length) moved entirely to the frontend. Backend receives the assembled `composerInstructions` string.
- **Dead code housecleaning**: removed legacy `OllamaClient`, `GET /api/models` stub, unused `target_words` request field, and 12 dead i18n keys.

### Breaking Changes
- `GET /api/models` endpoint removed (was already a deprecated stub returning `[]`).
- `target_words` / `targetWords` field removed from `POST /api/reading-sentence/next` request body.
- `OllamaClient` removed. Use `OpenAICompatibleClient` (set endpoint to `http://localhost:11434` for Ollama).

---

## v0.5.1

Date: 2026-03-31

### Highlights
- **Persistent settings store**: all user preferences (interface, reading, generation) are now stored in the backend SQLite database via a new `SettingRecord` model, replacing scattered `localStorage` keys.
- **Settings page refactor**: replaced the modal-based preferences dialog with a full-page `/settings` route, aligning with the `ui_guide_settings.html` design spec.
- **Unified settings composable**: new `useSettings()` reactive singleton provides `get`/`set`/`hydrate` API with instant localStorage cache and async backend sync.

---

## v0.5.0

Date: 2026-03-28

### Highlights
- **Cooldown queue algorithm**: replaced the 0–4 `familiarity` scale with an `interval` + `cooldown` dual-field model. Miss → interval halves; Hit → interval doubles. Words enter a cooldown countdown after each review, emerging automatically when due.
- **Lemma normalization**: vocabulary now keys on `(lemma, pos)` instead of `(word, pos)`. All inflected forms collapse into a single record.
- **`last_context` field**: each word record stores the most recent sentence it appeared in.

### Breaking Changes
- **Database incompatible**: `openvoca.db` must be deleted and recreated. Schema changed from `(word, pos, familiarity, last_seen)` to `(lemma, pos, interval, cooldown, last_seen, last_context)`.
- **API contract changed**: `/api/feedback` now expects `{ lemma, pos }` instead of `{ word, pos }`. `/api/vocabulary` returns `{ lemma, pos, interval, cooldown, lastContext }` instead of `{ word, pos, familiarity }`.

---

## v0.4.9

Date: 2026-03-27

### Added
- Error handling for `submitFeedback`: a 4-second auto-dismissing toast warns when word feedback fails to save.

---

## v0.4.8

Date: 2026-03-27

### Removed
- Dead code: `POST /api/reading-sentence` endpoint, `fetchReadingSentence()` frontend function, and Pinia dependency.

### Breaking Changes
- `POST /api/reading-sentence` removed. Use `POST /api/reading-sentence/next` instead.

---

## v0.4.7

Date: 2026-03-27

### Highlights
- **Component extraction**: split 998-line `HomeView.vue` into `SentenceDisplay`, `HoldButton`, `ReadingSettingsBar`, `PreferencesModal`.
- **LLM abstraction**: introduced `LLMProvider` protocol in the backend, decoupling routes from the Ollama client.

---

## v0.4.6 – v0.4.1

Date: 2026-03-27

### Summary
A series of incremental improvements:
- v0.4.6: Contraction display spacing via `trailingSpace` token flag.
- v0.4.5: Extracted `_generate_reading_response` helper (DRY).
- v0.4.4: Added `lemma` field to tokens; POS-aware word marking in frontend.
- v0.4.3: Fixed hyphenated target words (`*well-known*`); added missing endpoint tests.
- v0.4.2: Replaced static stopword list with POS-aware function-word filtering.
- v0.4.1: Unified tokenization pipeline using spaCy; composite `(word, pos)` primary key.

---

## v0.4.0

Date: 2026-03-23

### Highlights
- Added backend stop-word filtering.
- Preserved model-driven target-word behavior using Markdown markers.
- Phase 1 objective reached: full loop (pick words → generate → mark → update familiarity) is stable.

---

## v0.3.3

Date: 2026-03-23

### Added
- Model-driven target-word annotation using Markdown emphasis markers (`*word*`).
- Sentence highlighting resilient to inflections, synonyms, and empty target-word cases.

---

## v0.3.2

Date: 2026-03-23

### Added
- Configurable per-sentence review word count (1–5) in Preferences.

---

## v0.3.1

Date: 2026-03-22

### Added
- Interface font-size control; dotted underlines for target words in sentence rendering.
- Improved hold-to-continue affordance with centered capsule interaction.

---

## v0.3.0

Date: 2026-03-22

### Highlights
- **Core learning loop**: mark words in-context, submit feedback, update familiarity, generate next sentence from least-familiar words.
- **Vocabulary stats page** with familiarity levels and clear-all support.
- **Hold-to-confirm** interaction for advancing sentences.

---

## v0.2.0

Date: 2026-03-22

### Added
- Tokenization service; `POST /api/reading-sentence` returns tokenized output.
- Inline reading settings panel (size/spacing/theme).
- Reading theme support (light/dark).

### Breaking Changes
- `POST /api/reading-sentence` response now includes a `tokens` field.

---

## v0.1.0

Date: 2026-03-22

### Highlights
- Initial release. Phase 1 minimal closed loop for sentence generation with local Ollama (`gemma3:4b`).
- Reading page with Zen-style layout.
- Preferences menu (target words, prompt template).
- Lightweight i18n (zh/en) with locale persistence.
