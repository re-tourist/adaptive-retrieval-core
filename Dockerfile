FROM ghcr.io/astral-sh/uv:0.9.10 AS uv
FROM python:3.12-slim

COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/opt/arc \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/arc/bin:${PATH}"
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --group sparse --group harness --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev --group sparse --group harness --no-editable
USER 65532:65532
EXPOSE 8000
ENTRYPOINT ["arc"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]
