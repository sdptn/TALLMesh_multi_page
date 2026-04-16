FROM python:3.12-slim

WORKDIR /app

# System deps (needed for PyMuPDF etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Streamlit port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "TALLMesh.py", "--server.port=8501", "--server.address=0.0.0.0"]