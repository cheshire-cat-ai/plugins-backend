# Use the official Python image as the base image
FROM python:3.10.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file and install the dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

#Installing Git
RUN apt-get update && apt-get install -y git

# Copy the entire app directory to the container
COPY . /app/

# Expose the port that FastAPI will listen on (if your app is using a different port, change it here)
EXPOSE 8000

# Run the FastAPI application (uvicorn is launched from main.py)
CMD ["python", "/app/main.py"]