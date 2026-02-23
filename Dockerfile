# Base image
FROM python:3.12-slim

# Working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install gcc + build-essential
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    python3-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get remove -y build-essential gcc python3-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy bot code
COPY . .

# Run bot
CMD ["python", "bot.py"]
