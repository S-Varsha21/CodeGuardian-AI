
from fastapi import FastAPI

app = FastAPI(
    title="CodeGuardian AI",
    description="AI-powered software testing and code security analysis.",
    version="0.1.0",
)


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
