# CollabDocs CI/CD Pipeline & GitHub Actions Guide

The Continuous Integration and Continuous Deployment (CI/CD) infrastructure for **CollabDocs** is powered by **GitHub Actions**. It employs a templatized architecture utilizing reusable workflows to promote modularity, maintainability, and clean separation of concerns.

---

## 📁 Workflow File Architecture

All workflow files are located in `.github/workflows/`:

```text
.github/workflows/
├── ci-cd.yml                        # Main pipeline orchestrator
├── reusable-lint.yml                # Code quality, formatting, and linting workflow
├── reusable-test.yml                # PostgreSQL service container & unit test workflow
├── reusable-build.yml               # Docker Buildx container image build workflow
└── reusable-release.yml             # Production artifact packaging & release workflow
```

---

## 🔄 Pipeline Job Dependency & Execution Flow

```text
   +-----------------------+
   |   Push / Pull Request |
   +-----------+-----------+
               |
               v
   +-----------------------+
   |   code-quality        |  (Runs reusable-lint.yml)
   +-----------+-----------+
               |
               v (needs: code-quality)
   +-----------------------+
   | unit-integration-tests|  (Runs reusable-test.yml + Postgres service)
   +-----------+-----------+
               |
               v (needs: unit-integration-tests)
   +-----------------------+
   |    container-build    |  (Runs reusable-build.yml + Docker Buildx)
   +-----------+-----------+
               |
               v (needs: container-build & branch == main)
   +-----------------------+
   |    release-package    |  (Runs reusable-release.yml + GitHub Release Artifact)
   +-----------------------+
```

---

## ⚙ Detailed Workflow Specifications

### 1. Main Pipeline Orchestrator (`ci-cd.yml`)

- **Triggers**:
  - `push` to `main` and `develop` branches.
  - `pull_request` to `main` and `develop` branches.
- **Jobs**:
  - `code-quality`: Invokes `./.github/workflows/reusable-lint.yml` with `python-version: '3.11'`.
  - `unit-integration-tests`: Depends on `code-quality`. Invokes `./.github/workflows/reusable-test.yml`.
  - `container-build`: Depends on `unit-integration-tests`. Invokes `./.github/workflows/reusable-build.yml` with `image-name: 'collabdocs-api'` and `image-tag: ${{ github.sha }}`.
  - `release-package`: Depends on `container-build`. Condition: `if: github.ref == 'refs/heads/main'`. Invokes `./.github/workflows/reusable-release.yml` with `version: '1.0.0'`.

---

### 2. Code Quality Workflow (`reusable-lint.yml`)

- **Type**: `workflow_call`
- **Inputs**:
  - `python-version` (optional, default `'3.11'`).
- **Steps Executed**:
  1. `actions/checkout@v4`: Checks out repository code.
  2. `actions/setup-python@v5`: Configures Python 3.11 environment.
  3. `Install dependencies`: Upgrades `pip` and installs `flake8`, `black`, `isort`, `mypy`, and `requirements.txt`.
  4. `Code Formatting Check`: Executes `black --check .` and `isort --check-only .`.
  5. `Lint with Flake8`: Runs `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics` for syntax error detection.

---

### 3. Automated Testing Suite (`reusable-test.yml`)

- **Type**: `workflow_call`
- **Inputs**:
  - `python-version` (optional, default `'3.11'`).
- **Service Containers**:
  - `postgres`: Image `postgres:15-alpine`
  - Environment: `POSTGRES_DB=collabdocs_test`, `POSTGRES_USER=collabuser`, `POSTGRES_PASSWORD=collabpass`
  - Ports: `5432:5432`
  - Health Check: `--health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5`
- **Steps Executed**:
  1. `actions/checkout@v4`
  2. `actions/setup-python@v5`
  3. `Install dependencies`: Installs `coverage` and project `requirements.txt`.
  4. `Run Migrations & Tests`: Sets database connection env vars pointing to `127.0.0.1:5432`, executes `python manage.py migrate`, runs `coverage run manage.py test api`, and outputs `coverage report -m`.

---

### 4. Container Build Workflow (`reusable-build.yml`)

- **Type**: `workflow_call`
- **Inputs**:
  - `image-name` (required string).
  - `image-tag` (optional string, default `'latest'`).
- **Steps Executed**:
  1. `actions/checkout@v4`
  2. `docker/setup-buildx-action@v3`: Initializes Docker Buildx.
  3. `docker/build-push-action@v5`: Validates multi-stage build of `./Dockerfile` without pushing.

---

### 5. Application Release Workflow (`reusable-release.yml`)

- **Type**: `workflow_call`
- **Inputs**:
  - `version` (required string, e.g. `'1.0.0'`).
- **Steps Executed**:
  1. `actions/checkout@v4`
  2. `Bundle Release Code`: Packages codebase into `release-dist/collabdocs-1.0.0.tar.gz` while excluding `.git`, `.venv`, and `__pycache__`.
  3. `actions/upload-artifact@v4`: Uploads the gzipped release tarball as a GitHub build artifact.
