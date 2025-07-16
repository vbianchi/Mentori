# -----------------------------------------------------------------------------
# Dockerfile for the Mentor::i Backend
#
# This file defines the steps to build a Docker image containing our
# Python backend application and all its dependencies.
# It uses the `uv` package manager for faster installation and includes
# a diagnostic step to verify installed packages.
# -----------------------------------------------------------------------------

# -- Stage 1: Base Image --
FROM python:3.12-slim

# -- Environment Variables --
WORKDIR /app
ENV PYTHONUNBUFFERED=1

# -- Install Dependencies using uv --
RUN pip install uv

# Copy the requirements file to leverage Docker's layer caching.
COPY requirements.txt .

# Install the project dependencies using uv.
RUN uv pip install --system -r requirements.txt

# --- DIAGNOSTIC STEP ---
# List all installed packages to verify the installation during the build process.
# The output of this command will be visible in the build logs.
RUN uv pip list

# -- Copy Application Code --
COPY ./backend ./backend

# -- Expose Ports --
EXPOSE 8765
EXPOSE 8766

# -- Run Command --
CMD ["python3", "-m", "backend.server"]
