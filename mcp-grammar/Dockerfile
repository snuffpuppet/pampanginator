FROM python:3.12-slim

WORKDIR /app

COPY libs/ /libs/
COPY mcp-grammar/requirements.txt .
RUN pip install --no-cache-dir /libs/kapampangan_obs -r requirements.txt && \
    rm -rf /libs/

# Pre-download the embedding model at build time so startup is fast.
# The model is ~80 MB and is read-only at runtime.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY mcp-grammar/ .

# data/ is mounted as a volume at runtime
EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
