
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(
    title="CodeGuardian AI",
    description="AI-powered software testing and code security analysis.",
    version="0.2.0",
)


class CodeAnalysisRequest(BaseModel):
    code: str = Field(
        ...,
        max_length=100_000,
        description="Python source code to analyze.",
    )


def scan_security_issues(code: str) -> list[dict]:
    """Scan Python source code with Bandit and return security findings."""
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            encoding="utf-8",
            delete=False,
        ) as temp_file:
            temp_file.write(code)
            temp_path = temp_file.name

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "bandit",
                "-f",
                "json",
                "-q",
                temp_path,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if result.returncode not in (0, 1):
            raise RuntimeError(
                "Bandit could not complete the security scan."
            )

        report = json.loads(result.stdout)

        return [
            {
                "test_id": issue["test_id"],
                "issue_text": issue["issue_text"],
                "severity": issue["issue_severity"],
                "confidence": issue["issue_confidence"],
                "line_number": issue["line_number"],
            }
            for issue in report.get("results", [])
        ]

    finally:
        if temp_path is not None:
            Path(temp_path).unlink(missing_ok=True)


@app.get("/")
def root():
    return {
        "message": "Welcome to CodeGuardian AI",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CodeGuardian AI",
    }


@app.post("/analyze")
def analyze_code(request: CodeAnalysisRequest):
    code = request.code

    try:
        compile(code, "<submitted_code>", "exec")
        syntax_valid = True
        syntax_error = None
    except SyntaxError as error:
        syntax_valid = False
        syntax_error = {
            "message": error.msg,
            "line": error.lineno,
            "column": error.offset,
        }

    security_findings = []
    security_scan_error = None

    if syntax_valid:
        try:
            security_findings = scan_security_issues(code)
        except subprocess.TimeoutExpired:
            security_scan_error = "Security scan timed out."
        except (
            RuntimeError,
            json.JSONDecodeError,
            OSError,
            KeyError,
            TypeError,
        ):
            security_scan_error = "Security scan could not be completed."

    severity_counts = {
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    }

    for finding in security_findings:
        severity = finding.get("severity", "").upper()
        if severity in severity_counts:
            severity_counts[severity] += 1

    return {
        "syntax_valid": syntax_valid,
        "syntax_error": syntax_error,
        "line_count": len(code.splitlines()),
        "character_count": len(code),
        "security_findings": security_findings,
        "security_summary": {
            "total_findings": len(security_findings),
            "by_severity": severity_counts,
        },
        "security_scan_error": security_scan_error,
    }

