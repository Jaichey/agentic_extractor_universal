# Use Python 3.9 with full Debian packages
FROM python:3.9.18-bookworm

# Install all required system dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgtk2.0-dev \
    libgtk-3-dev \
    libboost-all-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# First install dlib with explicit build options
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir cmake && \
    pip install --no-cache-dir --verbose --global-option=--verbose \
    --install-option="--no" --install-option="DLIB_USE_CUDA" \
    --install-option="--no" --install-option="DLIB_USE_BLAS" \
    dlib==19.24.2 && \
    pip install --no-cache-dir opencv-python-headless==4.5.5.64 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]