# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# (Optional: If you had requirements.txt)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run your Python application using the shell form with exec
# This ensures signals are passed correctly and output streams are managed.
CMD exec python app.py