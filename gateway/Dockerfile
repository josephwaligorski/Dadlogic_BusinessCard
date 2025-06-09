# Stage 1: Build React frontend
FROM node:18 AS frontend-build
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend ./
RUN npm run build

# Stage 2: Python Flask API + static serving
FROM python:3.10-slim
WORKDIR /app
COPY gateway/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY gateway .
# Copy built frontend from previous stage
COPY --from=frontend-build /frontend/build ./static
CMD ["python", "main.py"]