# docker/Dockerfile.backend
# Use official Python 3.12 slim image
FROM python:3.12-slim

# Install uv (fast Python package installer)
# Using the pre-built installer image to copy the binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Install system dependencies + R base for R notebook kernel support
# Actual R version is determined by the Debian apt mirror at build time
# (R 4.5.0 on arm64 Debian bookworm/trixie as of 2026-02)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    default-jre \
    poppler-utils \
    r-base \
    r-base-dev \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    && rm -rf /var/lib/apt/lists/*

# Install R packages (no jupyter needed yet, just CRAN deps)
RUN R -e "install.packages(c('IRkernel','IRdisplay','repr'), \
        repos='https://cloud.r-project.org', \
        Ncpus=2, quiet=TRUE)"

# Copy only dependency files first to leverage cache
COPY pyproject.toml .

# Install Python dependencies (includes jupyter-client, needed by IRkernel::installspec)
# --system installs into system python (no venv needed in container)
RUN uv pip install --system .

# Register IRkernel system-wide AFTER jupyter-client is installed
# After this, `jupyter kernelspec list` shows kernel name "ir"
RUN R -e "IRkernel::installspec(user=FALSE)"

# Download spaCy models for semantic chunking (English + Dutch for WBVR)
RUN python -m spacy download en_core_web_sm && \
    python -m spacy download nl_core_news_sm

# Copy the rest of the application
COPY backend/ ./backend/

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8766

# Command to run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8766", "--reload"]
