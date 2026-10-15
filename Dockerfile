# Always-on image for the read-only dashboard. Light: Streamlit only, no API client, no secrets.
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .
RUN useradd --create-home app && chown -R app /app
USER app

# Hosts like Render set $PORT; locally it defaults to 8501.
EXPOSE 8501
HEALTHCHECK CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.getenv(\"PORT\", \"8501\")}/_stcore/health')"
CMD ["sh", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501} --server.fileWatcherType=none"]
