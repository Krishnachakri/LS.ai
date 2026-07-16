# Stage 1: Build Next.js Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
# Configure Next.js to make relative requests to the Nginx gateway
ENV NEXT_PUBLIC_API_URL=""
RUN npm run build

# Stage 2: Final Production Container
FROM python:3.10-slim
WORKDIR /app

# Install system utilities, Nginx, and Node.js runtime
RUN apt-get update && apt-get install -y \
    curl \
    nginx \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install backend Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy built frontend application
COPY --from=frontend-builder /app/frontend ./frontend

# Copy backend application
COPY backend/ ./backend

# Copy proxy configurations and startup controller
COPY nginx.conf /etc/nginx/nginx.conf
COPY start.sh ./
RUN chmod +x start.sh

# Expose default Hugging Face Space port
EXPOSE 7860

# Run unified startup controller
CMD ["./start.sh"]
