# docker/Dockerfile

# Use a prebuilt PyTorch image that already has Python + Torch installed.
# This saves time vs installing Torch from scratch in python:3.9-slim.
FROM pytorch/pytorch

# Make a working directory
WORKDIR /app

# Copy only requirements first to leverage Docker caching
COPY api/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script that creates the tiny model
COPY create_tiny_model.py /app/

# RUN the script so we have a consistent /app/model each build
RUN python create_tiny_model.py

# Debug step (optional): see what's in /app/model
RUN ls -l /app/model

# Now copy in the rest of the code
COPY api/ /app/api/
COPY frontend/ /app/frontend/
COPY docker/ /app/docker/
# system_prompt is in /app/api/system_prompt.txt
# If you have other files, copy them as needed.

# Expose the Flask port
EXPOSE 8000

# Run the app
CMD ["python", "api/app.py"]
