# AI Agent Reference for pwa2nx

---

## Token Efficiency Rules (CRITICAL — Read First)

These rules apply to **every response** without exception:

1. **Output minimal prose.** Bullet points only. No introductory sentences, no filler, no "Great question!", no "As requested".
2. **No walkthrough unless explicitly asked.** Never create or update `walkthrough.md` unless the user writes "walkthrough" or "summary" in their request.
3. **No implementation plan unless complex.** Skip planning artifacts for simple tweaks, single-file edits, bug fixes, or minor features. Plan only for major architectural changes.
4. **Short change summaries only.** After making changes, output ≤5 bullet points describing *what* changed and *why* — never a line-by-line description.
5. **No repeating file content.** Never echo back code you just wrote or edited. Reference filenames with links instead.
6. **No tool-call narration.** Do not describe what tool you are about to call. Just call it.
7. **Targeted file reads only.** Use `grep_search` or `view_file` with `StartLine`/`EndLine` to read only the relevant section. Never view an entire large file unless strictly necessary.
8. **Parallel tool calls.** Fire all independent tool calls in a single block. Never sequence calls that can run simultaneously.
9. **No re-summarizing artifacts.** After creating or updating an artifact, do NOT restate its contents — just link to it and note any open questions.
10. **Skip trivial confirmations.** Do not ask "Would you like me to proceed?" for obvious next steps. Just do them.
11. **No closing pleasantries.** End your response after the change summary. No "Let me know if you have questions!" etc.
12. **Reuse subagents.** Send follow-up tasks to an existing idle subagent instead of spawning a new one.
13. **Suppress test output noise.** When running tests, only report failures. Do not paste successful test output unless the user asks.
14. **Delegate with subagents.** For any research-heavy, multi-file, or parallelizable task, spin up a subagent instead of doing it inline.
15. **Prefer `research` subagent for read-only work.** Codebase exploration, grep searches, file reads, and web lookups should go to the `research` subagent.
16. **Prefer `self` subagent for isolated execution.** Use the `self` subagent for tasks that need write access in a separate context.

---

## Single Source of Truth
Read [project_manifest.json](file:///project_manifest.json) and [project_connections.json](file:///project_connections.json) first before performing recursive file searches to understand boundaries and flows.

---

## Codebase Architecture

| Area | Path | Description |
|---|---|---|
| C/C++ Source | [source/](file:///source) | Switch-side application wrapper wrapper, updater, and configurations |
| Scripts | [scripts/](file:///scripts) | Asset extraction and manifest parsers (e.g. [extract_pwa.py](file:///scripts/extract_pwa.py)) |
| Build Tool | [Makefile](file:///Makefile) | devkitPro build configuration and targets |
| Metadata | [app.json](file:///app.json) | App store metadata package layout |
| Workflows | [.github/workflows/](file:///.github/workflows) | Automated pipeline wrappers |

---

## CLI Commands Reference

- **Clean and Compile NRO**:
  ```bash
  make clean && make
  ```
- **Extract PWA & Update Headers (Python)**:
  ```bash
  python scripts/extract_pwa.py --url "<url>" --name "<name>"
  ```
- **Update Manifest File**:
  ```bash
  python scripts/generate_manifest.py
  ```

---

## Coding Rules & Quality Hygiene

- All wrapper code must be fully compatible with devkitPro (devkitA64) and `libnx`.
- Proper memory management and error handling (check for return codes/`R_FAILED`).
- Graceful session persistence using specific User ID mounting (`WebArgType_Uid`).
- Automatic updater checks via GitHub API using `curl` or `http` services.
- Keep reusable utilities inside `scripts/` or `source/`. Temporary files go into `scratch/`. Do not commit secrets.
- Coding comments and documentation must default to English (EN) unless requested otherwise.
