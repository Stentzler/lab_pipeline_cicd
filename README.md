# lab_pipeline_cicd

Study repository for a Python API CI/CD pipeline with GitHub Actions, security checks, Docker image validation, SonarQube analysis, Trivy scanning, and Slack notifications.

## Pipeline Overview

The main workflow is [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml). It is designed to validate application code early, build and scan Docker images only when needed, and notify Slack about successful or failed runs.

The workflow runs on:

- Manual execution through `workflow_dispatch`.
- Pushes to `develop`, `main`, and `release/**`.
- Pull requests targeting `main`.

It only runs when files under `app/**`, `.github/actions/**`, or `.github/workflows/**` change.

## Global Settings

The pipeline uses a shared `metadata` job to centralize values such as:

- Python version: `3.12`
- Application directory: `app`
- Coverage threshold: `80`
- Docker image name: `study-api`
- Artifact names for test and Trivy reports
- Report and image retention periods

This keeps the rest of the workflow consistent and avoids repeating the same values in every job.

## Job Flow

```text
metadata
  ├── ruff
  └── bandit
        ↓
      tests
        ↓
    pip_audit
        ↓
      build
        ↓
      trivy
        ├── trivy_enforcement
        └── sonar

notify_slack_failure / notify_slack_success run at the end.
```

Some jobs are conditional:

- `build` and `trivy` run only for `main`, `release/**`, or pull requests targeting `main`.
- `sonar` runs only on pushes to `main`.
- Slack notification jobs always evaluate at the end and decide whether to send success or failure messages.

## Pipeline Steps

### `metadata`

Prepares shared pipeline values and exposes them as job outputs. Other jobs use these outputs for paths, Python version, Docker image metadata, artifact names, and retention settings.

### `ruff`

Runs Ruff against the Python application using the local action:

```text
.github/actions/run-ruff-scan
```

This checks formatting-adjacent lint rules, import order, common Python mistakes, and modernization suggestions based on the project Ruff configuration.

### `bandit`

Runs Bandit security analysis against `app/src` using:

```text
.github/actions/run-bandit-scan
```

This checks the Python source code for common security risks.

### `tests`

Runs unit and integration tests through:

```text
.github/actions/run-tests
```

This job:

- Sets up Python.
- Installs dependencies from `app/requirements.txt`.
- Runs `pip check`.
- Executes tests under `tests/unit` and `tests/integration`.
- Generates coverage output.
- Enforces minimum coverage of `80%`.
- Uploads JUnit and coverage reports as artifacts.

### `pip_audit`

Runs dependency vulnerability checks with:

```text
.github/actions/run-pip-audit
```

It scans `app/requirements.txt` for known vulnerable Python dependencies.

### `build`

Builds the Docker image using:

```text
.github/actions/run-build
```

This job:

- Builds the `study-api` Docker image.
- Verifies the image exists locally.
- Saves the image as a tarball.
- Uploads the image tarball as a short-lived artifact.

This job only runs for release-relevant branches and pull requests targeting `main`.

### `trivy`

Scans the Docker image using:

```text
.github/actions/run-trivy-report
```

This job downloads the image artifact, runs Trivy, uploads a Trivy report artifact, and exposes whether blocking vulnerabilities were found.

### `trivy_enforcement`

Applies the final Trivy decision using:

```text
.github/actions/run-trivy-enforcement
```

This job fails the pipeline when Trivy found blocking vulnerabilities or when the Trivy scan job failed unexpectedly.

### `sonar`

Runs SonarQube analysis using:

```text
.github/actions/run-sonar-scan
```

This job only runs on pushes to `main`. It:

- Checks out the repository with full history.
- Resolves the project version.
- Uses uploaded test and Trivy artifacts.
- Sends analysis data to SonarQube.

Required environment configuration:

- Environment: `SONAR_TOKEN`
- Secret: `SONAR_TOKEN`
- Variable: `SONAR_HOST_URL`

## Slack Notifications

The pipeline has two Slack notification actions:

```text
.github/actions/notify-slack-failure
.github/actions/notify-slack-success
```

Failure notifications are sent when any required job fails or is cancelled. Success notifications are sent when no required job failed or was cancelled.

The messages include:

- Project name
- Workflow name
- Trigger type, such as `push`, `pull_request`, or `workflow_dispatch`
- Branch name
- GitHub user who triggered the run
- Short commit SHA
- Workflow run link
- Source event link

Failure messages also include:

- Pull request title or commit message
- Failed job and failed step when available from the GitHub Actions API
- A fallback message pointing to the workflow logs when details are unavailable

Required Slack configuration in the `SONAR_TOKEN` environment:

- Secret: `SLACK_CICD_ERRORS`
- Secret: `SLACK_CICD_SUCCESS`
- Variable: `SLACK_GITHUB_USER_MAP`

`SLACK_GITHUB_USER_MAP` is optional and maps GitHub usernames to Slack member IDs so Slack can create real mentions:

```json
{
  "Stentzler": "U12345678"
}
```

## Local Checks

Run the same test command used by CI from the `app` directory:

```bash
cd app
source .venv/bin/activate

mkdir -p reports

python -m pytest tests/unit tests/integration -q \
  --cov \
  --cov-config=.coveragerc \
  --cov-report=term-missing \
  --cov-report=xml:coverage.xml \
  --junitxml=reports/junit.xml \
  --cov-fail-under=80
```

Run GitHub Actions linting locally:

```bash
.tools/bin/actionlint
```

## Notes

External GitHub Actions are pinned to full commit SHAs to comply with repository security policy. Local wrapper actions are used to keep the main workflow readable and to centralize repeated behavior.
