# Contributing to The Council

Thanks for contributing. Please keep changes focused, tested, and easy to review.

## Standards

- Follow PEP 8 and keep functions small and readable.
- Prefer type hints for new or significantly modified functions.
- Avoid network calls by default; keep everything local-first.
- Preserve safety guardrails (no auto-execution without approval).

## Tests

Run the unit test suite before opening a PR:

```bash
pytest -v
```

If you change Council workflows, also run:

```bash
python3 scripts/smoke_test.py
```

## Commit Messages

- Use short, descriptive messages.
- Prefix with area when helpful (e.g., `feat(cli): ...`, `fix(memory): ...`).

## Branch + PR Workflow

1. Create a feature branch from `main`.
2. Keep commits scoped to a single concern when possible.
3. Open a PR into `main` with:
   - Summary of changes
   - Tests run
   - Risks or rollout notes
4. Request review before merging.

## Local Artifacts (Ignored)

Do not commit local runtime artifacts. Examples:

- `.env`, `.cursor/`, `.pytest_cache/`
- `council_memory.db`, `data/healing_log.json`, `ollama.log`
