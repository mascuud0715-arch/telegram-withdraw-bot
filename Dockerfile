# Base image oo Python 3.12
FROM python:3.12-slim

# Folder ka shaqada gudaha container
WORKDIR /app

# Copy bot files
COPY bot.py .
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Ordo bot-ka
CMD ["python", "bot.py"]
