#!/bin/bash
# Helper script to run commands in Docker container
# Phase 11: Containerization
#
# Usage:
#   ./scripts/docker_run.sh test                    # Run tests
#   ./scripts/docker_run.sh pipeline --image ...    # Run pipeline
#   ./scripts/docker_run.sh evaluation --split ...  # Run evaluation
#   ./scripts/docker_run.sh shell                   # Open shell
#   ./scripts/docker_run.sh <any-command>           # Run custom command

set -e

COMMAND=${1:-"test"}

case $COMMAND in
  "pipeline")
    shift
    docker compose run --rm app python scripts/run_pipeline.py "$@"
    ;;
  "evaluation")
    shift
    docker compose run --rm app python scripts/run_evaluation.py "$@"
    ;;
  "error-analysis")
    shift
    docker compose run --rm app python scripts/run_error_analysis.py "$@"
    ;;
  "test")
    docker compose run --rm app python -m pytest -v
    ;;
  "shell")
    docker compose run --rm app /bin/bash
    ;;
  "build")
    docker compose build
    ;;
  "clean")
    docker compose down
    docker system prune -f
    ;;
  *)
    # Run custom command
    docker compose run --rm app "$@"
    ;;
esac

# Made with Bob
