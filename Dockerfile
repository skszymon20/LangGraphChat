# inspired by https://github.com/CoreyMSchafer/FastAPI-19-Deployment-Docker-GCR/blob/main/Dockerfile
# BUILD STAGE
FROM python:3.14.7-slim-bookworm AS builder

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --target=/app/packages -r requirements.txt

COPY . ./

# PRODUCTION STAGE
FROM python:3.14.7-slim-bookworm

WORKDIR /app

# Run as non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Copy app and dependencies from builder stage
COPY --from=builder --chown=appuser:appuser /app /app

ENV PYTHONPATH="/app/packages"
ENV PATH="/app/packages/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# exec replaces shell so fastapi receives SIGTERM for clean shutdown
CMD ["/bin/sh", "-c", "exec fastapi run --host 0.0.0.0 --port \"$PORT\" --proxy-headers --forwarded-allow-ips '*'"]