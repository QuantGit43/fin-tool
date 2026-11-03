# fin-tool

Personal finance analysis for monobank and PrivatBank transactions: where the money goes,
how spending changes month to month, and whether you stay within your budget.

> Status: early development. Built step by step with [OpenSpec](https://openspec.dev) specs and TDD.

## Architecture

```
monobank API / Privat24 statement file / NBU rates
        -> fin/sources -> categorization -> SQLite
        -> reports (pandas) -> FastAPI (/api) -> React (web/)
```

## Your data stays local

- Code lives in this repository; personal data lives **outside** it, in a sibling folder `../fin-data`
  (`.env` with your token, `fin.db`, your rules and budget).
- The API listens on `127.0.0.1` only.
- Never commit real statements, tokens, or screenshots with real data.

## Development setup

Requirements: [uv](https://docs.astral.sh/uv/), Node.js 24, git, [gitleaks](https://github.com/gitleaks/gitleaks), [pre-commit](https://pre-commit.com).

```bash
uv sync                 # create .venv and install Python dependencies
pre-commit install      # run secret scanning before every commit
uv run pytest           # run the test suite
```

Copy `.env.example` to `../fin-data/.env` and fill in your values.

## License

MIT
