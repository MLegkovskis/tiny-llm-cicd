# docker/Dockerfile

FROM python:3.9-slim

WORKDIR /app

COPY api/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY model/ /app/model/
COPY api/ /app/api/
COPY frontend/ /app/frontend/

EXPOSE 8000
CMD ["python", "api/app.py"]
