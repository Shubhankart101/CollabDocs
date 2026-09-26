# CollabDocs CI/CD Pipeline Documentation

The CI/CD pipeline for CollabDocs is implemented using **GitHub Actions** with reusable workflow templates to adhere to DRY (Don't Repeat Yourself) principles.

---

## 📁 Workflow File Structure

```
.github/workflows/
├── ci-cd.yml                        # Main workflow orchestrator
└── templates/
    ├── reusable-lint.yml            # Reusable linting & code format check
    ├── reusable-test.yml            # Reusable unit & integration testing with Postgres service
    ├── reusable-build.yml           # Reusable Docker container build check
    └── reusable-release.yml         # Reusable release packaging pipeline
```

---

## ⚙ Pipeline Stages

### 1. Code Quality & Linting (`reusable-lint.yml`)
- **Tools**: `flake8`, `black`, `isort`, `mypy`.
- **Triggers**: On pull requests and main pushes.
- **Actions**: Validates PEP 8 syntax, import ordering, code formatting, and static typing.

### 2. Automated Testing Suite (`reusable-test.yml`)
- **Database**: Provisions a live `postgres:15-alpine` container service.
- **Actions**: Runs Django database migrations, executes unit/integration tests with `coverage`, and outputs code coverage reports.

### 3. Container Build Pipeline (`reusable-build.yml`)
- **Tools**: Docker Buildx (`docker/build-push-action@v5`).
- **Actions**: Builds the container image from `Dockerfile` to guarantee buildability before deployment.

### 4. Application Release Pipeline (`reusable-release.yml`)
- **Triggers**: Only on pushes to the `main` branch after linting, testing, and container builds succeed.
- **Actions**: Bundles source code, creates a gzipped release tarball, and uploads it to GitHub release artifacts.
