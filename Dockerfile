# # Use official Python image with specific version
# FROM python:3.9.18-slim-bookworm

# # Install system dependencies
# RUN apt-get update && apt-get install -y \
#     tesseract-ocr \
#     libtesseract-dev \
#     libgl1 \
#     libglib2.0-0 \
#     libsm6 \
#     libxext6 \
#     libxrender-dev \
#     && rm -rf /var/lib/apt/lists/*

# # Set working directory
# WORKDIR /app

# # Install Python dependencies with specific versions
# COPY requirements.txt .
# RUN pip install --upgrade pip && \
#     pip install --no-cache-dir -r requirements.txt

# # Copy application files
# COPY . .

# # Environment variables
# ENV PYTHONUNBUFFERED=1
# ENV FLASK_ENV=production
# ENV TF_ENABLE_ONEDNN_OPTS=0
# ENV TF_CPP_MIN_LOG_LEVEL=2  
# # Reduce TensorFlow logging

# # Expose port
# EXPOSE 8080  
# # Changed to match your app's port

# # Use production WSGI server
# CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "app:app"]

# Use Python 3.10 image (to support newer packages)
FROM python:3.10.12-slim-bookworm

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    # Remove any mention of fcntl from requirements.txt as it's a built-in module
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV FLASK_APP=app.py

# Expose port
EXPOSE 8080

# Use production WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120", "app:app"]