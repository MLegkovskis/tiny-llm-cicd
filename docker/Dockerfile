# Use a prebuilt PyTorch image that already has Python + Torch installed.
FROM pytorch/pytorch

# Create a working directory
WORKDIR /app

# Copy only requirements first (to leverage Docker caching)
COPY api/requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a model folder (we'll COPY from local artifact)
RUN mkdir -p app/model

# Now copy in the rest of the source code
# (Excluding the model, which we'll copy separately below)
COPY api/ /app/api/
COPY frontend/ /app/frontend/
COPY docker/ /app/docker/

# Copy the model artifacts from the build environment
# (The GH Action "download-artifact" step places 'model' folder at the root)
COPY model app/model

# Debug step (optional): see what's in app/model
RUN ls -l app/model

# Expose the Flask port
EXPOSE 8000

# Run the app
CMD ["python", "api/app.py"]
