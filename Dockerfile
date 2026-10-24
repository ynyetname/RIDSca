FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    HF_HOME=/home/user/.cache/huggingface RIDSCA_MODE=local RIDSCA_THREADS=2 \
    OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 TOKENIZERS_PARALLELISM=false \
    HF_HUB_DISABLE_TELEMETRY=1 DO_NOT_TRACK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ffmpeg tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin aapt libgomp1 \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 user
WORKDIR /home/user/app
COPY requirements*.txt ./
RUN pip install --upgrade pip && \
    pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu && \
    CMAKE_ARGS="-DGGML_NATIVE=OFF -DGGML_OPENMP=ON" pip install -r requirements-models.txt
COPY --chown=user:user . .
USER user
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/_stcore/health',timeout=3)"
CMD ["python", "-m", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=7860"]
