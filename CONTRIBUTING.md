# Contributing to Townlet

Thanks for your interest. Townlet is a pre-release research project maintained by one person, so
please open an issue to discuss anything larger than a small fix before you write the code.

By taking part you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).

## Setting up

You need Python 3.13 or newer and [uv](https://github.com/astral-sh/uv). A CUDA GPU is optional.
Frontend work also needs Node.js 20.19 or newer (Vite 7).

```bash
git clone https://github.com/foundryside-dev/hamlet
cd hamlet
uv sync --all-extras --locked
uv run pytest
```

`--all-extras` installs the `dev` tools (pytest, Ruff, Black, mypy) and the `recording` extra,
which mypy needs to type-check `src/townlet/recording/`.

For the viewer:

```bash
cd frontend
npm ci
npm run dev    # http://localhost:5173
npm test
```

## Ground rules

These matter more here than in most projects. A pull request that breaks them will be asked to
change.

- **Configuration over code.** If a feature can only be used by editing Python, it is not
  finished. Prefer adding declarative surface to the config schema over special-casing the
  engine.
- **No hidden defaults.** Every behavioural parameter must be set explicitly in config. Pydantic
  DTOs use `extra="forbid"` and `scripts/no_defaults_lint.py` enforces the rule in CI.
- **No backwards compatibility.** Townlet has no compatibility contract before its first release.
  Delete old code paths rather than keeping fallbacks, aliases or migration shims, and let old
  configs fail loudly.
- **Never branch on a variable's name.** Behaviour that differs per variable must come from a
  declared parameter, never from checks like `if name == "money"`.
- **Leave the oracle alone.** The frozen reference implementation
  ([docs/oracle/ORACLE.md](docs/oracle/ORACLE.md)) records pre-rewrite behaviour for comparison.
  Never edit anything under `.oracle/` or `oracle_fixtures/`.
- **Work in `src/townlet/`.** Nothing else under `src/` is live.

## Before you open a pull request

Run the same checks as CI:

```bash
uv run ruff check .
uv run black --check src tests
uv run mypy src/townlet --show-error-codes
uv run python scripts/no_defaults_lint.py src/townlet/ --whitelist .defaults-whitelist.txt --ratchet .defaults-ratchet
uv run python scripts/validate_compiler_cli.py
uv run pytest -n auto
```

`-n auto` runs the suite in parallel through pytest-xdist. Wall-clock `perf` tests are deselected
by default; run them with `uv run pytest -m perf --no-cov`. The full suite still takes several
minutes, so while iterating run the part you are changing, for example `uv run pytest tests/test_townlet/unit/universe/`.

Tests live under `tests/test_townlet/`: `unit/`, `integration/`, `regressions/` (one test per fixed
bug), `properties/` (Hypothesis) and `performance/`. Markers include `gpu`, `integration`, `e2e` and `perf`; GPU
tests skip when CUDA is unavailable. Test mechanics and contracts, not whether an agent learns a
particular strategy. Unexpected emergent behaviour is often worth keeping as a
[teachable moment](docs/teachable_moments/) rather than fixing.

## Pull requests

- Keep each pull request to one logical change.
- Use [Conventional Commits](https://www.conventionalcommits.org/) for commit subjects and the PR
  title, for example `fix(vfs): reject writes to immutable variables`.
- Fill in the [pull request template](.github/PULL_REQUEST_TEMPLATE.md).
- Update the config reference in [docs/config-schemas/](docs/config-schemas/) when you change a
  declaration, and add a line to [CHANGELOG.md](CHANGELOG.md) for user-visible changes.

## Reporting bugs and asking questions

Use the issue templates for bugs and feature requests, and a plain issue for questions. Please
include your Python, PyTorch and CUDA versions and the smallest config pack that reproduces the
problem. Report security problems privately as described in [SECURITY.md](SECURITY.md).

## License

Contributions are accepted under the [MIT License](LICENSE).
