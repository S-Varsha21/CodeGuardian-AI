FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN useradd --create-home --uid 10001 runner \
    && mkdir -p /workspace \
    && chown runner:runner /workspace

WORKDIR /workspace

USER 10001:10001

ENTRYPOINT ["python"]
