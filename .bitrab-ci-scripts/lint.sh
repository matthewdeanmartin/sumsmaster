#!/usr/bin/env bash
set -euo pipefail
source ./.bitrab-ci-scripts/setup.sh
uv run isort --check-only sumsmaster tests
uv run black --check sumsmaster tests
uv run ruff check --quiet sumsmaster tests
uv run pylint --score=n --reports=n --rcfile=.pylintrc sumsmaster
uv run pylint --score=n --reports=n --rcfile=.pylintrc_tests tests
