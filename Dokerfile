FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (optional, in case you need build tools for some libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for caching
COPY requirements.txt setup.py ./

# Install pip + deps
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && pip install -e .

# Copy the rest of your app
COPY . .

# Expose the app port
EXPOSE 5000

# Run with Gunicorn (production WSGI server)
CMD ["gunicorn", "-b", "0.0.0.0:5000", "wsgi:app"]
