# Stage 1: Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY backend/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend directory into the container at /app
COPY ./backend /app/backend

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable to tell uvicorn where to find the app
# Note: We use backend.main because our code is inside the 'backend' subfolder.
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
