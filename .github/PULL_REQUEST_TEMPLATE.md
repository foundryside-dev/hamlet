## Summary

What this changes and why, in a sentence or two. Link the issue it closes, if any.

## Changes

-

## Config and compatibility

- [ ] No config pack or schema changes
- [ ] Changes a declaration schema: shipped packs and `docs/config-schemas/` are updated in this PR

Townlet has no backwards-compatibility contract before 1.0. Old configs should fail loudly, so
describe what now fails rather than adding a migration path.

## Checks

- [ ] `uv run ruff check .` and `uv run black --check src tests`
- [ ] `uv run mypy src/townlet --show-error-codes`
- [ ] `uv run python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt --ratchet .defaults-ratchet`
- [ ] `uv run python scripts/validate_compiler_cli.py`
- [ ] `uv run pytest -n auto`
- [ ] Frontend changes: `npm test` and `npm run build` in `frontend/`

## Notes for reviewers

Anything you want looked at closely, known limitations, or screenshots for viewer changes.
