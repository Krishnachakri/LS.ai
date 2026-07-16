#!/bin/bash

# Start FastAPI backend in background
cd /app/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000 &

# Start Next.js frontend in background
cd /app/frontend
npm run start &

# Start Nginx in foreground to keep container alive
nginx -g "daemon off;"
