# Use the official Python runtime as the base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the Python script into the container
COPY /src .

# Specify the command to run the Python script
ENTRYPOINT ["python", "emailer.py"]
