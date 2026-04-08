# docker/Dockerfile.frontend
FROM node:20-slim

WORKDIR /app

# Install system dependencies (if any needed for node-gyp etc)
# pure vite/react usually needs none for dev
# RUN apt-get update && ...

COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source
COPY frontend/ .

# Expose Vite default port
EXPOSE 5173

# Start dev server
CMD ["npm", "run", "dev", "--", "--host"]
