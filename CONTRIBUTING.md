# Contributing

## Development Setup

```bash
# Prerequisites: Python 3.12+, uv, Docker

git clone https://github.com/kogunlowo123/agent-runtime-defense.git
cd agent-runtime-defense
uv sync --all-extras
uv run pre-commit install
```

## Branch Naming

- `feat/short-description` — new feature
- `fix/short-description` — bug fix
- `chore/short-description` — maintenance
- `sec/short-description` — security patch
- `docs/short-description` — documentation only

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(anomaly-detector): add LOF ensemble to reduce false positives
fix(api): handle missing principal_id in baseline endpoint
sec(opa): tighten T2 approval scope validation
docs(adr): add ADR-0003 for embedding model selection
```

## Pull Request Process

1. Open a branch from `develop`
2. Write or update tests — all tests must pass
3. Run `make lint && make type-check`
4. Fill the PR template
5. Request review from `@kogunlowo123`
6. Squash merge to `develop`; release to `main` via release workflow

## Code Style

- **Python**: ruff (line length 100), mypy strict mode
- **Terraform**: `terraform fmt` enforced in CI
- **YAML/JSON**: 2-space indent

## Testing Requirements

- Unit tests for all new business logic
- Integration tests for new API endpoints
- Anomaly detection changes require updated false-positive rate tests

## Security Checklist

Before opening a PR that touches identity/, security/, or infra/:
- [ ] No secrets or credentials committed
- [ ] OPA policy tests added/updated
- [ ] Checkov scan passes on any new Terraform
- [ ] Container image changes documented in PR description
