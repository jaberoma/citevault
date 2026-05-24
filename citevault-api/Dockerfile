FROM python:3.11-slim

# WeasyPrint native deps + toolchain for building C extensions
# (zlib-state, a transitive dep via FlagEmbedding -> ir-datasets, needs gcc + zlib headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 \
    libffi-dev shared-mime-info \
    build-essential zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

COPY src/ ./src/

ENV PYTHONUNBUFFERED=1 \
    CITEVAULT_DB=/data/citevault.db \
    OLLAMA_HOST=http://ollama:11434 \
    CITEVAULT_MODEL=gemma4:e4b

VOLUME ["/data"]

EXPOSE 8000

ENTRYPOINT ["uv", "run", "citevault"]
CMD ["serve"]
