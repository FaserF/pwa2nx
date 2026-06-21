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

## Codebase Architecture

| Area | Path |
|---|---|
| C/C++ Source | `source/` |
| Makefile | `Makefile` |
| App Metadata | `app.json` / `res/` |
| Workflows | `.github/workflows/` |

---

## Coding Rules

### C/C++ & Switch Homebrew
- All wrapper code must be fully compatible with devkitPro (devkitA64) and `libnx`.
- Proper memory management and error handling (check for return codes/`R_FAILED`).
- Graceful session persistence using specific User ID mounting (`WebArgType_Uid`).
- Automatic updater checks via GitHub API using `curl` or `http` services.

---

## Communication Rules (Summary)

| Rule | Behavior |
|---|---|
| Response length | Bullet points, ≤5 items per change |
| Walkthrough artifact | Only if user explicitly requests it |
| Implementation plan | Only for major architectural changes |
| Asking for confirmation | Never for obvious steps |
| Test output | Failures only |
| Repeating written code | Never |
| Closing remarks | None |
| Language defaults | Code, docs, comments, and AI responses must default to English (EN) unless requested otherwise |
