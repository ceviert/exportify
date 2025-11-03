FROM python:3.12-slim

# Install system dependencies (for ffmpeg, yt-dlp)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY app/ ./app
COPY data/ ./data

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the main script
CMD ["python", "app/main.py"]
