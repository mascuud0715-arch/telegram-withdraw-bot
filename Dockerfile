# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Copy bot and requirements
COPY bot.py .
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Run the bot
CMD ["python", "bot.py"]
