# docker/Dockerfile

FROM python:3.9-slim

# Create a working directory
WORKDIR /app

# Copy and install dependencies
COPY api/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy model, API, frontend
COPY model/ /app/model/
COPY api/ /app/api/
COPY frontend/ /app/frontend/

# Expose the Flask port
EXPOSE 8000

# Run the Flask app
CMD ["python", "api/app.py"]
