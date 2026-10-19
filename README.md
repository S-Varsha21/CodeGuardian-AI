# CodeGuardian AI 🛡️

**AI-Powered Edge-Case Test Generation, Regression Detection, and Code Security Analysis**

CodeGuardian AI is a developer-focused platform designed to help developers discover bugs that ordinary tests may miss. The project aims to generate edge-case tests, execute tests in isolated environments, detect regressions, and produce reports with reproducible evidence.

> **Project Status:** Early development. The initial FastAPI backend and automated API tests are implemented. AI-powered testing, sandboxing, regression detection, and GitHub integration are planned.

## 🎯 Problem Statement

Software can work correctly with normal inputs but fail on unexpected values, boundary conditions, or unusual execution paths. CodeGuardian AI aims to automate parts of the testing and analysis process to help developers identify these issues earlier.

## ✨ Planned Features

- **AI-assisted test generation:** Generate candidate tests for edge cases and boundary conditions.
- **Isolated test execution:** Run code in restricted Docker containers.
- **Regression detection:** Identify failures introduced by code changes.
- **Static security analysis:** Detect common security and code-quality issues.
- **Reproducible reports:** Provide test results, failure details, and evidence for debugging.
- **GitHub integration:** Connect repositories and evaluate code changes.

*These are planned features and are not yet implemented.*

## 🧰 Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend and testing logic |
| FastAPI | REST API |
| Uvicorn | Development server |
| pytest | Automated testing |
| HTTPX | API test client |
| Docker | Planned isolated code execution |
| TypeScript / React | Planned frontend |
| GitHub API | Planned repository integration |
| Ruff / Bandit | Planned code-quality and security checks |

## 📁 Project Structure

```text
CodeGuardian/
├── backend/
│   ├── app/
│   │   └── main.py
│   └── tests/
│       └── test_main.py
├── docs/
├── .gitignore
└── README.md
```

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or a compatible Python 3 version
- Git

### 1. Clone the repository

```bash
git clone https://github.com/S-Varsha21/CodeGuardian-AI.git
cd CodeGuardian-AI
```

### 2. Create a virtual environment

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install fastapi "uvicorn[standard]" pytest httpx
```

### 4. Start the backend

```bash
python -m uvicorn backend.app.main:app --reload
```

Open these URLs in your browser:

- Home: http://127.0.0.1:8000/
- Health check: http://127.0.0.1:8000/health
- Interactive API documentation: http://127.0.0.1:8000/docs

### 5. Run automated tests

In a second terminal, navigate to the project folder, activate the virtual environment, and run:

```bash
python -m pytest backend/tests/test_main.py -v
```

The initial tests verify the home and health endpoints.

## 🗺️ Development Roadmap

- [x] Create the initial FastAPI backend
- [x] Implement home and health endpoints
- [x] Add automated API tests
- [x] Publish the initial project to GitHub
- [x] Document the project in README
- [ ] Add dependency management
- [ ] Add automated testing with GitHub Actions
- [ ] Integrate linting and static security analysis
- [ ] Build the edge-case test-generation engine
- [ ] Implement restricted Docker-based execution
- [ ] Add regression comparison and evidence reports
- [ ] Integrate GitHub repository workflows
- [ ] Build the TypeScript / React frontend

## 🔐 Security Principles

The project is intended to use defense in depth when executing untrusted code. Future sandboxing should restrict network access, limit CPU and memory usage, minimize container privileges, and keep untrusted execution separate from the API server.

## 👩‍💻 Author

**S.Varsha .**  
AI & Data Science Engineering Student

GitHub: [@S-Varsha21](https://github.com/S-Varsha21)

## 📄 License

No license has been selected yet. Until a license is added, reuse and redistribution permissions should not be assumed.
