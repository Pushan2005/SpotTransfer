# ---- Base Image ----
FROM python:3.12-slim AS base

# Set working directory
WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps (for pip + building some packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy dependency file and install requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose Flask app port
EXPOSE 8080

# Set environment variables for Flask
ENV FLASK_APP=main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8080
# Set environment variables for spottransfer
# ENV SPOTIPY_CLIENT_ID=<your_spotify_client_id>
# ENV SPOTIPY_CLIENT_SECRET=<your_spotify_client_secret>
ENV FRONTEND_URL=http://localhost:5173

# Run the Flask app
CMD ["flask", "run"]
