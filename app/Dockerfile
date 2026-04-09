# Stage 1 — compile the React frontend
# vite.config.ts sets outDir: '../app/frontend', which from /build/frontend
# resolves to /build/app/frontend — picked up by COPY in stage 2.
FROM node:20-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2 — Python runtime
FROM python:3.12-slim
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ .
COPY --from=frontend-build /build/app/frontend ./frontend

# config/ is mounted as a volume at runtime — not baked into the image
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
