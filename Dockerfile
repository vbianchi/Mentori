# -----------------------------------------------------------------------------
# Dockerfile for the ResearchAgent Backend
#
# This file defines the steps to build a Docker image containing our
# Python backend application and all its dependencies.
# -----------------------------------------------------------------------------

# -- Stage 1: Base Image --
# Use a slim, official Python image as the base.
# Using a specific version tag ensures reproducible builds.
FROM python:3.12-slim

# -- Environment Variables --
# Set the working directory for the application inside the container.
WORKDIR /app

# Prevents Python from buffering stdout and stderr, which helps with logging.
ENV PYTHONUNBUFFERED 1

# -- Install Dependencies --
# Copy the requirements file first to leverage Docker's layer caching.
# This layer will only be rebuilt if requirements.txt changes.
COPY requirements.txt .

# Install the Python dependencies.
# --no-cache-dir reduces the image size.
RUN pip install --no-cache-dir -r requirements.txt

# -- Copy Application Code --
# Copy the backend source code into the container.
# We assume the backend code will reside in a 'backend' directory.
COPY ./backend ./backend

# -- Expose Ports --
# Expose the ports the backend server will listen on.
# These will be mapped to host ports by docker-compose.yml.
# 8765 for the main WebSocket server.
EXPOSE 8765
# 8766 for the file server (for serving artifacts).
EXPOSE 8766

# -- Run Command --
# The command to execute when the container starts.
# This runs the server module within the 'backend' package.
CMD ["python3", "-m", "backend.server"]