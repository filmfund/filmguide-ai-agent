# Dockerfile for Python 3.11 and requirements installation
FROM python:3.11-slim AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

FROM base AS backend_agent
CMD ["python", "backend_agent.py"]
EXPOSE 8000

FROM base AS movie_agent
CMD ["python", "movie_agent.py"]
EXPOSE 5050

FROM base AS trailer_agent
CMD ["python", "trailer_agent.py"]
EXPOSE 5051
