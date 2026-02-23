FROM python:3.11-slim

WORKDIR /app

# Install gcc and dependencies for aiohttp
RUN apt-get update && apt-get install -y gcc build-essential libssl-dev libffi-dev python3-dev

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY bot.py .

CMD ["python", "bot.py"]
